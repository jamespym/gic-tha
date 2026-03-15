import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4o"

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

CHUNK_MAX_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 100

# ---------------------------------------------------------------------------
# Ingest / PDF parsing
# ---------------------------------------------------------------------------

# Header and footer exclusion zones as a fraction of page height.
# Text blocks whose top edge falls within [0, HEADER_ZONE] or
# [FOOTER_ZONE, 1.0] are dropped as running headers/footers/page numbers.
# Tune these if your document has unusually tall headers or footers.
HEADER_ZONE = 0.05
FOOTER_ZONE = 0.93

# Drop text blocks whose maximum font size is more than this many points
# below the estimated body size. Catches footnotes and fine print.
# Set to None to disable footnote filtering entirely.
FOOTNOTE_SIZE_DELTA = 1.5