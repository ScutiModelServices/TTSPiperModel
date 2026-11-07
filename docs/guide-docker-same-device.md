# TTSPiperModel: Docker Desktop on this PC

Run Piper text to speech on the CPU in Docker Desktop on the machine you work on, so other programs on it can call it.

## Requirements

- Docker Desktop with Compose v2 (Windows: WSL2 backend).
- RAM per replica: about 300 MB with one voice loaded (measured on Windows; each replica loads its own copy). Keep `TTSPIPER_REPLICAS=1` on a PC. Docker Desktop on Windows caps its engine at about half of your RAM unless you raise it in `.wslconfig`.
- Network access on the first start to download the files (63 MB per voice) from Hugging Face.
- CPU only, no GPU needed.

## Steps

1. Configure. In `TTSPiperModel/`:
   ```bash
   cp .env.example .env
   ```
   Set `TTSPIPER_ADMIN_PASSWORD` (empty = no auth and no admin page, fine for a local test). Leave `TTSPIPER_PORT=9150`. Leave `TTSPIPER_REPLICAS=1`.
2. Start:
   ```bash
   docker compose up -d --build
   ```
   The first start downloads 63 MB of voice files (each further voice downloads on first use) into the `models` volume. `ttspiper_lb` starts only after the service is healthy
   (up to 300 s grace). Watch with `docker compose ps` and `docker compose logs -f ttspiper`.
3. Check:
   ```bash
   curl http://127.0.0.1:9150/health
   ```
   `ready` is `false` until the model has loaded, then `true`.
4. Open the admin page: `http://127.0.0.1:9150/admin/` (see [guide-web-ui.md](guide-web-ui.md)) and make a token for each caller.
5. Try a call:
   ```bash
   curl -X POST http://127.0.0.1:9150/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttspiper_..." -d '{"text":"Hello from the model service."}' -o hello.wav
   ```
   Expect a WAV file, `hello.wav`.
6. Callers connect to the published port. The caller holds the URL and token:
   - Caller on the host: `http://127.0.0.1:9150`.
   - Caller in another Docker stack on the same host: `http://host.docker.internal:9150`.

## Settings

In `.env` next to `docker-compose.yml`:

| Variable | Default | Effect |
|---|---|---|
| `TTSPIPER_REPLICAS` | `1` | Number of `ttspiper` containers. Read by Compose. |
| `TTSPIPER_PORT` | `9150` | Host port `ttspiper_lb` publishes. |
| `TTSPIPER_ADMIN_PASSWORD` | empty | Password for `/admin/`. When set, every call except `/health` must send a token as `X-Internal-Token`. Empty = no auth. |
| `TTSPIPER_NUM_THREAD` | onnxruntime decides | Starting value for the CPU threads card; a value saved on `/admin/` wins. Use the number of physical cores (`lscpu`: cores x sockets), not logical CPUs; more threads than cores slows every call. |

On the **Settings** card of `/admin/` (saved in `settings.json` beside the tokens, shared by all replicas; a saved
value beats the environment variable named in brackets): update check hours (`TTSPIPER_UPDATE_CHECK_HOURS`, 6),
in-flight cap (`TTSPIPER_MAX_INFLIGHT`, 0 = 4), answers kept per replica (`TTSPIPER_CACHE_SIZE`, 64, 0 = off; at most 1 MB each), voices served (`TTSPIPER_VOICES`, default `en_US-lessac-medium`; comma separated Piper voice names, the first is the default, each downloads on first use), voices repository (`TTSPIPER_MODEL`, restart) and load at start (`TTSPIPER_WARM`, restart). Compose does not pass these;
add the variable under `environment:` of `ttspiper` to use one as a starting value.

## Daily use

```bash
docker compose ps          # state
docker compose logs -f ttspiper
docker compose down        # stop (the weights volume is kept)
docker compose up -d --build && docker compose restart ttspiper_lb   # after a code change
```

## Time it

Try it and time it:

```bash
python tools/bench.py http://127.0.0.1:9150 --save out
```

## Problems

| Symptom | Fix |
|---|---|
| `address already in use` on 9150 | Another copy (`run.bat`, or the same stack on another compose project) is running. Stop it or change `TTSPIPER_PORT`. |
| `/health` shows `ready: false` for minutes | First start: the weights are downloading or loading. Check `docker compose logs -f ttspiper`. |
| 401 Invalid token | The caller's token is missing or revoked; make one on `/admin/`. |
| Container restarts in a loop | Out of RAM. Raise the Docker Desktop memory limit or lower the replica count. |
| `ttspiper_lb` never starts | No replica is healthy yet (first download, or out of memory). `docker compose logs ttspiper`. |
| Replicas restart in a loop | Out of RAM. Lower `TTSPIPER_REPLICAS`. |
| 403 "may not use voice" | The token's list on `/admin/` does not include that voice (or the default voice, when `voice` is left out). |
| 404 on `/v1/speak` | The voice is not served here. `GET /v1/voices` lists them. |
| 422 on `format` or another field | Only `text`, `voice` and `speed` exist; the reply is always WAV. |
| 429 | Over the token's rate limit, or too many calls waiting for the model. |
| nginx 502 after scaling | `ttspiper_lb` not restarted after the replica count changed. |
