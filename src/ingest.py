"""
PDF ingestion: parse, section-detect, and chunk a long PDF document.

Pipeline: PDF → pages (PyMuPDF) → sections (heading detection) → chunks
Each Chunk carries its text, section heading, and page range for citations.
"""

from dataclasses import dataclass
from pathlib import Path

import fitz
from . import config

@dataclass
class Chunk:
    chunk_id: int
    text: str
    section: str       # nearest heading above this chunk
    page_start: int    # 1-indexed
    page_end: int      # 1-indexed, inclusive

# Heading Detection
def _span_is_heading(span: dict, body_size: float) -> bool:
    """Return True if a single span looks like a standalone section heading.

    Uses typographic heuristics that generalise across document types:
    - Larger-than-body font (> body_size + 0.5) → major heading regardless of weight
    - Body-size + bold (flags bit 4) → subsection heading
    """
    
    size: float = span["size"]
    bold: bool = bool(span["flags"] & 16)
    if size > body_size + 0.5:
        return True
    if size >= body_size and bold:
        return True
    return False


def _line_is_heading(line: dict, body_size: float, sole_in_block: bool = True) -> bool:
    """Return True if every non-whitespace span in a line is a heading span.
    
    sole_in_block guards against bold text embedded in a multiline paragraph.
    All-lowercase lines are also excluded
    """
    spans = [s for s in line["spans"] if s["text"].strip()]
    if not spans:
        return False
    text = "".join(s["text"] for s in spans).strip()
    if text == text.lower():
        return False
    if not all(_span_is_heading(s, body_size) for s in spans):
        return False
    # If the line qualifies only via bold-at-body-size (not oversized font),
    # require that it stands alone in its block — otherwise it is bold body text.
    oversized = any(s["size"] > body_size + 0.5 for s in spans)
    if not oversized and not sole_in_block:
        return False
    return True


def _line_text(line: dict) -> str:
    return "".join(s["text"] for s in line["spans"])


def _bbox_overlaps(a: tuple, b: tuple) -> bool:
    """Return True if two (x0, y0, x1, y1) bounding boxes overlap."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def _estimate_body_size(doc: fitz.Document, sample_pages: int = 20) -> float:
    """Estimate the dominant body font size by frequency across sample pages."""
    size_counts: dict[float, int] = {}
    total = min(sample_pages, len(doc))
    for page_num in range(total):
        for block in doc[page_num].get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["text"].strip():
                        rounded = round(span["size"] * 2) / 2  # nearest 0.5
                        size_counts[rounded] = size_counts.get(rounded, 0) + 1
    return max(size_counts, key=size_counts.__getitem__)


def extract_sections(
    doc: fitz.Document,
    filter_footnotes: bool = True,
) -> list[dict]:
    """Walk every page and split content into sections by detected headings.

    Skips header/footer zones and footnote-size text by default
    Skips ... or --- text
    Skips text blocks that overlap with table bounding boxes

    Returns a list of dicts:
        {
            "heading": str,
            "text": str,
            "page_start": int,   # 1-indexed
            "page_end": int,     # 1-indexed
        }
    """
    body_size = _estimate_body_size(doc)
    if filter_footnotes:
        min_font = (body_size - config.FOOTNOTE_SIZE_DELTA)
    else:
        min_font = None

    current_heading = "Preamble"
    current_lines: list[str] = []
    current_page_start = 1
    current_page_end = 1
    sections: list[dict] = []
    """
    
    """
    def _flush() -> None:
        text = " ".join(current_lines).strip()
        if text:
            sections.append({
                "heading": current_heading,
                "text": text,
                "page_start": current_page_start,
                "page_end": current_page_end,
            })

    for page_num in range(len(doc)):
        page_no = page_num + 1  # 1-indexed
        page_height = doc[page_num].rect.height
        header_limit = page_height * config.HEADER_ZONE
        footer_limit = page_height * config.FOOTER_ZONE

        try:
            table_bboxes = []
            for tbl in doc[page_num].find_tables().tables:
                table_bboxes.append(tbl.bbox)
        except Exception:
            table_bboxes = []

        blocks = doc[page_num].get_text("dict")["blocks"]

        for block in blocks:
            if block["type"] != 0:  # Skip images
                continue

            # Skip header and footer zones
            y0 = block["bbox"][1]
            if y0 < header_limit or y0 > footer_limit:
                continue

            is_table_block = False
            for tb in table_bboxes:
                if _bbox_overlaps(block["bbox"], tb):
                    is_table_block = True
                    break
            
            # Small font filtering
            if not is_table_block and min_font is not None:
                block_sizes = [
                    s["size"]
                    for line in block["lines"]
                    for s in line["spans"]
                    if s["text"].strip()
                ]
                if block_sizes and max(block_sizes) < min_font:
                    continue

            # Table blocks bypass heading detection to prevent table header cells   
            # being misread as section headings
            if is_table_block:
                for line in block["lines"]:
                    text = _line_text(line).strip()
                    if text:
                        current_lines.append(text)
                current_page_end = page_no
                continue

            # A heading that relies on bold-at-body-size must be the only
            # non-empty line in its block; otherwise it is bold body text.
            non_empty_lines = [l for l in block["lines"] if _line_text(l).strip()]
            sole_in_block = len(non_empty_lines) == 1

            for line in block["lines"]:
                text = _line_text(line).strip()
                if not text:
                    continue

                # Drop dotted lines before they enter the text buffer.
                non_space = [c for c in text if c != " "]
                if non_space and sum(1 for c in non_space if c in ".-") / len(non_space) > 0.5:
                    continue

                if _line_is_heading(line, body_size, sole_in_block=sole_in_block) and len(text) < 120:
                    # Save previous section, start new one
                    _flush()
                    current_heading = text
                    current_lines = []
                    current_page_start = page_no
                    current_page_end = page_no
                else:
                    current_lines.append(text)
                    current_page_end = page_no

    _flush()
    return sections


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

# Approximate token count: 1 token ≈ 4 chars (conservative for English prose)
_CHARS_PER_TOKEN = 4


# def _approx_tokens(text: str) -> int:
#     return len(text) // _CHARS_PER_TOKEN

def _split_into_chunks(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into overlapping chunks by approximate token count.
    Uses word boundaries to avoid mid-word splits.
    """
    max_chars = max_tokens * _CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * _CHARS_PER_TOKEN

    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + max_chars

        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Walk back to the nearest word boundary
        boundary = text.rfind(" ", start, end)
        if boundary == -1 or boundary <= start:
            boundary = end  # no space found, hard split

        chunks.append(text[start:boundary].strip())

        # Advance start, stepping back by overlap; always make forward progress
        start = max(boundary - overlap_chars, start + 1)

    return [c for c in chunks if c]


