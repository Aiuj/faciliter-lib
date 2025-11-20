# Job Queue System - Quick Reference

## Overview

The `core-lib` job queue system provides a Redis-based async job processing framework for distributed applications. It follows the same design pattern as the cache module.

## Installation

Already included in `core-lib`:

```python
from core_lib.jobs import (
    submit_job, get_job_status, get_job_result,
    update_job_progress, complete_job, fail_job,
    JobWorker, JobHandler, JobStatus, Job
)
```

## Environment Variables

```env
# Job Queue Configuration (falls back to REDIS_* if not set)
JOB_QUEUE_HOST=localhost
JOB_QUEUE_PORT=6379
JOB_QUEUE_DB=0
JOB_QUEUE_PASSWORD=
JOB_QUEUE_PREFIX=jobs:
JOB_QUEUE_TTL=86400                    # 24 hours in seconds
JOB_QUEUE_MAX_CONNECTIONS=10
JOB_QUEUE_RETRY_ON_TIMEOUT=true
JOB_QUEUE_SOCKET_TIMEOUT=5
```

## Quick Start

### 1. Submit a Job

```python
from core_lib.jobs import submit_job

job_id = submit_job(
    job_type="my_task",
    input_data={
        "param1": "value1",
        "param2": "value2"
    },
    company_id="company1",
    user_id="user1",
    session_id="session1",
    metadata={"source": "api"},
    ttl=3600  # Optional, 1 hour
)

print(f"Job submitted: {job_id}")
```

### 2. Check Job Status

```python
from core_lib.jobs import get_job_status, JobStatus

job = get_job_status(job_id)

if job:
    print(f"Status: {job.status.value}")
    print(f"Progress: {job.progress}%")
    print(f"Message: {job.progress_message}")
    
    if job.status == JobStatus.COMPLETED:
        print(f"Result: {job.result}")
    elif job.status == JobStatus.FAILED:
        print(f"Error: {job.error}")
```

### 3. Create a Worker

```python
from core_lib.jobs import JobWorker, JobHandler, Job

# Define a handler
class MyTaskHandler(JobHandler):
    def get_job_type(self) -> str:
        return "my_task"
    
    def handle(self, job: Job) -> dict:
        # Extract input data
        param1 = job.input_data.get("param1")
        param2 = job.input_data.get("param2")
        
        # Process the job
        result = process_something(param1, param2)
        
        # Return result
        return {
            "success": True,
            "data": result
        }

# Create and start worker
worker = JobWorker(
    poll_interval=1.0,
    max_retries=3,
    retry_delay=5.0
)

worker.register_handler(MyTaskHandler())
worker.start()
```

### 4. Function-Based Handler

```python
from core_lib.jobs import JobWorker, Job

def process_my_task(job: Job) -> dict:
    """Simple function handler."""
    param1 = job.input_data.get("param1")
    result = do_something(param1)
    return {"result": result}

worker = JobWorker()
worker.register_function_handler("my_task", process_my_task)
worker.start()
```

## Core API

### Job Submission

```python
submit_job(
    job_type: str,                      # Required: type identifier
    input_data: Optional[Dict] = None,  # Job parameters
    company_id: Optional[str] = None,   # Multi-tenancy
    user_id: Optional[str] = None,      # Audit trail
    session_id: Optional[str] = None,   # Tracking
    metadata: Optional[Dict] = None,    # Additional info
    ttl: Optional[int] = None,          # Time-to-live (seconds)
) -> str  # Returns job_id
```

### Job Status & Results

```python
# Get full job object
job = get_job_status(job_id)

# Get just the result (if completed)
result = get_job_result(job_id)  # Returns None if not completed
```

### Update Job Progress (from worker)

```python
from core_lib.jobs import update_job_progress

update_job_progress(
    job_id="...",
    progress=50,  # 0-100
    message="Processing step 5 of 10"
)
```

### Complete or Fail Job (from worker)

```python
from core_lib.jobs import complete_job, fail_job

# Success
complete_job(job_id, result={"data": "..."})

# Failure
fail_job(job_id, error="Something went wrong")
```

### List Jobs

```python
from core_lib.jobs import list_jobs, JobStatus

# All pending jobs
pending = list_jobs(status=JobStatus.PENDING)

# Jobs for a specific company
company_jobs = list_jobs(company_id="company1", limit=50)

# Jobs for a user
user_jobs = list_jobs(user_id="user1")
```

### Cleanup

```python
from core_lib.jobs import cleanup_old_jobs

# Delete completed/failed jobs older than 24 hours
deleted_count = cleanup_old_jobs(older_than_seconds=86400)
```

## Job Object

```python
@dataclass
class Job:
    job_id: str
    job_type: str
    status: JobStatus  # PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED
    created_at: str
    updated_at: str
    
    # Optional fields
    company_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    input_data: Optional[Dict[str, Any]]
    
    # Progress tracking
    progress: int = 0  # 0-100
    progress_message: Optional[str] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
```

## JobStatus Enum

```python
from core_lib.jobs import JobStatus

JobStatus.PENDING       # Job submitted, waiting for worker
JobStatus.PROCESSING    # Worker is processing the job
JobStatus.COMPLETED     # Job completed successfully
JobStatus.FAILED        # Job failed with error
JobStatus.CANCELLED     # Job was cancelled
```

