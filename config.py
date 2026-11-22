"""
VeriSync Configuration Module.
Centralizes paths, model configs, and runtime defaults.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CIRCULARS_DIR = DATA_DIR / "circulars"
STORE_DIR = BASE_DIR / "store"
CHROMA_DIR = STORE_DIR / "chroma"

# Ensure runtime directories exist
CIRCULARS_DIR.mkdir(parents=True, exist_ok=True)
STORE_DIR.mkdir(parents=True, exist_ok=True)

# LLM & Embedding Settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Retrieval Settings
DEFAULT_TOP_K = 5
