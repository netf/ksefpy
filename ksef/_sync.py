"""Synchronous wrapper utilities for async KSeF clients."""

from __future__ import annotations

import asyncio
import inspect
import threading
from typing import Any


class SyncWrapper:
    """Runs async methods of an AsyncKSeFClient on a private event loop in a daemon thread.

    Usage::

        wrapper = SyncWrapper(async_client)
        result = wrapper.auth.get_challenge()
        wrapper.close()
    """

    def __init__(self, async_client: Any) -> None:
        self._async_client = async_client
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="ksef-sync-event-loop",
        )
        self._thread.start()

        # Enter the async client context on the private loop
        self._run_coroutine(self._async_client.__aenter__())

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_coroutine(self, coro: Any) -> Any:
        """Submit *coro* to the private loop and block until it completes."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def close(self) -> None:
        """Close the underlying async client and stop the event loop."""
        try:
            self._run_coroutine(self._async_client.__aexit__(None, None, None))
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async_client, name)
        if inspect.iscoroutinefunction(attr):
            # Wrap top-level async methods directly
            def _sync_method(*args: Any, **kwargs: Any) -> Any:
                return self._run_coroutine(attr(*args, **kwargs))
            return _sync_method
        # For sub-client objects, wrap them in a SyncSubClient
        if hasattr(attr, "__class__") and not isinstance(attr, (str, int, float, bool, type(None))):
            return SyncSubClient(attr, self._run_coroutine)
        return attr


class SyncSubClient:
    """Wraps an async sub-client object so its async methods are callable synchronously."""

    def __init__(self, sub_client: Any, run_fn: Any) -> None:
        # Store via object.__setattr__ to avoid triggering our own __getattr__
        object.__setattr__(self, "_sub_client", sub_client)
        object.__setattr__(self, "_run_fn", run_fn)

    def __getattr__(self, name: str) -> Any:
        sub_client = object.__getattribute__(self, "_sub_client")
        run_fn = object.__getattribute__(self, "_run_fn")
        attr = getattr(sub_client, name)
        if inspect.iscoroutinefunction(attr):
            def _sync_method(*args: Any, **kwargs: Any) -> Any:
                return run_fn(attr(*args, **kwargs))
            return _sync_method
        return attr
