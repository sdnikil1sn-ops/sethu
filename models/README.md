# Models

The AI layer loads models only from this folder, mounted read-only into the `ai-worker` at `/models`
(`SETHU_MODELS_DIR`). `manifest.json` lists each model with its SHA-256; a model whose files do not match is
refused. Nothing is downloaded at run time.

Add a model on a machine with internet access, never inside a container: `python scripts/fetch_models.py` (see
docs/AI-PIPELINE.md, "Adding a model"). Then copy this folder to the AICTE host.

`stub-echo` is a few bytes used by the stub providers and the tests; it is not a real model.
