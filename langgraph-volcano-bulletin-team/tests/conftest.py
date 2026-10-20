import os

# The chat model is built at import time and wants a key; tests never call it.
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
