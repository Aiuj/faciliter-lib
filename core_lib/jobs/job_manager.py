"""Job queue manager with singleton pattern."""

from typing import Any, Optional, Dict, List

from .base_job_queue import BaseJobQueue, JobStatus, Job
from .redis_job_queue import RedisJobQueue
from core_lib.tracing.logger import get_module_logger


logger = get_module_logger()

# Global job queue instance
_job_queue_instance: Optional[BaseJobQueue] = None


def create_job_queue(queue_type: str = "redis", **kwargs) -> BaseJobQueue:
    """Create a job queue instance.
    
    Args:
        queue_type: Type of queue ("redis" or "valkey")
        **kwargs: Additional configuration parameters
        
    Returns:
        Job queue instance
    """
    if queue_type.lower() in ["redis", "valkey"]:
        queue = RedisJobQueue(**kwargs)
    else:
        raise ValueError(f"Unsupported queue type: {queue_type}")
    
    queue.connect()
    return queue


def set_job_queue(queue: BaseJobQueue):
    """Set the global job queue instance.
    
    Args:
        queue: Job queue instance to set as global
    """
    global _job_queue_instance
    _job_queue_instance = queue


def get_job_queue() -> Optional[BaseJobQueue]:
    """Get the global job queue instance.
    
    Returns:
        Global job queue instance or None if not initialized
    """
    global _job_queue_instance
    
    # Auto-initialize if not set
    if _job_queue_instance is None:
        try:
            _job_queue_instance = create_job_queue()
            logger.info("[JobManager] Auto-initialized Redis job queue")
        except Exception as e:
            logger.error(f"[JobManager] Failed to auto-initialize job queue: {e}")
            return None
    
    return _job_queue_instance


# --- Convenience functions ---

def submit_job(
    job_type: str,
    input_data: Optional[Dict[str, Any]] = None,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ttl: Optional[int] = None,
) -> str:
    """Submit a new job to the queue.
    
    Args:
        job_type: Type of job (e.g., "ingest_excel", "answer_questionnaire")
        input_data: Input data for the job
        company_id: Optional company identifier
        user_id: Optional user identifier
        session_id: Optional session identifier
        metadata: Optional metadata
        ttl: Optional time-to-live in seconds
        
    Returns:
        Job ID
        
    Raises:
        RuntimeError: If job queue is not initialized
    """
    queue = get_job_queue()
    if not queue:
        raise RuntimeError("Job queue not initialized")
    
    return queue.submit_job(
        job_type=job_type,
        input_data=input_data,
        company_id=company_id,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
        ttl=ttl,
    )


def get_job_status(job_id: str) -> Optional[Job]:
    """Get job status and information.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job object or None if not found
    """
    queue = get_job_queue()
    if not queue:
        return None
    
    return queue.get_job(job_id)


def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job result if completed.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job result or None if not completed/not found
    """
    job = get_job_status(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        return None
    
    return job.result


def update_job_status(
    job_id: str,
    status: JobStatus,
    error: Optional[str] = None
) -> bool:
    """Update job status.
    
    Args:
        job_id: Job identifier
        status: New status
        error: Optional error message
        
    Returns:
        True if updated successfully
    """
    queue = get_job_queue()
    if not queue:
        return False
    
    return queue.update_job_status(job_id, status, error)


def update_job_progress(
    job_id: str,
    progress: int,
    message: Optional[str] = None
) -> bool:
    """Update job progress.
    
    Args:
        job_id: Job identifier
        progress: Progress percentage (0-100)
        message: Optional progress message
        
    Returns:
        True if updated successfully
    """
    queue = get_job_queue()
    if not queue:
        return False
    
    return queue.update_job_progress(job_id, progress, message)


def complete_job(
    job_id: str,
    result: Optional[Dict[str, Any]] = None
) -> bool:
    """Mark job as completed.
    
    Args:
        job_id: Job identifier
        result: Job result data
        
    Returns:
        True if updated successfully
    """
    queue = get_job_queue()
    if not queue:
        return False
    
    return queue.complete_job(job_id, result)


def fail_job(job_id: str, error: str) -> bool:
    """Mark job as failed.
    
    Args:
        job_id: Job identifier
        error: Error message
        
    Returns:
        True if updated successfully
    """
    queue = get_job_queue()
    if not queue:
        return False
    
    return queue.fail_job(job_id, error)


def cancel_job(job_id: str) -> bool:
    """Cancel a pending or processing job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if cancelled successfully
    """
    queue = get_job_queue()
    if not queue:
        return False
    
    return queue.cancel_job(job_id)


def list_jobs(
    status: Optional[JobStatus] = None,
    company_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100
) -> List[Job]:
    """List jobs with optional filtering.
    
    Args:
        status: Optional status filter
        company_id: Optional company filter
        user_id: Optional user filter
        limit: Maximum number of jobs to return
        
    Returns:
        List of Job objects
    """
    queue = get_job_queue()
    if not queue:
        return []
    
    return queue.list_jobs(status, company_id, user_id, limit)


def cleanup_old_jobs(older_than_seconds: int = 86400) -> int:
    """Clean up completed/failed jobs older than specified time.
    
    Args:
        older_than_seconds: Delete jobs older than this (default 24h)
        
    Returns:
        Number of jobs deleted
    """
    queue = get_job_queue()
    if not queue:
        return 0
    
    return queue.cleanup_old_jobs(older_than_seconds)
