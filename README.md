# Science–Technology Landscape

Open-source community project for interactively mapping scientific papers across two dimensions:

- **X — Scientific Fundamentalness**: from applied/engineering-oriented work to fundamental mechanisms, theory, and basic science.
- **Y — Demonstrated Technological Maturity**: from speculative/early-stage ideas to validated prototypes, real-world deployment, clinical/industrial evidence, and operational technology.

The application can analyse a paper title and abstract with a local OpenAI-compatible LLM endpoint and place the paper on the landscape. It also compares the paper with representative Nobel scientific landmarks using conceptual, geometric, and hybrid proximity modes.

> Nobel proximity is a thematic/reference aid only. It is **not** a claim that a paper is Nobel-level, correct, or prize-worthy.

## Architecture

- `server.py` — FastAPI backend
- `index.html`, `app.js`, `style.css` — interactive frontend
- `data/nobel.json` — representative Nobel landmarks used by the visualisation
- Local/OpenAI-compatible LLM endpoint through `SPARK_BASE_URL`

Typical local configuration:

```bash
SPARK_BASE_URL=http://127.0.0.1:8001/v1
SPARK_MODEL=auto
```

The application itself can run on port `8012`.

## Community contributions

Contributions are welcome. Useful areas include:

- better scientific/technology scoring methodologies
- calibration datasets and benchmark papers
- improved prompts and structured-output validation
- broader Nobel/scientific landmark datasets
- new visualisations and uncertainty displays
- multilingual support
- reproducibility and evaluation tools
- accessibility and UI improvements
- connectors to arXiv, Crossref, OpenAlex, Semantic Scholar, PubMed, and other open scholarly sources

Please open an Issue for substantial methodological changes and use Pull Requests for proposed improvements.

## Development principle

The scores are analytical estimates, not objective measures of scientific quality. Contributions should preserve transparency about model uncertainty, evidence, and limitations.

## Running locally

Create a `.env` file, for example:

```bash
cat > .env <<'EOF'
SPARK_BASE_URL=http://127.0.0.1:8001/v1
SPARK_MODEL=auto
EOF
```

Then start the FastAPI application using the provided `run.sh` or your preferred Uvicorn setup.

Health endpoint:

```text
/api/health
```

Paper-analysis endpoint:

```text
/api/analyze
```

## Deployment

The production instance is intended to be available at:

```text
https://stl.albertomunoz.ai
```

The public hostname should proxy to the FastAPI service running on the DGX Spark, without exposing the local LLM endpoint itself.

## License

A permissive open-source licence is recommended so the community can improve and redistribute the project. See `LICENSE`.
