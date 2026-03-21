Assumptions:
1. PDF is text based, not image based
2. 

Prod would need real table parsing

What would change if the domain is not finance but healthcare/CS research? Chunking strategy??

Latency and cost

chars per token = 4 for english, but depending on domain, may change

page number is by global PDF pg no

simple prepending -> test eval -> section level context retrieval if needed

In retrospect, I would have started with recursive character splitting to get an end-to-end pipeline working on Day 1, then upgraded to section-aware chunking after identifying retrieval failures in evaluation. The current implementation went straight to section-aware chunking, which produced better results but delayed the first full integration test.

future improvements:
list chunk size/overlap hyperparam tuning
no per line per page tracking/citing (DO THIS AFTER EVAL, THREAD PG NO THROUGH)

## Hallucination checker

A single-pass hallucination check was implemented in `generate.py`. After generating an answer, a second GPT-4o-mini call re-read the same retrieved chunks and checked the answer against four criteria: grounded, scope, complete, hedged. It returned a PASS/FAIL verdict with a one-sentence reason.

**Why it was removed:**

The checker was given the same 5 retrieved chunks that the generator used — it had no independent access to the full document. This means it was asking a model to verify an answer against the exact context that produced it. In practice it almost always returned PASS, because the answer was generated from those chunks and was locally consistent with them. It was not catching the real failure mode: cases where the retrieved chunks were themselves insufficient or the wrong scope, and the answer was wrong relative to the full document.

**Where it could work:**

LLM-as-judge hallucination checking is well-validated for open-ended generation tasks (summarisation, long-document QA, chatbot responses). The canonical failure mode it targets is when a model ignores retrieved context and answers from parametric memory instead — fabricating figures it "knows" from training data rather than reading the sources. For that failure mode, it works well and is used in frameworks like RAGAS and TruLens.

The issue is that this is not our pipeline's weak point. GPT-4o-mini with explicit grounding instructions is already faithful to whatever chunks it receives. Our failures are upstream — in ingest (tables not parsed well, chunks split across section boundaries) and in retrieval (wrong chunks surface for numerical or firm-wide queries). The checker sees an answer that is locally consistent with the retrieved chunks, returns PASS, and misses the real error entirely.

It would add value in:
- A setup where the checker has access to a broader context than the generator
- Catching scope errors on negative questions (did the model correctly say "I don't know"?)
- A pipeline where generation faithfulness is actually the weak point, e.g. a model without strong instruction-following

**On adding it back for implicit ranking questions:** implicit ranking queries (e.g. "what is the largest operational risk?") were considered as a case where the HC would genuinely help — the model overclaims by presenting one item from a list as definitively the greatest, which the checker's HEDGED criterion would catch. However, this overclaiming is already addressed by prompt engineering ("if sources do not rank items, list all and note the document does not indicate precedence"). Adding the HC on top would be redundant at the generation level, and it still would not address the underlying retrieval problem — top-k may not surface all relevant chunks regardless.

## Known failure modes (19/3/25, pre-eval)

**Ingest/chunking:**
- Tables parsed as garbled text or split across chunks — numbers lose row/column context
- Section boundaries occasionally misdetected — chunks bleed across sections
- Parent headings with no body text (e.g. "Corporate Social Responsibility" immediately followed by subsections) are dropped during section extraction. Subsections don't inherit the parent label, so queries using the parent term miss them. Retrieval still surfaces semantically relevant subsection content, so this is a citation labelling issue more than a factual failure.

