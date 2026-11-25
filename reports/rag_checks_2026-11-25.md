# Study retrieval checks — 2026-11-25

## Automated checks

Ran `tests.test_study_retrieval`, `tests.test_study_answer`, `tests.test_study_server`, and the main-interface study UI test. They cover text and text-based PDF ingestion with page numbers, keyword retrieval, literal percentage suggestions, no extraction across page boundaries, upload limits, duplicate detection, clearing, local HTTP origin checks, citation-number formatting, unavailable/no-context paths, and explicit application of values. The server and model-answer tests use a temporary index and, where needed, mocked model responses. No uploaded user studies were modified.

## Live local model smoke checks

Used the installed `llama3:latest` model through Ollama with an isolated in-memory index. A synthetic test sample stated PLA2 24.5% and SVMP 10%. The model returned 24.5% with a valid-looking citation when asked about PLA2, and correctly said that habitat was not stated when asked about habitat. These two examples are not a general accuracy evaluation.

Also uploaded the existing 47-page text PDF `data/raw/african_venoms_2022/supplementary/giac121_giga-d-22-00205_original_submission.pdf` into a fresh in-memory index. For a question about African snake venom composition, the first retrieved passage was from page 14 and discussed the measured proteomes, while three other top passages were bibliography material. The local model cited page 14, but described the evidence as not directly reporting composition even though the retrieved passage describes the proteomic analysis. The citation syntax passed but the answer was misleading/incomplete. Verify claims against the cited passages; a valid citation number does not check factual support.

Retrieval is keyword-based, not semantic vector search. Extracted PDF reading order and tables can be unreliable, scanned PDFs require OCR, and only explicit reviewed percentage suggestions may be applied. These checks do not establish accuracy on arbitrary papers or resistance to every prompt-injection attempt.
