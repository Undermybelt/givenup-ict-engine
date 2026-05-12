import os
import sys


if os.environ.get("ICT_ENGINE_AQ_FORCE_THREADED_RESOLVER") == "1":
    try:
        import aiohttp.connector as connector
        import aiohttp.resolver as resolver

        resolver.DefaultResolver = resolver.ThreadedResolver
        connector.DefaultResolver = resolver.ThreadedResolver
        print(
            "ict_engine_autoquant_threaded_resolver_sitecustomize=applied",
            file=sys.stderr,
        )
    except Exception as exc:  # pragma: no cover - diagnostic shim only
        print(
            f"ict_engine_autoquant_threaded_resolver_sitecustomize=failed:{exc!r}",
            file=sys.stderr,
        )
