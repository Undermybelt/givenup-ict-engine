"""Force aiohttp to use system getaddrinfo for this isolated Auto-Quant run.

This mirrors the bounded 022552 resolver shim and is loaded only through this
run's PYTHONPATH. It does not patch ict-engine or the managed Auto-Quant code.
"""

try:
    import aiohttp.connector as _aiohttp_connector
    import aiohttp.resolver as _aiohttp_resolver

    _aiohttp_resolver.DefaultResolver = _aiohttp_resolver.ThreadedResolver
    _aiohttp_connector.DefaultResolver = _aiohttp_resolver.ThreadedResolver
except Exception:
    pass
