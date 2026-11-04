# Deploying TTSPiperModel

TTSPiperModel is one HTTP service (port 9150). It runs as `ttspiper` replicas behind an nginx load balancer,
`ttspiper_lb`. Callers use `http://<host>:9150`; they never reach a replica directly.

## Requirements

- Docker with Compose v2.
- RAM per replica: about 300 MB with one voice loaded (measured on Windows; each replica loads its own copy).
- Network access on the first start to download the files (63 MB per voice) from Hugging Face.
- CPU only, no GPU needed.

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

## Start

```bash
docker compose up -d --build
curl http://127.0.0.1:9150/health
```

Expect `"ready": true` once a replica has loaded the model. The first start downloads the files into the `models`
volume, so `ttspiper_lb` can take a minute to appear (the health check allows 300 s before failures count; run
`docker compose ps` and wait).

Try it and time it:

```bash
python tools/bench.py http://127.0.0.1:9150 --save out
```

## Scaling

```bash
TTSPIPER_REPLICAS=3 docker compose up -d --build
docker compose restart ttspiper_lb
```

The restart is needed because nginx resolves replica addresses once at start.

## Updating the files

The **Updates** card compares the downloaded revision of the Hugging Face repository with its newest one. **Download
new weights** fetches them into the models volume; every replica drops its old copy within a few seconds and loads the
new one on its next request. Updating the service itself: `docker compose up -d --build`, then
`docker compose restart ttspiper_lb`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ttspiper_lb` never starts | No replica is healthy yet (first download, or out of memory). `docker compose logs ttspiper`. |
| Replicas restart in a loop | Out of RAM. Lower `TTSPIPER_REPLICAS`. |
| 401 "Invalid token" | The caller sends no token, or a revoked one. |
| 403 "may not use voice" | The token's list on `/admin/` does not include that voice (or the default voice, when `voice` is left out). |
| 404 on `/v1/speak` | The voice is not served here. `GET /v1/voices` lists them. |
| 422 on `format` or another field | Only `text`, `voice` and `speed` exist; the reply is always WAV. |
| 429 | Over the token's rate limit, or too many calls waiting for the model. |
| nginx 502 after scaling | `ttspiper_lb` not restarted after the replica count changed. |

## Releasing

A plain publish (`tools\deploy.bat` option 1) only updates the `live` branch. For a release set `VERSION` (and
`pyproject.toml` to the same number), commit, then run `tools\deploy.bat` option R or
`py tools\publish_live.py --release`. `tools\make_zip.bat` then builds `zip_versions\TTSPiperModel-<VERSION>.zip`.
