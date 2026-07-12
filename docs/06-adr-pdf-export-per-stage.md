# ADR 06: PDF export is cumulative and stage-scoped ("download till here")

**Status:** Accepted
**Date:** Step 6 of the v2.0 rebuild

## Context
The product requirement is: every tab has a "Download PDF till here"
button, which should produce one PDF containing every report generated
so far, in pipeline order, up to and including the current tab — not
just the current tab's report in isolation.

## Decision
- `backend/state.py:STAGE_ORDER` defines the canonical pipeline order.
- `GET /session/{id}/pdf?upto={stage}` slices `STAGE_ORDER` up to and
  including `upto`, and includes whichever of those stages already have a
  generated report in `state.reports` (skipping any that haven't been
  run yet, rather than erroring).
- Rendering uses `markdown2` (Markdown → HTML) then `xhtml2pdf` (HTML →
  PDF) — both pure-Python, so no system dependency like a headless
  Chrome or `wkhtmltopdf` binary is required in the Docker image.
- The frontend's download button always requests `upto=<the current
  tab's stage key>`, matching the "till here" requirement literally.

## Consequences
- A user can download a partial project (e.g. just Data Health + EDA) at
  any point without needing to run every stage first.
- PDF generation is a pure function of `ProjectState` and a stage name —
  easy to unit test without a browser or LLM call involved.
- Styling is deliberately simple (one CSS block in `pdf/exporter.py`);
  see `13-roadmap.md` for richer PDF theming as a future improvement.
