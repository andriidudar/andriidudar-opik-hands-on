"""Bike workshop chat assistant."""

import os

# Opik reads the project name when it is first imported, so pin it here, before
# any module imports opik. Without it, traces land in the "Default Project".
os.environ["OPIK_PROJECT_NAME"] = "openai-bike-workshop-chat"
