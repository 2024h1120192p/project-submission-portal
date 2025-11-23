"""Managed Flink (AWS Kinesis Data Analytics for Apache Flink) client.

Provides an async-friendly wrapper around the AWS Kinesis Analytics V2 API
for listing, describing, starting and stopping Flink applications.

This complements the existing `FlinkClient` (self-hosted JobManager REST)
by offering a similar interface adapted to the managed service.
"""
from typing import Any, Dict, Optional
import asyncio

try:
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError("boto3 is required for Managed Flink operations. Install with 'pip install boto3'.") from e

from config.logging import get_logger

logger = get_logger(__name__)


class ManagedFlinkClient:
    """Client for AWS Managed Flink (Kinesis Data Analytics for Apache Flink).

    Async methods internally delegate to the synchronous boto3 client using
    `asyncio.to_thread` for non-blocking behavior.

    Usage:
        client = ManagedFlinkClient(region="us-east-1", application_name="dev-managed-flink")
        apps = await client.list_applications()
        details = await client.describe_application()
        await client.start_application()
    """

    def __init__(self, region: str, application_name: str):
        self.region = region
        self.application_name = application_name
        self._client = boto3.client("kinesisanalyticsv2", region_name=region)

    async def list_applications(self) -> Dict[str, Any]:
        return await asyncio.to_thread(self._list_applications_sync)

    def _list_applications_sync(self) -> Dict[str, Any]:
        try:
            resp = self._client.list_applications()
            return resp
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to list Managed Flink applications: {e}")
            return {}

    async def describe_application(self) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._describe_application_sync)

    def _describe_application_sync(self) -> Optional[Dict[str, Any]]:
        try:
            resp = self._client.describe_application(ApplicationName=self.application_name)
            return resp.get("ApplicationDetail")
        except self._client.exceptions.ResourceNotFoundException:
            logger.warning(f"Managed Flink application '{self.application_name}' not found")
            return None
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to describe application '{self.application_name}': {e}")
            return None

    async def start_application(self, input_config: Optional[Dict[str, Any]] = None) -> bool:
        return await asyncio.to_thread(self._start_application_sync, input_config)

    def _start_application_sync(self, input_config: Optional[Dict[str, Any]]) -> bool:
        try:
            params: Dict[str, Any] = {"ApplicationName": self.application_name}
            if input_config:
                params["RunConfiguration"] = input_config
            self._client.start_application(**params)
            logger.info(f"Start initiated for Managed Flink application '{self.application_name}'")
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to start application '{self.application_name}': {e}")
            return False

    async def stop_application(self) -> bool:
        return await asyncio.to_thread(self._stop_application_sync)

    def _stop_application_sync(self) -> bool:
        try:
            self._client.stop_application(ApplicationName=self.application_name)
            logger.info(f"Stop initiated for Managed Flink application '{self.application_name}'")
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to stop application '{self.application_name}': {e}")
            return False

    async def application_status(self) -> Optional[str]:
        detail = await self.describe_application()
        if not detail:
            return None
        return detail.get("ApplicationStatus")

    async def is_running(self) -> bool:
        status = await self.application_status()
        return status in {"RUNNING", "UPDATING"}
