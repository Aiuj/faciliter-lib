"""OpenTelemetry Protocol (OTLP) logging handler.

This module provides an OTLP handler that sends logs to an OpenTelemetry collector
via HTTP using the OTLP protocol. The handler converts Python logging records to
OTLP log format and sends them to a configurable endpoint.

The handler uses the standard OTLP/HTTP protocol on port 4318 by default.

References:
    - OTLP specification: https://opentelemetry.io/docs/specs/otlp/
    - Log data model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
import sys


class OTLPHandler(logging.Handler):
    """Handler that sends logs to an OpenTelemetry collector via OTLP/HTTP.
    
    This handler batches log records and sends them to an OTLP collector endpoint.
    It implements the OTLP/HTTP protocol for logs as specified in the OpenTelemetry
    specification.
    
    The handler runs in non-blocking mode using a queue and background thread to
    avoid impacting application performance.
    
    Attributes:
        endpoint: Full URL to the OTLP collector (e.g., 'http://localhost:4318/v1/logs')
        headers: HTTP headers to include in requests (e.g., authentication)
        timeout: Request timeout in seconds
        insecure: If True, skip SSL certificate verification
    """
    
    def __init__(
        self,
        endpoint: str = "http://localhost:4318/v1/logs",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        insecure: bool = False,
        service_name: str = "faciliter-lib",
        service_version: Optional[str] = None,
    ):
        """Initialize the OTLP handler.
        
        Args:
            endpoint: OTLP collector endpoint URL (default: http://localhost:4318/v1/logs)
            headers: Optional HTTP headers for authentication or metadata
            timeout: Request timeout in seconds (default: 10)
            insecure: Skip SSL verification if True (default: False)
            service_name: Service name for resource attributes (default: faciliter-lib)
            service_version: Optional service version for resource attributes
        """
        super().__init__()
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = timeout
        self.insecure = insecure
        self.service_name = service_name
        self.service_version = service_version
        
        # Ensure Content-Type is set for OTLP/HTTP
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Internal queue for async sending
        self._queue: Queue = Queue(maxsize=1000)
        self._listener: Optional[QueueListener] = None
        self._worker_handler: Optional['_OTLPWorkerHandler'] = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """Queue a log record for async transmission to OTLP collector.
        
        Args:
            record: The log record to send
        """
        try:
            # Put record in queue for background processing
            if not self._queue.full():
                self._queue.put_nowait(record)
        except Exception:
            # Silently fail to avoid recursion
            pass
    
    def _convert_to_otlp(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Convert a Python logging record to OTLP log format.
        
        Args:
            record: The logging record to convert
            
        Returns:
            Dictionary representing OTLP log record format
        """
        # Convert log level to OTLP severity
        severity_map = {
            logging.DEBUG: (5, "DEBUG"),
            logging.INFO: (9, "INFO"),
            logging.WARNING: (13, "WARN"),
            logging.ERROR: (17, "ERROR"),
            logging.CRITICAL: (21, "FATAL"),
        }
        severity_number, severity_text = severity_map.get(
            record.levelno, (0, "UNSPECIFIED")
        )
        
        # Build OTLP log record
        otlp_record = {
            "timeUnixNano": str(int(record.created * 1_000_000_000)),
            "severityNumber": severity_number,
            "severityText": severity_text,
            "body": {"stringValue": record.getMessage()},
            "attributes": [
                {"key": "logger.name", "value": {"stringValue": record.name}},
                {"key": "source.file", "value": {"stringValue": record.pathname}},
                {"key": "source.line", "value": {"intValue": str(record.lineno)}},
                {"key": "source.function", "value": {"stringValue": record.funcName or ""}},
            ],
        }
        
        # Add trace context if available
        if hasattr(record, "trace_id") and record.trace_id:
            otlp_record["traceId"] = record.trace_id
        if hasattr(record, "span_id") and record.span_id:
            otlp_record["spanId"] = record.span_id
        
        # Add any extra attributes from the record
        if hasattr(record, "extra_attrs"):
            for key, value in record.extra_attrs.items():
                attr_value = {"stringValue": str(value)}
                if isinstance(value, int):
                    attr_value = {"intValue": str(value)}
                elif isinstance(value, float):
                    attr_value = {"doubleValue": value}
                elif isinstance(value, bool):
                    attr_value = {"boolValue": value}
                otlp_record["attributes"].append({"key": key, "value": attr_value})
        
        return otlp_record
    
    def _build_payload(self, records: list) -> Dict[str, Any]:
        """Build the OTLP export request payload.
        
        Args:
            records: List of converted OTLP log records
            
        Returns:
            Complete OTLP export request payload
        """
        resource_attrs = [
            {"key": "service.name", "value": {"stringValue": self.service_name}},
        ]
        if self.service_version:
            resource_attrs.append(
                {"key": "service.version", "value": {"stringValue": self.service_version}}
            )
        
        return {
            "resourceLogs": [
                {
                    "resource": {"attributes": resource_attrs},
                    "scopeLogs": [
                        {
                            "scope": {"name": "faciliter-lib-logger"},
                            "logRecords": records,
                        }
                    ],
                }
            ]
        }
    
    def start(self) -> None:
        """Start the background worker thread for sending logs."""
        if self._listener is None:
            self._worker_handler = _OTLPWorkerHandler(
                endpoint=self.endpoint,
                headers=self.headers,
                timeout=self.timeout,
                insecure=self.insecure,
                service_name=self.service_name,
                service_version=self.service_version,
            )
            self._listener = QueueListener(
                self._queue, self._worker_handler, respect_handler_level=True
            )
            self._listener.start()
    
    def stop(self) -> None:
        """Stop the background worker thread and flush pending logs."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._worker_handler is not None:
            self._worker_handler.close()
            self._worker_handler = None
    
    def close(self) -> None:
        """Close the handler and release resources."""
        self.stop()
        super().close()


class _OTLPWorkerHandler(logging.Handler):
    """Internal worker handler that actually sends logs to OTLP collector.
    
    This handler runs in a background thread and batches/sends logs.
    """
    
    def __init__(
        self,
        endpoint: str,
        headers: Dict[str, str],
        timeout: int,
        insecure: bool,
        service_name: str,
        service_version: Optional[str],
    ):
        super().__init__()
        self.endpoint = endpoint
        self.headers = headers
        self.timeout = timeout
        self.insecure = insecure
        self.service_name = service_name
        self.service_version = service_version
        self._batch: list = []
        self._last_send = time.time()
        self._batch_size = 100  # Send after 100 records
        self._batch_timeout = 5.0  # Or after 5 seconds
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record from the queue.
        
        Args:
            record: The log record to process
        """
        try:
            otlp_record = self._convert_to_otlp(record)
            self._batch.append(otlp_record)
            
            # Send if batch is full or timeout reached
            if (
                len(self._batch) >= self._batch_size
                or (time.time() - self._last_send) >= self._batch_timeout
            ):
                self._send_batch()
        except Exception as e:
            # Use stderr to avoid logging recursion
            print(f"OTLP handler error: {e}", file=sys.stderr)
    
    def _convert_to_otlp(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Convert a Python logging record to OTLP log format."""
        severity_map = {
            logging.DEBUG: (5, "DEBUG"),
            logging.INFO: (9, "INFO"),
            logging.WARNING: (13, "WARN"),
            logging.ERROR: (17, "ERROR"),
            logging.CRITICAL: (21, "FATAL"),
        }
        severity_number, severity_text = severity_map.get(
            record.levelno, (0, "UNSPECIFIED")
        )
        
        otlp_record = {
            "timeUnixNano": str(int(record.created * 1_000_000_000)),
            "severityNumber": severity_number,
            "severityText": severity_text,
            "body": {"stringValue": record.getMessage()},
            "attributes": [
                {"key": "logger.name", "value": {"stringValue": record.name}},
                {"key": "source.file", "value": {"stringValue": record.pathname}},
                {"key": "source.line", "value": {"intValue": str(record.lineno)}},
                {"key": "source.function", "value": {"stringValue": record.funcName or ""}},
            ],
        }
        
        return otlp_record
    
    def _send_batch(self) -> None:
        """Send batched logs to OTLP collector."""
        if not self._batch:
            return
        
        try:
            import requests
            
            resource_attrs = [
                {"key": "service.name", "value": {"stringValue": self.service_name}},
            ]
            if self.service_version:
                resource_attrs.append(
                    {"key": "service.version", "value": {"stringValue": self.service_version}}
                )
            
            payload = {
                "resourceLogs": [
                    {
                        "resource": {"attributes": resource_attrs},
                        "scopeLogs": [
                            {
                                "scope": {"name": "faciliter-lib-logger"},
                                "logRecords": self._batch,
                            }
                        ],
                    }
                ]
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                verify=not self.insecure,
            )
            
            if response.status_code not in (200, 202):
                print(
                    f"OTLP export failed: {response.status_code} - {response.text}",
                    file=sys.stderr,
                )
            
            # Clear batch and reset timer
            self._batch = []
            self._last_send = time.time()
            
        except Exception as e:
            # Use stderr to avoid logging recursion
            print(f"OTLP send error: {e}", file=sys.stderr)
            self._batch = []  # Clear to avoid memory buildup
    
    def close(self) -> None:
        """Flush remaining logs before closing."""
        self._send_batch()
        super().close()