def build_chunks(sections: list[dict], max_tokens: int = config.CHUNK_MAX_TOKENS, overlap_tokens: int = config.CHUNK_OVERLAP_TOKENS) -> list[Chunk]:
    """Convert sections into Chunk objects, splitting long sections as needed.

    Each chunk inherits its section's heading and page range.  When a section
    is split, all sub-chunks share the same page range
    """
    chunks: list[Chunk] = []
    chunk_id = 0

    for section in sections:
        heading = section["heading"]
        text = section["text"]
        page_start = section["page_start"]
        page_end = section["page_end"]

        sub_texts = _split_into_chunks(text, max_tokens, overlap_tokens)
        for sub in sub_texts:
            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=sub,
                section=heading,
                page_start=page_start,
                page_end=page_end,
            ))
            chunk_id += 1

    return chunks


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ingest(
    pdf_path: Path,
    max_tokens: int = config.CHUNK_MAX_TOKENS,
    overlap_tokens: int = config.CHUNK_OVERLAP_TOKENS,
    filter_footnotes: bool = True,
) -> list[Chunk]:
    """Parse a PDF and return a list of Chunks ready for indexing.
    
    """
    
    doc = fitz.open(str(pdf_path))
    sections = extract_sections(doc, filter_footnotes=filter_footnotes)
    chunks = build_chunks(sections, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    doc.close()
    return chunks

# TEST BLOCK
if __name__ == "__main__":
    import sys

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.pdf"
    chunks = ingest(Path(pdf_path))

    print(f"Total chunks: {len(chunks)}")
    print(f"Avg chunk length: {sum(len(c.text) for c in chunks) // len(chunks)} chars")
    print()

    for i in [340, 341, 342, 343, 344, 350, 351, 352, 353, 354, 356, 358, 360, 370, 380, 390, 400, 410, 430]:
        if i < len(chunks):
            c = chunks[i]
            print(f"--- Chunk {c.chunk_id} | Section: {c.section} | Pages {c.page_start}-{c.page_end} ---")
            print(c.text[:300])
            print()
            
    from collections import Counter
    headings = Counter(c.section for c in chunks)
    for heading, count in headings.most_common(20):
        print(f"{count:4d}  {heading}")
        
    # p51_chunks = [c for c in chunks if c.page_start <= 51 <= c.page_end]
    # print(f"Chunks covering page 51: {len(p51_chunks)}")
    # for c in p51_chunks:
    #     print(f"--- Chunk {c.chunk_id} | {c.section} | Pages {c.page_start}-{c.page_end} ---")
    #     print(repr(c.text[:500]))
    #     print()