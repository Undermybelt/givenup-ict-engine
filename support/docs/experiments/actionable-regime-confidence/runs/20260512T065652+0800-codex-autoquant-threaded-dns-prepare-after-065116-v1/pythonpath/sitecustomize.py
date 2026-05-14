"""Run-local aiohttp DNS resolver override for AutoQuant prepare diagnostics."""

try:
    import aiohttp.resolver as _resolver

    _resolver.DefaultResolver = _resolver.ThreadedResolver
except Exception:
    pass
