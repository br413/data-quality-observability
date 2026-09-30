"""Portable reports: no server, JavaScript, or external assets required."""

from __future__ import annotations

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from .models import CheckStatus, RunSummary


def report_payload(summaries: list[RunSummary]) -> dict:
    """Version the export independently of the package and history schema."""
    runs = []
    for summary in summaries:
        run = asdict(summary)
        run.update(
            started_at=summary.started_at.isoformat(),
            finished_at=summary.finished_at.isoformat(),
            passed=summary.passed,
        )
        runs.append(run)
    return {"schema_version": 1, "runs": runs}


def render_html(summaries: list[RunSummary], *, title: str = "Data quality report") -> str:
    sections = []
    for index, summary in enumerate(summaries, start=1):
        counts = {status: sum(r.status == status for r in summary.results) for status in CheckStatus}
        status = "passed" if summary.passed else "failed"
        cards = []
        for result in summary.results:
            metadata = ""
            if result.metadata:
                metadata = (
                    '<details><summary>Inspect evidence</summary><pre>'
                    + escape(json.dumps(result.metadata, indent=2, ensure_ascii=False))
                    + "</pre></details>"
                )
            row_count = "unknown" if result.row_count is None else str(result.row_count)
            cards.append(
                f'<article class="check {result.status.value}"><div class="check-heading">'
                f'<h3>{escape(result.check_type.replace("_", " ").title())}</h3>'
                f'<span class="badge {result.status.value}">{result.status.value}</span></div>'
                f'<p>{escape(result.message)}</p><p class="meta">'
                f'{escape(result.severity.value)} severity &middot; {row_count} rows evaluated</p>'
                f'{metadata}</article>'
            )
        sections.append(
            f'<section aria-labelledby="run-{index}"><div class="run-heading"><div>'
            f'<p class="eyebrow">RUN {index:02d} &middot; CONTRACT v{escape(summary.contract_version)}</p>'
            f'<h2 id="run-{index}">{escape(summary.contract_name)}</h2></div>'
            f'<span class="badge {status}">{"No failed checks" if summary.passed else "Needs attention"}</span></div>'
            f'<div class="stats"><div><strong>{counts[CheckStatus.PASSED]}</strong> passed</div>'
            f'<div><strong>{counts[CheckStatus.FAILED]}</strong> failed</div>'
            f'<div><strong>{counts[CheckStatus.SKIPPED]}</strong> skipped</div></div>'
            f'<div class="checks">{"".join(cards)}</div>'
            f'<p class="meta">Started {escape(summary.started_at.isoformat())}'
            f'<br>Run ID: {escape(summary.run_id)}</p></section>'
        )
    safe_title = escape(title)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{safe_title}</title><style>
:root{{color-scheme:light;--ink:#172d36;--muted:#526570;--line:#d8e2e5}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7f7;color:var(--ink);font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:48px 24px}}header{{padding:0 0 28px;border-bottom:1px solid var(--line)}}
.eyebrow{{font-size:12px;letter-spacing:.12em;font-weight:700;color:#376b69;margin:0 0 8px}}
h1{{font-size:clamp(30px,5vw,48px);line-height:1.15;letter-spacing:-.04em;margin:0 0 16px}}
h2{{font-size:28px;margin:0}}h3{{font-size:17px;margin:0}}header p{{max-width:700px;color:var(--muted)}}
section{{margin-top:36px}}.run-heading,.check-heading{{display:flex;justify-content:space-between;align-items:center;gap:16px}}
.stats{{display:flex;gap:32px;margin:22px 0}}.stats strong{{font-size:28px;margin-right:6px}}
.checks{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
.check{{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;border-left:4px solid #30756b}}
.check.failed{{border-left-color:#b64b36}}.check.skipped{{border-left-color:#89969e}}
.check p{{margin:12px 0;overflow-wrap:anywhere}}.badge{{white-space:nowrap;font-size:12px;font-weight:700;padding:5px 10px;border-radius:20px}}
.badge.passed{{background:#def2e9;color:#165d45}}.badge.failed{{background:#fbe5de;color:#8d3524}}
.badge.skipped{{background:#edf0f2;color:#46555e}}.meta{{font-size:12px;color:var(--muted);overflow-wrap:anywhere}}
details{{font-size:13px}}summary{{cursor:pointer;color:#245f5b}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7f7;padding:14px}}
footer{{margin-top:40px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
@media(max-width:640px){{main{{padding:28px 16px}}.checks{{grid-template-columns:1fr}}.run-heading{{align-items:flex-start;flex-wrap:wrap}}.stats{{gap:18px}}}}
@media print{{body{{background:white}}main{{padding:0}}.check{{break-inside:avoid}}details{{display:block}}}}
</style></head><body><main><header><p class="eyebrow">DQO / DATA QUALITY OBSERVABILITY</p>
<h1>{safe_title}</h1><p>Inspect the findings. Fix the source. Run the checks again.
This report is self-contained and works offline.</p></header>
{"".join(sections)}<footer>Generated by DQO &middot; Counts refer to checks, not distinct failing rows.
Skipped checks are not a pass. Reports may contain sample identifiers; review before sharing.</footer></main></body></html>'''


def write_report(path: Path, summaries: list[RunSummary], *, title: str = "Data quality report") -> None:
    """Select format explicitly from a supported filename extension."""
    if path.suffix.lower() not in {".html", ".json"}:
        raise ValueError("report path must end in .html or .json")
    content = (
        json.dumps(report_payload(summaries), indent=2, ensure_ascii=False) + "\n"
        if path.suffix.lower() == ".json" else render_html(summaries, title=title)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
