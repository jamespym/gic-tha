import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


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

# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

INDEX_DIR = DATA_DIR / "index"

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
LLM_MODEL = "gpt-4o-mini"
HALLUCINATION_MODEL = "gpt-4o-mini"  # cheaper model sufficient for binary classification

GENERATION_PROMPT = """\
You are a precise document analyst. Answer the question using ONLY the provided sources.

Rules:
- Cite every claim with the source number in brackets e.g. [1] not the page number — the source number maps to a page already shown to the user.
- If the query is ambiguous in scope (e.g. asks for "total revenue" without specifying a division or segment), prefer the highest-level aggregate figure available in the sources and note that more specific breakdowns exist.
- If the query explicitly names a specific entity, division, or segment, answer at that level.
- If the answer requires a figure not present in the sources, say "The sources do not contain sufficient information to answer this fully" and explain what is missing.
- Never infer or extrapolate beyond what the sources state.
- Be concise. One short paragraph unless the question requires more.

Question: {query}

Sources:
{sources}
"""

HALLUCINATION_PROMPT = """You are evaluating whether an answer correctly responds to a query based only on the provided sources.

Query: {query}

Answer: {answer}

Sources:
{sources}

Check ALL of the following:
1. GROUNDED: Every factual claim in the answer appears in the sources. No numbers or facts are fabricated.
2. SCOPE: The answer matches the scope of the query. If the query asks for a firm-wide figure, a segment-level figure is not an acceptable answer even if it appears in the sources.
3. COMPLETE: The answer does not ignore a more relevant source in favour of a less relevant one.
4. HEDGED: If the sources are insufficient to answer the query fully, the answer acknowledges this rather than presenting a partial answer as complete.

Respond with one of:
PASS - all four criteria are met
FAIL: GROUNDED - answer contains claims not in sources
FAIL: SCOPE - answer answers a different scope than the query (e.g. segment vs firm-wide)
FAIL: COMPLETE - answer overlooks a more relevant source
FAIL: HEDGED - answer presents a partial answer as complete without caveat

Then one sentence explaining your reasoning.
"""