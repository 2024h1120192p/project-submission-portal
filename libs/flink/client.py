"""Flink REST API client for job management and monitoring.

Provides interface to interact with Flink JobManager via REST API.
"""
from typing import Dict, Any, List, Optional
import httpx
from config.logging import get_logger

logger = get_logger(__name__)


class FlinkClient:
    """Client for interacting with Flink JobManager REST API.
    
    Usage:
        client = FlinkClient(jobmanager_url="http://flink-jobmanager:8081")
        jobs = await client.list_jobs()
        job_details = await client.get_job_details(job_id)
    """
    
    def __init__(self, jobmanager_url: str = "http://flink-jobmanager:8081"):
        """Initialize Flink client.
        
        Args:
            jobmanager_url: URL of the Flink JobManager REST API
        """
        self.base_url = jobmanager_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """Check if Flink JobManager is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/overview")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all Flink jobs.
        
        Returns:
            List of job dictionaries with status information
        """
        try:
            response = await self.client.get(f"{self.base_url}/jobs")
            response.raise_for_status()
            data = response.json()
            return data.get('jobs', [])
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    async def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific job.
        
        Args:
            job_id: Flink job ID
            
        Returns:
            Job details dictionary or None if not found
        """
        try:
            response = await self.client.get(f"{self.base_url}/jobs/{job_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get job details for {job_id}: {e}")
            return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running Flink job.
        
        Args:
            job_id: Flink job ID to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        try:
            response = await self.client.patch(
                f"{self.base_url}/jobs/{job_id}",
                params={"mode": "cancel"}
            )
            response.raise_for_status()
            logger.info(f"Job {job_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """Get metrics for a specific job.
        
        Args:
            job_id: Flink job ID
            
        Returns:
            Dictionary of metrics
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/jobs/{job_id}/metrics"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get metrics for job {job_id}: {e}")
            return {}
    
    async def get_overview(self) -> Dict[str, Any]:
        """Get overview of Flink cluster.
        
        Returns:
            Dictionary with cluster overview information
        """
        try:
            response = await self.client.get(f"{self.base_url}/overview")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get overview: {e}")
            return {}
