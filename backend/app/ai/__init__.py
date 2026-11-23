"""The AI layer (docs/AI-PIPELINE.md): a model registry with checksums, a one-model-at-a-time memory manager, and a
router that tries providers in order and falls back to a person. Runs in the `ai-worker` container, inside the
`ai` network zone, which has no route out. Nothing here makes a network call outside the deployment."""

QUEUE = "ai"                   # the ai-worker's Celery queue (a Redis list of this name)
STATE_KEY = "sethu:ai:state"   # where the ai-worker publishes its state for the health screen
