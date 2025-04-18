import os
from dotenv import load_dotenv

# Load .env file while preserving system environment variables (e.g. Azure App Settings)
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=False)

# App identity
TOOL_NAME = "MyClinicalTrialsHub"
TOOL_EMAIL = "myemail@example.com"

# Port configuration
PORT = int(os.getenv("PORT", 5050))

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# CORS origins list (split by comma, strip whitespace, ignore empty strings)
RAW_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = [origin.strip() for origin in RAW_CORS_ORIGINS.split(",") if origin.strip()]
