# TTSPiperModel: without Docker, on Windows

Run Piper text to speech on the CPU directly with Python: one process, no load balancer, listening on `127.0.0.1:9150`.

## Requirements
- Windows with Python 3.11 or newer and uv (`winget install astral-sh.uv`).
- Internet on the first start (63 MB of voice files (each further voice downloads on first use)).
- RAM for the model (one copy).

## Start
Double-click `run.bat`, or run it in a terminal from `TTSPiperModel\`. Choose **1 Run the service** in the menu, or run `run.bat run` to skip the menu. It runs `uv sync` to create or update `.venv`, then starts
`python src/app.py`. The first start downloads 63 MB of voice files (each further voice downloads on first use).

Linux or macOS:
```bash
cd TTSPiperModel
uv sync
uv run python src/app.py
```

## Settings
`run.bat` and `app.py` read the real environment, **not** `.env`. Set variables before starting:

| Variable | Default | Effect |
|---|---|---|
| `TTSPIPER_HOST` | `127.0.0.1` | Bind address. Use `0.0.0.0` only if other devices must reach it. |
| `TTSPIPER_PORT` | `9150` | Port. |
| `TTSPIPER_ADMIN_PASSWORD` | empty | Unlocks `/admin/` and requires tokens on every call but `/health`. Empty = no auth. |
| `TTSPIPER_WARM` | `1` | Load the model at start; with `0` the first request pays the load time. |
| `TTSPIPER_NUM_THREAD` | the library decides | CPU threads. Set it to the number of **physical** cores. |

PowerShell: `$env:TTSPIPER_ADMIN_PASSWORD = "secret"; .\run.bat`
Bash: `TTSPIPER_ADMIN_PASSWORD=secret uv run python src/app.py`

## Check
```bash
curl http://127.0.0.1:9150/health
```
`ready` is `false` until the model has loaded. Then open `http://127.0.0.1:9150/admin/` (see [guide-web-ui.md](guide-web-ui.md)),
make a token, and try a call:
```bash
curl -X POST http://127.0.0.1:9150/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttspiper_..." -d '{"text":"Hello from the model service."}' -o hello.wav
```

## Stop
Ctrl+C in the terminal. Do not run this and the Docker stack together: both use port 9150.

## Tests
`uv run pytest`.
