"""GELF (Graylog Extended Log Format) handler for OVH Logs Data Platform.

This module provides a TCP-based GELF handler that sends structured logs
to OVH Logs Data Platform or any GELF-compatible endpoint.

The handler is only imported and initialized when OVH LDP is enabled,
minimizing overhead for applications that don't use it.
"""

import json
import logging
import socket
import zlib
from logging.handlers import SocketHandler
from typing import Dict, Optional


class GELFTCPHandler(SocketHandler):
    """GELF (Graylog Extended Log Format) handler over TCP.
    
    Sends logs to OVH Logs Data Platform or any GELF-compatible endpoint.
    Supports compression, TLS, and custom fields.
    
    Features:
    - TLS/SSL encryption
    - GZIP compression
    - OVH token authentication
    - Custom field injection
    - Automatic reconnection on errors
    """
    
    def __init__(
        self, 
        host: str, 
        port: int, 
        token: Optional[str] = None,
        use_tls: bool = True,
        compress: bool = True,
        additional_fields: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ):
        """Initialize GELF TCP handler.
        
        Args:
            host: GELF endpoint hostname (e.g., gra1.logs.ovh.com)
            port: GELF port (default: 12202 for TCP)
            token: OVH LDP authentication token
            use_tls: Enable TLS/SSL encryption
            compress: Enable GZIP compression
            additional_fields: Custom fields to include in every log
            timeout: Socket connection timeout in seconds
        """
        super().__init__(host, port)
        self.token = token
        self.use_tls = use_tls
        self.compress = compress
        self.additional_fields = additional_fields or {}
        self.timeout = timeout
        self.closeOnError = True
        
    def makeSocket(self, timeout=1):
        """Create a socket with optional TLS.
        
        Returns:
            socket.socket: Connected socket or None on failure
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        
        if self.use_tls:
            try:
                import ssl
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.host)
            except Exception as e:
                # Use stderr to avoid logging recursion
                import sys
                print(f"GELF TLS wrapping failed: {e}", file=sys.stderr)
        
        try:
            sock.connect((self.host, self.port))
            return sock
        except Exception as e:
            # Use stderr to avoid logging recursion
            import sys
            print(f"GELF failed to connect to {self.host}:{self.port}: {e}", file=sys.stderr)
            return None
    
    def makePickle(self, record):
        """Convert LogRecord to GELF format (JSON).
        
        Args:
            record: logging.LogRecord instance
            
        Returns:
            bytes: GELF message as JSON bytes with null terminator
        """
        # Map Python log levels to syslog levels
        level_map = {
            logging.DEBUG: 7,
            logging.INFO: 6,
            logging.WARNING: 4,
            logging.ERROR: 3,
            logging.CRITICAL: 2,
        }
        
        gelf_dict = {
            "version": "1.1",
            "host": socket.gethostname(),
            "short_message": record.getMessage(),
            "timestamp": record.created,
            "level": level_map.get(record.levelno, 6),
            "_logger": record.name,
            "_line": record.lineno,
            "_file": record.pathname,
            "_function": record.funcName,
            "_process": record.process,
            "_thread": record.thread,
        }
        
        # Add token if provided (for OVH LDP authentication)
        if self.token:
            gelf_dict["_X-OVH-TOKEN"] = self.token
        
        # Add additional custom fields
        for key, value in self.additional_fields.items():
            if not key.startswith("_"):
                key = f"_{key}"
            gelf_dict[key] = value
        
        # Add exception info if present
        if record.exc_info:
            gelf_dict["full_message"] = self.format(record)
            gelf_dict["_exception"] = str(record.exc_info[1])
        
        # Convert to JSON bytes
        json_bytes = json.dumps(gelf_dict).encode("utf-8")
        
        # Compress if enabled
        if self.compress:
            json_bytes = zlib.compress(json_bytes)
        
        # GELF TCP: null-byte terminated
        return json_bytes + b"\x00"
    
    def send(self, s):
        """Send the pickled bytes to the socket.
        
        Args:
            s: bytes to send
        """
        if self.sock is None:
            self.createSocket()
        if self.sock:
            try:
                self.sock.sendall(s)
            except Exception:
                self.sock.close()
                self.sock = None
