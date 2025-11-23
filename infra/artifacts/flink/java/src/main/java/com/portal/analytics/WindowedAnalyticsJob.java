package com.portal.analytics;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer;
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.api.functions.windowing.ProcessWindowFunction;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;
import org.apache.flink.util.Collector;

import java.time.Instant;
import java.util.Properties;

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

        Properties props = new Properties();
        props.setProperty("bootstrap.servers", bootstrap);
        props.setProperty("group.id", "analytics-flink-job");

        FlinkKafkaConsumer<String> submissionConsumer = new FlinkKafkaConsumer<>(submissionTopic, new SimpleStringSchema(), props);
        FlinkKafkaConsumer<String> plagiarismConsumer = new FlinkKafkaConsumer<>(plagiarismTopic, new SimpleStringSchema(), props);

        submissionConsumer.assignTimestampsAndWatermarks(WatermarkStrategy.noWatermarks());
        plagiarismConsumer.assignTimestampsAndWatermarks(WatermarkStrategy.noWatermarks());

        DataStream<String> submissions = env.addSource(submissionConsumer).name("SubmissionsStream");
        DataStream<String> plagiarism = env.addSource(plagiarismConsumer).name("PlagiarismStream");

        DataStream<String> merged = submissions.union(plagiarism).name("MergedEvents");

        DataStream<String> windowed = merged
            .timeWindowAll(Time.minutes(5))
            .process(new CountWindowProcess())
            .name("FiveMinuteCounts");

        FlinkKafkaProducer<String> producer = new FlinkKafkaProducer<>(
            outputTopic,
            new SimpleStringSchema(),
            props,
            FlinkKafkaProducer.Semantic.AT_LEAST_ONCE
        );

        windowed.addSink(producer).name("AnalyticsWindowSink");

        env.execute("PortalAnalyticsWindowJob");
    }

    private static class CountWindowProcess extends ProcessWindowFunction<String, String, Void, TimeWindow> {
        @Override
        public void process(Void key, Context context, Iterable<String> elements, Collector<String> out) {
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
