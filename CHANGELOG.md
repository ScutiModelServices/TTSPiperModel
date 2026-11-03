# Changelog

## Unreleased

- First version: Piper text to speech (default voice `en_US-lessac-medium`) served on the CPU, with the admin page, tokens (scope, rate limit, expiry), metrics,
  Settings card, update checks and file downloads shared with the other model services.
- `POST /v1/speak` takes `text`, `voice` and `speed` and returns a WAV file. `GET /v1/voices` lists the voices.
- `tools/bench.py` times a service so `TTSPiperModel` and `TTSParadeeModel` can be compared.
