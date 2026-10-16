# Backend QA fix report — F6 / F8

2026-10-16. User decisions in `qa-findings-1.md` override plan ledger R2.

- F6: `generate_card` preserves uncited LLM state/emotion/barrier text for dims situations. `grade_card` assigns `speculated`; grading logic is unchanged. `test_dims_situation_uncited_keeps_text_as_speculated` covers all three fields, and `test_dims_situation_keeps_cited_llm_text` remains.
- F8: The prompt requires copying tagged evidence pain_point sentences exactly, selecting one representative among similar tags, writing original text only without tagged pain_point, and always citing. The prompt-file assertion covers these instructions. The fake backend copies tag text; the saved JSON fixture agrees. R4 verified-tag and normalized-match rules remain unchanged.
- Strengthened the fake-backend regression with two distinct tag sentences and assertions for exact text, source_pain, citation, and observed grading at Context and aggregate levels. Existing R4 tests pass.

## Actual validation in this run

The requested implementation, tests, and an earlier report were already present when this run began. This run strengthened the regression and independently reran validation. RED below is an explicitly reconstructed pre-fix behavior check, not a claim that the starting workspace failed.

- RED — `backend/.venv/bin/python -m pytest backend/tests/persona/test_cards.py -q`: pytest exit 1; **7 failed, 40 passed, 1 warning in 1.91s**. Temporarily reinstated the dims fallback, removed the exact-copy prompt instructions, and replaced fake tag copying with fixed text. Failures covered three dims fields, prompt instructions, and two fake-copy cases. The seventh failure was the no-evidence test because this temporary fallback also affected evidence-free contexts. All temporary implementation changes were restored in a `finally` block before GREEN.
- GREEN — `backend/.venv/bin/python -m pytest backend/tests/persona/test_cards.py -q`: exit 0; **47 passed, 1 warning in 1.61s**. Includes the cited dims regression and existing R4 observed/rewritten/unverified tests.
- Full suite — `backend/.venv/bin/python -m pytest backend/tests -q -n 6`: exit 0; **2779 passed, 13 warnings in 146.93s**. Warnings concern Pydantic class-based config deprecation and joblib physical-core detection.

Edits were restricted to authorized files. No frontend edits or git writes.
