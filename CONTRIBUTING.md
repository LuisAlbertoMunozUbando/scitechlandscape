# Contributing to Science–Technology Landscape

Thank you for helping improve the Science–Technology Landscape.

## Ways to contribute

We especially welcome contributions to scoring methodology, benchmark datasets, scientific landmark data, prompt design, model evaluation, visualisation, multilingual support, scholarly-data integrations, accessibility, documentation, and deployment reliability.

## Workflow

1. Fork the repository or create a feature branch.
2. Keep each change focused and explain the motivation.
3. Test the application locally.
4. Open a Pull Request describing what changed and why.
5. For changes to the meaning of the X/Y axes, scoring methodology, Nobel proximity, or evaluation criteria, please open an Issue first so the assumptions can be discussed publicly.

## Scientific transparency

Please distinguish measured evidence from model inference. Scores produced by an LLM are analytical estimates rather than objective measures of paper quality, truth, importance, or prize-worthiness.

Changes to scoring should document:

- the intended interpretation of each score;
- evidence used by the classifier;
- expected failure modes;
- calibration or benchmark examples when possible.

## Security

Never commit API keys, tokens, credentials, private endpoints, or `.env` files. The public web application should access the LLM through the backend; the local model endpoint should not be exposed directly to the Internet.

## Style

Prefer readable code, small changes, descriptive commits, and documentation for non-obvious methodological decisions.
