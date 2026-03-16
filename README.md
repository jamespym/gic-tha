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
hallucination check
no per line per page tracking/citing (DO THIS AFTER EVAL, THREAD PG NO THROUGH)

design decisions:
BAAI bge small: local for data sovereignty. small, fast (no api call latency), free. product would probably use bge-large

Consolidated financial statement tables (e.g. page 53 income statement) are not retrieved for firm-wide queries like "revenue growth". Segment-level narrative chunks surface instead because they contain semantically rich prose. Enrich.py will address this by prepending LLM-generated summaries to table chunks before embedding. Expected impact: high for numerical/comparison queries, low for qualitative queries.