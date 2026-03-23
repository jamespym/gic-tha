# Appendix — Detailed Evaluation Results

## Standard question set

`eval_20260322_204811_topk10.json` · 40 questions

| ID | Question | Type | Source | Ret | Corr | Faith |
|---|---|---|---|:---:|:---:|:---:|
| Q001 | What was the total purchase price Microsoft paid for Nuance Communications? | factoid | prose | ✓ | ✓ | ✓ |
| Q002 | How many jobs did Microsoft eliminate as part of the January 2023 cost-cutting? | factoid | prose | ✓ | ✓ | ✓ |
| Q003 | What change in accounting estimate did Microsoft make effective fiscal year 2023 regarding server and network equipment, and what was its impact on operating income? | factoid | prose | ✓ | ✓ | ✓ |
| Q004 | What was Microsoft's effective tax rate for FY2023, and what drove the change vs FY2022? | factoid | prose | ✓ | ✓ | ✓ |
| Q005 | What was Microsoft's total revenue for fiscal year 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q006 | What was the revenue for the Intelligent Cloud segment in FY2023? | factoid | table | ✓ | ✓ | ✓ |
| Q007 | How much did Microsoft spend on additions to property and equipment (capex) in FY2023? | factoid | table | ✓ | ✓ | ✓ |
| Q008 | How much was Microsoft's common stock and paid-in capital as of 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q009 | What was the revenue from Server products and cloud services in FY2023? | factoid | table | ✓ | ✓ | ✓ |
| Q010 | Which reportable segment had the highest operating income in FY2023? | superlative | table | ✓ | ✓ | ✓ |
| Q011 | Which product/service category had the greatest growth in revenue from FY2022 to FY2023? | superlative | table | ✓ | **✗** | ✓ |
| Q012 | Which segment experienced a decline in revenue in FY2023 compared to FY2022? | superlative | table+prose | ✓ | ✓ | ✓ |
| Q013 | What was Microsoft's revenue from only its Azure cloud service? | negative | n/a | - | ✓ | ✓ |
| Q014 | How many employees does Microsoft have as of June 30, 2024? | negative | n/a | - | ✓ | ✓ |
| Q015 | How does Microsoft's goodwill balance as of June 30, 2023 break down by segment? | cross_section | table+prose | ✓ | ✓ | ✓ |
| Q016 | What was Microsoft Cloud revenue in FY2023, and what percentage of total revenue did it represent? | cross_section | table+prose | ✓ | ✓ | ✓ |
| Q017 | What was Microsoft's gross profit margin for fiscal year 2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q018 | What was the year-over-year change in short-term investments from 2022 to 2023? | multi_hop | table | ✓ | **✗** | ✓ |
| Q019 | How much of the total contractual obligations due in fiscal year 2024 is attributable to 
  purchase commitments? | multi_hop | table | ✓ | ✓ | ✓ |
| Q020 | What were Microsoft's total operating expenses (R&D + Sales & Marketing + G&A) in FY2023? | multi_hop | table+prose | ✓ | **✗** | ✓ |
| Q021 | What was Microsoft's diluted earnings per share for fiscal year 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q022 | What were Microsoft's total assets as of June 30, 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q023 | What was the agreed-upon acquisition price for Activision Blizzard, and has it closed? | factoid | prose | ✓ | ✓ | ✓ |
| Q024 | How much of Microsoft's FY2023 total revenue came from service and other revenue versus product revenue? | factoid | table | ✓ | ✓ | ✓ |
| Q025 | What was Microsoft's net cash from operations for fiscal year 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q026 | How many Microsoft 365 Consumer subscribers did Microsoft have as of fiscal year 2023? | factoid | prose | ✓ | ✓ | ✓ |
| Q027 | What was Microsoft's provision for income taxes in fiscal year 2023? | factoid | table | ✓ | ✓ | ✓ |
| Q028 | How much transition tax under the TCJA did Microsoft still owe as of June 30, 2023? | factoid | prose | ✓ | ✓ | ✓ |
| Q029 | How much remained available under Microsoft's share repurchase programme as of June 30, 2023? | factoid | prose | ✓ | ✓ | ✓ |
| Q030 | What was the largest component of property and equipment by gross carrying amount? | superlative | table | ✓ | ✓ | ✓ |
| Q031 | What was the single largest product/service category by revenue in FY2023? | superlative | table | ✓ | ✓ | ✓ |
| Q032 | Which category of intangible assets had the highest net carrying amount as of June 30, 2023? | superlative | table | ✓ | ✓ | ✓ |
| Q033 | What was Microsoft's market capitalisation as of June 30, 2023? | negative | n/a | - | **✗** | ✓ |
| Q034 | What was Microsoft's revenue in China for fiscal year 2023? | negative | n/a | - | ✓ | ✓ |
| Q035 | What percentage of Microsoft's FY2023 revenue came from the United States? | cross_section | table+prose | **✗** | **✗** | ✓ |
| Q036 | What was the value of Microsoft's long-lived assets in Ireland as of June 30, 2023? | cross_section | table+prose | ✓ | ✓ | ✓ |
| Q037 | What was Microsoft's current ratio as of June 30, 2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q038 | What percentage of Microsoft's total FY2023 revenue came from service and other revenue? | multi_hop | table | ✓ | ✓ | ✓ |
| Q039 | What was Microsoft's total unearned revenue (current plus non-current) as of June 30, 2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q040 | What was the year-over-year increase in property and equipment (net) from FY2022 to FY2023? | multi_hop | table | ✓ | ✓ | ✓ |

