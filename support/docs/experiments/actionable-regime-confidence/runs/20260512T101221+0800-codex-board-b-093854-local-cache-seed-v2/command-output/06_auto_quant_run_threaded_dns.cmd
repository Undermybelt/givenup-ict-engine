cd "$AQ_ROOT" && uv run --with ta-lib python - <<'PY'
import runpy
import aiohttp.connector
import aiohttp.resolver

aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
aiohttp.connector.DefaultResolver = aiohttp.resolver.ThreadedResolver
runpy.run_path("run.py", run_name="__main__")
PY
