"""
backend/pdf/exporter.py
Renders the accumulated Markdown reports (up to and including a given
stage) into a single downloadable PDF. Uses markdown -> HTML -> PDF via
markdown2 + xhtml2pdf, both pure-Python and dependency-light (no system
package like wkhtmltopdf or a headless browser required).
"""
import html
import io

import markdown2
from xhtml2pdf import pisa

from backend.agents.prompts import STAGE_LABELS
from backend.state import ProjectState, STAGE_ORDER

CSS = """
<style>
  body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #222; }
  h1 { color: #1a1a1a; border-bottom: 2px solid #444; padding-bottom: 6px; }
  h2 { color: #2c3e50; margin-top: 28px; }
  h3 { color: #34495e; }
  .stage-title { background: #f0f2f5; padding: 8px 12px; border-left: 4px solid #4a6fa5; margin-top: 30px; }
  .cover { text-align: center; margin-top: 120px; }
  .cover h1 { border: none; font-size: 26pt; }
</style>
"""


def build_pdf(state: ProjectState, upto_stage: str) -> bytes:
    if upto_stage not in STAGE_ORDER:
        raise ValueError(f"Unknown stage: {upto_stage}")

    cutoff = STAGE_ORDER.index(upto_stage)
    stages_to_include = STAGE_ORDER[: cutoff + 1]

    safe_dataset_name = html.escape(state.dataset_name or "")
    sections_label = html.escape(
        ", ".join(STAGE_LABELS.get(s, s) for s in stages_to_include if s in state.reports)
    )

    html_parts = [
        CSS,
        f"""<div class="cover">
            <h1>ClusterMaster Report</h1>
            <p>{safe_dataset_name}</p>
            <p>Sections: {sections_label}</p>
        </div><div style="page-break-after: always;"></div>""",
    ]

    for stage in stages_to_include:
        report_md = state.reports.get(stage)
        if not report_md:
            continue
        label = html.escape(STAGE_LABELS.get(stage, stage))
        section_html = markdown2.markdown(report_md, extras=["tables", "fenced-code-blocks"])
        html_parts.append(f'<div class="stage-title"><h2>{label}</h2></div>{section_html}')

    full_html = "\n".join(html_parts)

    buffer = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(full_html), dest=buffer)
    if result.err:
        raise RuntimeError("PDF generation failed")
    return buffer.getvalue()