## Worker Configuration

```python
worker = JobWorker(
    job_queue=None,          # Optional: custom queue (auto-initializes if None)
    poll_interval=1.0,       # Seconds between queue checks
    max_retries=3,           # Max retry attempts for failed jobs
    retry_delay=5.0,         # Delay between retries (seconds)
)

# Register handlers
worker.register_handler(MyHandler())
worker.register_function_handler("task_type", my_function)

# Start processing (blocks until stopped)
worker.start(max_jobs=None)  # Optional: limit number of jobs

# Stop worker (from another thread or signal handler)
worker.stop()

# Check if running
if worker.is_running():
    print("Worker is active")
```

## Advanced: Custom Job Queue

```python
from core_lib.jobs import create_job_queue, set_job_queue, JobConfig

# Custom configuration
config = JobConfig(
    host="redis.example.com",
    port=6379,
    db=1,
    password="secret",
    prefix="myapp:jobs:",
    default_ttl=7200  # 2 hours
)

# Create and set custom queue
queue = create_job_queue("redis", config=config)
set_job_queue(queue)

# Now all submit_job() calls use this queue
```

## Error Handling

### In Workers

```python
class MyHandler(JobHandler):
    def handle(self, job: Job) -> dict:
        # Raise exceptions on errors
        if not job.input_data:
            raise ValueError("Missing input data")
        
        # Worker will:
        # 1. Catch the exception
        # 2. Retry up to max_retries
        # 3. Mark as FAILED after max retries
        
        return {"success": True}
```

### In Clients

```python
from core_lib.jobs import get_job_status, JobStatus

job = get_job_status(job_id)

if job.status == JobStatus.FAILED:
    print(f"Job failed: {job.error}")
    
    # Check retry count
    retry_count = job.metadata.get("retry_count", 0) if job.metadata else 0
    print(f"Retries attempted: {retry_count}")
```

## Multi-Tenancy

```python
# Submit job with company_id
job_id = submit_job(
    job_type="task",
    input_data={"data": "..."},
    company_id="company1"  # Tenant isolation
)

# List jobs for specific company
company_jobs = list_jobs(company_id="company1")
```

## Patterns

### Progress Reporting

```python
class LongRunningHandler(JobHandler):
    def handle(self, job: Job) -> dict:
        steps = 10
        for i in range(steps):
            # Update progress
            progress = int((i + 1) / steps * 100)
            update_job_progress(
                job.job_id,
                progress=progress,
                message=f"Processing step {i+1}/{steps}"
            )
            
            # Do work
            process_step(i)
        
        return {"completed": True}
```

### File Processing

```python
import base64

class FileHandler(JobHandler):
    def handle(self, job: Job) -> dict:
        # Get base64 file from input
        file_b64 = job.input_data.get("file_content")
        file_bytes = base64.b64decode(file_b64)
        
        # Process file
        result_bytes = process_file(file_bytes)
        
        # Return result as base64
        result_b64 = base64.b64encode(result_bytes).decode()
        return {
            "file_bytes_b64": result_b64,
            "filename": "result.xlsx"
        }
```

### Cleanup Schedule

```python
import schedule
import time
from core_lib.jobs import cleanup_old_jobs

def cleanup_task():
    deleted = cleanup_old_jobs(older_than_seconds=86400)  # 24h
    print(f"Cleaned up {deleted} old jobs")

# Run cleanup every 6 hours
schedule.every(6).hours.do(cleanup_task)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Testing

### Mock Queue

```python
from core_lib.jobs import set_job_queue
from unittest.mock import MagicMock

# Create mock queue
mock_queue = MagicMock()
mock_queue.submit_job.return_value = "test-job-id"
set_job_queue(mock_queue)

# Test code
job_id = submit_job("test", {"data": "..."})
assert job_id == "test-job-id"
```

### Test Handler

```python
from core_lib.jobs import Job, JobStatus

def test_my_handler():
    handler = MyTaskHandler()
    
    # Create test job
    job = Job(
        job_id="test-123",
        job_type="my_task",
        status=JobStatus.PROCESSING,
        created_at="2025-10-01T00:00:00",
        updated_at="2025-10-01T00:00:00",
        input_data={"param1": "value1"}
    )
    
    # Test handler
    result = handler.handle(job)
    assert result["success"] is True
```

## Comparison with Cache Module

Both follow similar patterns:

| Feature | Cache | Jobs |
|---------|-------|------|
| Backend | Redis/Valkey | Redis/Valkey |
| Singleton | `set_cache()`, `get_cache()` | `set_job_queue()`, `get_job_queue()` |
| Config | `CacheConfig` | `JobConfig` |
| Factory | `create_cache()` | `create_job_queue()` |
| Convenience | `cache_get()`, `cache_set()` | `submit_job()`, `get_job_status()` |

## See Also

- Agent-RFx async API documentation: `docs/ASYNC_JOB_PROCESSING.md`
- Cache module documentation: `docs/cache.md`
- Redis configuration: `docs/ENV_VARIABLES.md`
