# TTSPiperModel: Docker on a deployment machine

Run Piper text to speech on the CPU on a separate always-on machine (default `lex@scutiserver1.local`, folder
`/media/ZimaOS-HD/Apps/TTSPiperModel`). Callers reach it over the published port.

## Requirements on the machine
- Docker + Compose v2, and ssh access (root over ssh is refused; use the normal user).
- Enough RAM for the model times `TTSPIPER_REPLICAS`.

## 1. Publish the code (from your PC)
Run `TTSPiperModel\tools\deploy.bat`. Menu:

| Option | Does |
|---|---|
| 1 | Publish code to the `live` branch |
| 2 | Copy your `.env` to the server (one ssh/tar session, one password prompt) |
| 3 | Both |
| 4, 5 | Dry runs of 1 and 2 |
| 6 | chown helper, if option 2 says `Permission denied` |
| R | Release: publish, then tag `VERSION` |

Keep your own target in the git-ignored `tools\deploy.local.bat` (copy `tools\deploy.local.example.bat`), or set
`DEPLOY_HOST`, `DEPLOY_DIR` and `DEPLOY_WEB_PORT` before running. Commit `main` first: publish reads committed `main`.

## 2. First-time setup on the machine
```bash
mkdir -p /media/ZimaOS-HD/Apps
git clone -b live <your-repo-url> /media/ZimaOS-HD/Apps/TTSPiperModel
cd /media/ZimaOS-HD/Apps/TTSPiperModel
```
Create `.env` (deploy option 2 copies yours, or `cp .env.example .env` and edit):
- `TTSPIPER_ADMIN_PASSWORD`: a real password.
- `TTSPIPER_REPLICAS=1` unless you have the memory for more.
- `TTSPIPER_PORT=9150` (published on all interfaces; firewall it if the LAN should not reach it, or bind it to
  `127.0.0.1` in the `ports:` line of `ttspiper_lb` when only callers on the machine need it).

## 3. Start
```bash
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:9150/health
```
The first start downloads 63 MB of voice files (each further voice downloads on first use) into the `models` volume; `ttspiper_lb` waits for a healthy service
(up to 300 s grace).

## 4. Connect callers
1. Open `http://<machine-ip>:9150/admin/`, sign in with the admin password and create one token per caller
   (see [guide-web-ui.md](guide-web-ui.md)).
2. The caller holds the URL and token:
   - Caller on another machine: `http://<machine-ip>:9150`.
   - Caller in a Docker stack on the same machine: `http://host.docker.internal:9150`.
3. Try a call from the machine:
   ```bash
   curl -X POST http://127.0.0.1:9150/v1/speak -H "Content-Type: application/json" -H "X-Internal-Token: ttspiper_..." -d '{"text":"Hello from the model service."}' -o hello.wav
   ```

## Updating
```bash
cd /media/ZimaOS-HD/Apps/TTSPiperModel
git pull
docker compose up -d --build
docker compose restart ttspiper_lb
```

## Problems
| Symptom | Fix |
|---|---|
| Caller cannot reach the service | Check the caller's URL and token, and that `curl http://<machine-ip>:9150/health` works. |
| nginx 502 after an update | `docker compose restart ttspiper_lb`. |
| Permission denied on push | deploy.bat option 6. |
| Port 9150 in use | Another stack on the machine already publishes it. |
