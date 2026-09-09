# Science–Technology Landscape · Spark

Paste a paper abstract and position it on a 2D map:

- **X** = scientific fundamentalness (applied/engineering → fundamental science)
- **Y** = demonstrated technology maturity (claims of future potential do not raise Y by themselves)
- **Potential** = separate future technology potential score
- **Nobel Proximity** = three views: conceptual affinity, map-position proximity, and hybrid proximity

The Nobel comparison is a **reference mechanism only**. It does not imply that a submitted paper is Nobel-level.

## Run locally on DGX Spark

```bash
unzip paper-scitech-spark.zip
cd paper-scitech-spark
chmod +x install_spark.sh
./install_spark.sh
```

Default URLs:

- App: `http://127.0.0.1:8012`
- Health: `http://127.0.0.1:8012/api/health`

From another computer on the same LAN use `http://SPARK_IP:8012`.

## LLM connection

The app expects an OpenAI-compatible endpoint. Defaults:

```bash
SPARK_BASE_URL=http://127.0.0.1:8000/v1
SPARK_MODEL=auto
```

`auto` calls `/v1/models` and prefers the strongest-looking general instruct/reasoning model, excluding embedding/reranking/ASR models.

To pin a model:

```bash
SPARK_MODEL="your/model-id" ./install_spark.sh
```

Or edit `.env` after installation, then:

```bash
systemctl --user restart paper-scitech-landscape
```

## Useful commands

```bash
systemctl --user status paper-scitech-landscape
journalctl --user -u paper-scitech-landscape -f
curl http://127.0.0.1:8012/api/health
curl http://127.0.0.1:8000/v1/models
```

## Architecture

- FastAPI serves the static frontend and `/api/analyze`
- Spark LLM receives title + abstract + compact Nobel reference catalogue
- LLM returns strict JSON: area, coordinates, maturity, potential, confidence, evidence signals, and conceptual Nobel affinity
- Backend computes geometric distance to each Nobel and a hybrid score:
  - 65% conceptual affinity
  - 35% map-position proximity
- Browser stores analysed papers in `localStorage` for this mockup

## Next production steps

For public deployment, add authentication, PostgreSQL persistence, rate limiting, audit logging, a Cloudflare Tunnel, and a fixed/versioned model + prompt so scores are reproducible.
