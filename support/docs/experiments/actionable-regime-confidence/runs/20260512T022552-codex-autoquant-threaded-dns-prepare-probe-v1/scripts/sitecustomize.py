"""Force aiohttp to use system getaddrinfo for this Auto-Quant probe only.

This file is loaded through PYTHONPATH by the bounded DNS workaround probe. It
does not patch ict-engine or the managed Auto-Quant checkout.
"""

try:
    import aiohttp.connector as _aiohttp_connector
    import aiohttp.resolver as _aiohttp_resolver

    _aiohttp_resolver.DefaultResolver = _aiohttp_resolver.ThreadedResolver
    _aiohttp_connector.DefaultResolver = _aiohttp_resolver.ThreadedResolver
except Exception:
    pass
