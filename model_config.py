"""
Model and LLM configuration settings.
These are public configuration options that control the AI behavior.
"""

# OpenAI Model Configuration
# Options: "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview", "gpt-4o", etc.
OPENAI_MODEL = "gpt-3.5-turbo"

# Temperature setting (0.0-2.0)
# Lower = more consistent/focused, Higher = more creative/varied
TEMPERATURE = 0.5

# Base max tokens per snippet
# Will be multiplied by snippet count, capped at 2000
BASE_MAX_TOKENS = 500

