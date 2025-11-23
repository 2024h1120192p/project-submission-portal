package com.portal.analytics;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.functions.windowing.ProcessAllWindowFunction;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.time.Instant;

/**
 * Simplified Flink job: 
 * - Consumes processed submission & plagiarism topics
 * - Merges streams
 * - Performs 5-min tumbling window count
 * - Emits JSON summary to analytics_window topic
 */
public class WindowedAnalyticsJob {

    public static void main(String[] args) throws Exception {
        final String bootstrap = envOr("KAFKA_BOOTSTRAP", argOr(args, 0, "localhost:9092"));
        final String submissionTopic = envOr("SUBMISSION_TOPIC", argOr(args, 1, "paper_uploaded_processed"));
        final String plagiarismTopic = envOr("PLAGIARISM_TOPIC", argOr(args, 2, "plagiarism_checked_processed"));
        final String outputTopic = envOr("OUTPUT_TOPIC", argOr(args, 3, "analytics_window"));

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Kafka Source for submissions
        KafkaSource<String> submissionSource = KafkaSource.<String>builder()
            .setBootstrapServers(bootstrap)
            .setTopics(submissionTopic)
            .setGroupId("analytics-flink-job")
            .setStartingOffsets(OffsetsInitializer.earliest())
            .setValueOnlyDeserializer(new SimpleStringSchema())
            .build();

        // Kafka Source for plagiarism
        KafkaSource<String> plagiarismSource = KafkaSource.<String>builder()
            .setBootstrapServers(bootstrap)
            .setTopics(plagiarismTopic)
            .setGroupId("analytics-flink-job")
            .setStartingOffsets(OffsetsInitializer.earliest())
            .setValueOnlyDeserializer(new SimpleStringSchema())
            .build();

        DataStream<String> submissions = env.fromSource(
            submissionSource,
            WatermarkStrategy.noWatermarks(),
            "SubmissionsStream"
        );
        
        DataStream<String> plagiarism = env.fromSource(
            plagiarismSource,
            WatermarkStrategy.noWatermarks(),
            "PlagiarismStream"
        );

        DataStream<String> merged = submissions.union(plagiarism);

        DataStream<String> windowed = merged
            .windowAll(org.apache.flink.streaming.api.windowing.assigners.TumblingProcessingTimeWindows.of(Time.minutes(5)))
            .process(new CountWindowProcess());

        // Kafka Sink
        KafkaSink<String> sink = KafkaSink.<String>builder()
            .setBootstrapServers(bootstrap)
            .setRecordSerializer(
                KafkaRecordSerializationSchema.builder()
                    .setTopic(outputTopic)
                    .setValueSerializationSchema(new SimpleStringSchema())
                    .build()
            )
            .build();

        windowed.sinkTo(sink).name("AnalyticsWindowSink");

        env.execute("PortalAnalyticsWindowJob");
    }

    private static class CountWindowProcess extends ProcessAllWindowFunction<String, String, TimeWindow> {
        @Override
        public void process(Context context, Iterable<String> elements, Collector<String> out) {
            long count = 0;
            for (String ignored : elements) {
                count++;
            }
            long windowStart = context.window().getStart();
            long windowEnd = context.window().getEnd();
            String json = String.format("{\"window_start\":%d,\"window_end\":%d,\"event_count\":%d,\"generated_at\":%d}",
                windowStart, windowEnd, count, Instant.now().toEpochMilli());
            out.collect(json);
        }
    }

    private static String envOr(String key, String fallback) {
        String v = System.getenv(key);
        return v == null || v.isBlank() ? fallback : v;
    }

    private static String argOr(String[] args, int idx, String fallback) {
        return idx < args.length ? args[idx] : fallback;
    }
}
