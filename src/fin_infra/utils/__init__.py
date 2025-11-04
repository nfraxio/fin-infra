"""Utilities namespace for fin-infra.

Networking timeouts/retries and related resource limits are provided by svc-infra
and should be consumed from there in services. This package intentionally keeps
no local HTTP/retry wrappers to avoid duplication.
"""

__all__: list[str] = []
