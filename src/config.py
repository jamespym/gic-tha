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
# Approximate token count: 1 token ≈ 4 chars (conservative for English prose).
# Adjust downward for non-Latin scripts or heavily numeric content.
CHARS_PER_TOKEN = 4

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
FOOTNOTE_SIZE_DELTA = 2.0

# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

INDEX_DIR = DATA_DIR / "index"

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
LLM_MODEL = "gpt-4o-mini"

# ---------------------------------------------------------------------------
# Eval metrics
# ---------------------------------------------------------------------------

RETRIEVAL_JUDGE_PROMPT = """\
You are an evaluation judge.

Question: {question}

Retrieved chunks:
{context}

Do the retrieved chunks contain sufficient information to answer the question?
Answer Yes if the chunks contain the facts needed to answer or calculate the answer, even if the final answer is not stated explicitly.
Format your response in this manner:
Answer: <Yes or No>
Explanation: <short explanation>
"""

CORRECTNESS_JUDGE_PROMPT = """\
You are an evaluation judge.

Question: {question}
Reference answer: {expected_answer}
System answer: {answer}

Is the system answer factually correct per the reference answer? Minor phrasing differences are fine, judge based on facts only. Accept rounded answers to ±1 d.p.
Format your response in this manner:
Answer: <Yes or No>
Explanation: <short explanation>
"""

FAITHFULNESS_JUDGE_PROMPT = """\
You are an evaluation judge.

System answer: {answer}

Retrieved chunks:
{context}

Is every factual claim in the system answer supported by the retrieved chunks above?
Format your response in this manner:
Answer: <Yes or No>
Explanation: <short explanation>
"""

GENERATION_PROMPT = """\
You are a precise document analyst. Answer the question using ONLY the provided sources.

Rules:
- Cite every claim with the source number in brackets e.g. [1] not the page number — the source number maps to a page already shown to the user.
- If the query explicitly names a specific entity, division, or segment, answer at that level.
- If the answer requires a figure not present in the sources, say "The sources do not contain sufficient information to answer this fully" and explain what is missing.
- Never infer or extrapolate beyond what the sources state. Calculation is allowed should the question ask for it.
- If the query regards superlatives ("biggest", "lowest", etc) or comparison of items, but the sources list multiple with no way of ranking them explicitly, list all candidates and state that the document does not explicitly rank them.
- Be concise. One short paragraph unless the question requires more.
- Match the level of granularity the question asks for: If it names a specific entity, segment, or item, prefer information at that level. If it's ambiguous, prefer the highest-level aggregate available.
Question: {query}

Sources:
{sources}
"""

