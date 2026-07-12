# 11. Testing Strategy

## What's tested
`tests/test_pipeline.py` covers the deterministic backbone of the system:
stage sequencing, prerequisite enforcement, and state accumulation
(`ProjectState.reports` / `.project_memory` growing correctly stage by
stage). It does this **without** calling Groq or Tavily — `call_groq` is
mocked (`unittest.mock.patch`), so the tests run offline, free, and fast,
and don't depend on API quota.

What's exercised end-to-end this way:
- Each `run_*` function in `backend/pipeline.py` produces a report and
  updates `state.reports` / `state.project_memory`.
- Stage prerequisites are enforced (`run_eda` before `run_data_health`
  raises `StageError`; same pattern applies to clustering-dependent
  stages).
- A full 9-stage run produces all 9 reports and all 9 memory entries.

## What's intentionally not covered by automated tests (v1)
- **Prompt quality / LLM output content** — inherently non-deterministic;
  reviewed manually during development, not asserted on in CI.
- **Tavily search result relevance** — same reasoning; the Domain
  Specialist's query-generation and synthesis logic is tested with the
  network call mocked, not its real-world output quality.
- **PDF visual rendering** — `build_pdf()` is exercised for "does it
  produce PDF bytes given N stages," not for pixel-level layout.
- **Streamlit frontend** — the frontend has no business logic to unit
  test (see ADR 01); it is checked manually / via a smoke run against a
  live backend before releases.

## How to run
```bash
cd clustermaster
pip install -r backend/requirements.txt
pip install pytest
pytest tests/ -v
```

## Adding new tests
Any new `run_*` pipeline function should get: (1) a happy-path test with
`call_groq` mocked, (2) a prerequisite-violation test if it depends on an
earlier stage's state. Follow the pattern in `test_pipeline.py`.
