# Test configuration and fallbacks for faciliter-lib
#
# Provides a lightweight fallback for async tests when pytest-asyncio
# plugin is not installed. This ensures repository tests still run in
# minimal environments while preserving compatibility with pytest-asyncio
# when it is available.

import inspect
import asyncio
import logging
from typing import Any
import pytest

logger = logging.getLogger("faciliter_lib.tests")


def pytest_configure(config: Any) -> None:
    config.addinivalue_line(
        "markers", "asyncio: mark test as asynchronous (fallback provided if pytest-asyncio missing)"
    )


def pytest_pyfunc_call(pyfuncitem):  # type: ignore
    """Fallback async test runner.

    If pytest-asyncio is installed we do nothing and allow the plugin to manage execution.
    Otherwise we detect coroutine functions marked with @pytest.mark.asyncio and run them
    using asyncio.run().
    """
    # If pytest-asyncio plugin present, defer to it
    if any(name.startswith("pytest_asyncio") for name, _ in pyfuncitem.config.pluginmanager.list_name_plugin()):
        return False  # let plugin handle

    if "asyncio" in pyfuncitem.keywords and inspect.iscoroutinefunction(pyfuncitem.obj):
        asyncio.run(pyfuncitem.obj(**pyfuncitem.funcargs))
        return True  # indicate we handled invocation
    return False