**Retrieval:**
- Firm-wide queries surface segment-level chunks instead of consolidated statements (scope mismatch)
- Numerical queries retrieve prose summaries of tables rather than the tables themselves
- Short boilerplate chunks ("None.") rank high when query has no strong signal
- Comparison/superlative queries fail retrieval because they carry no named-entity anchor (e.g. "which segment declined" doesn't mention "More Personal Computing" or "Intelligent Cloud"). The embedding has no strong signal to pull any specific segment's chunk, so entirely irrelevant chunks surface instead. This is distinct from a vocabulary mismatch — "decline" and "decreased" are near-synonyms that bge-small handles correctly. The root cause is that answering requires retrieving chunks for all segments simultaneously and comparing them, which single-query dense retrieval cannot do. A higher top-k partially mitigates this by increasing the chance relevant chunks appear; a proper fix would be query decomposition (detect comparison intent, issue one sub-query per segment). Not addressed in current pipeline.

**Generation:**
- Scope errors — answers at wrong level of aggregation (segment vs firm-wide), partly a retrieval problem, partly prompt
- Incomplete synthesis on cross-section questions — picks dominant source, ignores secondary
- Second-order reasoning — "how did X affect Y" sometimes lists facts separately rather than connecting them

**Root cause:** most failures trace back to ingest quality, not retrieval or generation. Better table parsing would fix numerical-table failures, scope mismatches, and some cross-section failures in one shot.

**Not a failure mode:** hallucination on grounded questions (model rarely fabricates when right chunks are retrieved), negative questions (correctly says "I don't know").

**Implicit ranking questions** (e.g. "what is JPMorgan's largest operational risk?") — document lists items without ranking them. Generation failure: model picks the first/most prominent and states it as fact. Partial fix: prompt engineering ("if sources don't rank, list all and say so"). Retrieval problem remains — top-k may not surface all relevant chunks. Not a separate question type; folded into cross-section questions with hedging as the expected behaviour.

design decisions:
BAAI bge small: Open-source embeddings keep the ingestion pipeline fully local — the entire corpus passes through the embedding model at index time, making data sovereignty a hard constraint at that layer. bge-small-en-v1.5 is competitive on MTEB retrieval benchmarks, runs with no API cost or latency, and decouples index-building from any external dependency. GPT-4o-mini is used for generation because generation quality is directly user-visible and meaningfully better than comparably-sized open-source models for citation-accurate financial Q&A; a weak generator conflates retrieval failures with generation failures and makes eval uninformative. In production, this would swap to Azure OpenAI (in-region deployment) to satisfy data residency requirements while retaining generation quality.

Consolidated financial statement tables (e.g. page 53 income statement) are not retrieved for firm-wide queries like "revenue growth". Segment-level narrative chunks surface instead because they contain semantically rich prose. Enrich.py will address this by prepending LLM-generated summaries to table chunks before embedding. Expected impact: high for numerical/comparison queries, low for qualitative queries.

can also add or test retrieval quality by positioning query below sources [lost in the middle]. check if retrieval quality is the bottleneck first.

**Derived metric queries** (e.g. "what is the gross margin for 2022?") — gross margin is revenue / COGS, but the query only says "gross margin". FAISS/BM25 retrieve on the query string alone and have no way to know two separate chunks are needed. Fails silently if the figure isn't stated explicitly in the document. HyDE would help (hypothetical answer embeds revenue + COGS signals); query decomposition would explicitly split into sub-queries. Known limitation, not addressed in current pipeline.

INGEST/RETRIEVAL IS BROKENNNN ON TABLES

## Evaluation Design

### Why not a single 1–5 score
The original judge used one 1–5 score per question. Two problems: (1) ambiguous boundaries — the LLM picks 3 vs 4 inconsistently, (2) it conflates retrieval and generation failures. A score of 2/5 could mean wrong chunks retrieved, or right chunks but model hallucinated — different root causes, different fixes.

### Why not grounded floats (RAGAS-style)
Decompose expected answer into atomic facts, verify each binary, score = X/N. More principled, but adds multiple LLM calls per metric and GPT-4o-mini is unreliable at consistent decomposition in one pass. The added complexity doesn't change the diagnostic story.

### What was chosen: three binary dimensions
Results reported as pass rates across 20 questions, broken down by question type.

- **Retrieval** (`question + chunks`): do the retrieved chunks contain sufficient information?
- **Correctness** (`question + expected + answer`): is the answer factually correct per ground truth?
- **Faithfulness** (`question + answer + chunks`): does the answer stay within the retrieved context?

Binary eliminates boundary ambiguity. The diagnostic value comes from the breakdown: 89% retrieval pass on prose vs 22% on table questions is a cleaner finding than a 3.1/5 average.

### top_k ablation (5 → 10)

Increasing reranker top_k from 5 to 10 improved retrieval from 70% to 85% (14→17/20), confirming that relevant chunks existed in the index but weren't surfacing. However, correctness only moved from 50% to 61% (9→11/18), and cases where retrieval passes but correctness fails increased from 5 to 6. More chunks means more competing numbers in the prompt — GPT-4o-mini grabs the wrong figure even when the right one is present. The remaining failures are now almost entirely generation-side: table correctness is still 50%, superlative correctness 33%. The bottleneck has shifted from retrieval to number disambiguation at generation. The fix is not more chunks but better generation — e.g. instructing the model to prefer the most specific figure that directly matches the query, or using a stronger model as generator.