### Summary — standard set

| Dimension | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Retrieval | 35 | 36 | 97% |
| Correctness | 35 | 40 | 88% |
| Faithfulness | 40 | 40 | 100% |

**Correctness by question type**

| Type | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Factoid | 18 | 18 | 100% |
| Multi-hop | 6 | 8 | 75% |
| Superlative | 5 | 6 | 83% |
| Cross-section | 3 | 4 | 75% |
| Negative | 3 | 4 | 75% |

**Correctness by source type**

| Source | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Prose | 8 | 8 | 100% |
| Table | 20 | 22 | 91% |
| Table + prose | 4 | 6 | 67% |
| N/A (negative Qs) | 3 | 4 | 75% |

---

## Adversarial question set

`eval_20260323_024422_topk10_adv.json` · 20 questions

| ID | Question | Type | Source | Ret | Corr | Faith |
|---|---|---|---|:---:|:---:|:---:|
| Q041 | What was Microsoft's net income margin for fiscal year 2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q042 | Which of the three fiscal years reported (2021, 2022, 2023) had the highest net income? | superlative | table | ✓ | ✓ | ✓ |
| Q043 | What was Microsoft's free cash flow for fiscal year 2023? | multi_hop | table | **✗** | **✗** | ✓ |
| Q044 | What was the year-over-year change in total long-term debt face value from FY2022 to FY2023? | multi_hop | table | ✓ | **✗** | ✓ |
| Q045 | What was Microsoft's dividend payout ratio for fiscal year 2023? | multi_hop | table | ✓ | **✗** | ✓ |
| Q046 | What was Microsoft's total operating expense ratio (R&D + Sales & Marketing + G&A) for FY2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q047 | What was Microsoft's debt-to-equity ratio as of June 30, 2023? | multi_hop | table | ✓ | ✓ | ✓ |
| Q048 | What was Microsoft's revenue per full-time employee for fiscal year 2023? | multi_hop | table+prose | ✓ | ✓ | ✓ |
| Q049 | Which segment had the highest operating income margin in fiscal year 2023? | superlative | table | ✓ | **✗** | ✓ |
| Q050 | In FY2023, Ireland generated 81% of Microsoft's foreign income — what was the total foreign income? | cross_section | table+prose | ✓ | ✓ | ✓ |
| Q051 | Which segment had the highest unearned revenue as of June 30, 2023, and what was the amount? | cross_section | table | ✓ | ✓ | ✓ |
| Q052 | How did stock-based compensation expense change from FY2022 to FY2023? | cross_section | table | ✓ | ✓ | ✓ |
| Q053 | Which intangible asset category had the largest accumulated amortisation as of June 30, 2023? | superlative | table | ✓ | ✓ | ✓ |
| Q054 | Which year in the debt maturity schedule (FY2024–FY2028) has the highest principal repayment? | superlative | table | ✓ | ✓ | ✓ |
| Q055 | Which product or service categories had lower revenue in FY2023 than in FY2022? | superlative | table | ✓ | **✗** | ✓ |
| Q056 | As of June 30, 2023, what were Microsoft's total operating lease liabilities? | cross_section | table | ✓ | ✓ | ✓ |
| Q057 | What was the total combined value of operating and finance leases that commenced in FY2023? | multi_hop | prose | ✓ | ✓ | ✓ |
| Q058 | What was the absolute dollar revenue from Xbox hardware and Xbox content & services individually? | negative | n/a | - | **✗** | ✓ |
| Q059 | What credit rating does Microsoft hold as of fiscal year 2023? | negative | n/a | - | ✓ | ✓ |
| Q060 | What was the largest functional employee category by headcount as of June 30, 2023? | cross_section | table+prose | **✗** | **✗** | ✓ |

### Summary — adversarial set

| Dimension | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Retrieval | 16 | 18 | 89% |
| Correctness | 13 | 20 | 65% |
| Faithfulness | 20 | 20 | 100% |

**Correctness by question type**

| Type | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Multi-hop | 5 | 8 | 62% |
| Superlative | 3 | 5 | 60% |
| Cross-section | 4 | 5 | 80% |
| Negative | 1 | 2 | 50% |

**Correctness by source type**

| Source | Passed | Total | Pass rate |
|---|---:|---:|---:|
| Prose | 1 | 1 | 100% |
| Table | 9 | 14 | 64% |
| Table + prose | 2 | 3 | 67% |
| N/A (negative Qs) | 1 | 2 | 50% |
