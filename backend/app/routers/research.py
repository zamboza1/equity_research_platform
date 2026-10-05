"""Local research files with immutable, calculated revisions and optimistic writes."""
from datetime import date, datetime, timezone
import hashlib
import html
import json
import math
import os
import re
from pathlib import Path
import sqlite3
from typing import Literal
from uuid import UUID
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.engine.dcf_engine import AdvancedDCFEngine, AdvancedDCFRequest

router = APIRouter()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class Financials(StrictModel):
    current_price: float = Field(gt=0)
    shares_outstanding_m: float = Field(gt=0)
    start_revenue_m: float = Field(gt=0)
    net_debt_m: float
    tax_rate: float = Field(ge=0, le=1)
    da_pct: float = Field(ge=0, le=1)
    capex_pct: float = Field(ge=0, le=1)
    nwc_pct: float = Field(ge=-1, le=1)
    minority_interest_m: float = Field(default=0, ge=0)
    preferred_equity_m: float = Field(default=0, ge=0)
    nonoperating_assets_m: float = Field(default=0, ge=0)


class Scenario(StrictModel):
    key: Literal["bear", "base", "bull"]
    probability: float = Field(ge=0, le=1)
    growth_rates: list[float] = Field(min_length=1, max_length=30)
    ebit_margins: list[float] = Field(min_length=1, max_length=30)
    wacc: float = Field(gt=0, le=1)
    terminal_growth: float = Field(gt=-1, le=.25)
    rationale: str = Field(default="", max_length=3000)


class Source(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    published_date: date | None = None
    supports: str = Field(default="", max_length=2000)


class Catalyst(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None
    status: Literal["watch", "upcoming", "occurred"] = "watch"


class ResearchDraft(StrictModel):
    company_name: str = Field(min_length=1, max_length=160)
    ticker: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9.^=_-]+$")
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    as_of: date
    review_date: date | None = None
    status: Literal["watching", "researching", "reviewed", "archived"] = "researching"
    data_origin: Literal["illustrative", "analyst"] = "illustrative"
    thesis: str = Field(default="", max_length=12000)
    risks: str = Field(default="", max_length=12000)
    invalidation: str = Field(default="", max_length=6000)
    decision_notes: str = Field(default="", max_length=6000)
    financials: Financials
    scenarios: list[Scenario] = Field(min_length=3, max_length=3)
    sources: list[Source] = Field(default_factory=list, max_length=40)
    catalysts: list[Catalyst] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def coherent_scenarios(self):
        if {s.key for s in self.scenarios} != {"bear", "base", "bull"}:
            raise ValueError("Use exactly one bear, base and bull scenario")
        if not math.isclose(sum(s.probability for s in self.scenarios), 1, abs_tol=1e-8):
            raise ValueError("Scenario probabilities must total 100%")
        for scenario in self.scenarios:
            assumptions(self, scenario)
        return self


def assumptions(draft: ResearchDraft, scenario: Scenario) -> AdvancedDCFRequest:
    return AdvancedDCFRequest(**draft.financials.model_dump(), ticker=draft.ticker,
        currency=draft.currency, growth_rates=scenario.growth_rates,
        ebit_margins=scenario.ebit_margins, years=len(scenario.growth_rates),
        wacc=scenario.wacc, terminal_growth=scenario.terminal_growth,
        nwc_treatment="balance_ratio", discount_timing="year_end", terminal_method="GORDON")


class CreateCase(StrictModel):
    request_id: UUID
    draft: ResearchDraft


class UpdateCase(StrictModel):
    expected_revision: int = Field(ge=1)
    draft: ResearchDraft
    change_note: str = Field(default="Updated research and assumptions", max_length=300)


@contextmanager
def connect():
    path = Path(os.getenv("VERTIGE_RESEARCH_DB", str(Path(__file__).resolve().parents[2] / "data" / "research.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS research_cases (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, current_revision INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS research_revisions (
            case_id TEXT NOT NULL REFERENCES research_cases(id), revision INTEGER NOT NULL,
            saved_at TEXT NOT NULL, change_note TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(case_id, revision)
        );
    """)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def serialize(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def calculate(draft: ResearchDraft):
    scenarios = {}
    for scenario in draft.scenarios:
        result = AdvancedDCFEngine(assumptions(draft, scenario)).calculate()
        scenarios[scenario.key] = {"probability": scenario.probability, "result": result.model_dump()}
    weighted = sum(item["probability"] * item["result"]["implied_price"] for item in scenarios.values())
    base = next(s for s in draft.scenarios if s.key == "base")
    base_assumptions = assumptions(draft, base)
    waccs = [base.wacc + delta for delta in [-.02, -.01, 0, .01, .02]]
    growths = [base.terminal_growth + delta for delta in [-.01, -.005, 0, .005, .01]]
    prices = []
    for growth in growths:
        row = []
        for wacc in waccs:
            try:
                request = AdvancedDCFRequest.model_validate(base_assumptions.model_dump() | {"wacc": wacc, "terminal_growth": growth})
                row.append(AdvancedDCFEngine(request).calculate().implied_price)
            except ValueError:
                row.append(None)
        prices.append(row)
    gaps = []
    if draft.data_origin == "illustrative": gaps.append("Illustrative financial inputs; replace them before using this case for company research.")
    if not draft.sources: gaps.append("No supporting sources recorded.")
    if not draft.thesis: gaps.append("Investment thesis is empty.")
    if not draft.risks: gaps.append("Risks are not documented.")
    if not draft.invalidation: gaps.append("No condition for revisiting the thesis is recorded.")
    if any(not s.rationale for s in draft.scenarios): gaps.append("At least one scenario has no rationale.")
    return {"scenarios": scenarios, "weighted_price": weighted,
        "weighted_upside": (weighted / draft.financials.current_price - 1) * 100,
        "sensitivity": {"wacc_values": waccs, "growth_values": growths, "prices": prices},
        "research_gaps": gaps, "calculation_version": "fcff-1.1",
        "description": "Analyst-weighted scenario values, not a statistical forecast or recommendation."}


def snapshot(draft):
    data = draft.model_dump(mode="json")
    evaluation = calculate(draft)
    result = {"draft": data, "evaluation": evaluation,
        "input_sha256": hashlib.sha256(serialize(data).encode()).hexdigest()}
    serialize(result)  # Reject numeric overflow before a write.
    return result


def read_revision(connection, case_id, revision=None):
    current = connection.execute("SELECT * FROM research_cases WHERE id=?", (str(case_id),)).fetchone()
    if not current: raise HTTPException(404, "Research case not found")
    number = current["current_revision"] if revision is None else revision
    row = connection.execute("SELECT * FROM research_revisions WHERE case_id=? AND revision=?", (str(case_id), number)).fetchone()
    if not row: raise HTTPException(404, "Research revision not found")
    return {"id": str(case_id), "revision": row["revision"], "current_revision": current["current_revision"],
        "created_at": current["created_at"], "saved_at": row["saved_at"], "change_note": row["change_note"],
        **json.loads(row["payload"])}


@router.get("/cases")
def list_cases():
    with connect() as connection:
        rows = connection.execute("SELECT c.id,c.current_revision,r.saved_at,r.payload FROM research_cases c JOIN research_revisions r ON c.id=r.case_id AND c.current_revision=r.revision ORDER BY r.saved_at DESC").fetchall()
    cases = []
    for row in rows:
        data = json.loads(row["payload"]); draft = data["draft"]; evaluation = data["evaluation"]
        cases.append({"id": row["id"], "revision": row["current_revision"], "saved_at": row["saved_at"],
            **{k: draft[k] for k in ["company_name", "ticker", "currency", "status", "as_of", "review_date", "data_origin"]},
            "current_price": draft["financials"]["current_price"], "weighted_price": evaluation["weighted_price"],
            "weighted_upside": evaluation["weighted_upside"], "source_count": len(draft["sources"]),
            "gap_count": len(evaluation["research_gaps"])})
    return cases


@router.post("/cases", status_code=201)
def create_case(body: CreateCase):
    payload = snapshot(body.draft)
    now = datetime.now(timezone.utc).isoformat()
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT id FROM research_cases WHERE id=?", (str(body.request_id),)).fetchone()
        if existing:
            first = read_revision(connection, body.request_id, 1)
            if first["input_sha256"] != payload["input_sha256"]:
                raise HTTPException(409, "This creation request was already used for different inputs")
            return read_revision(connection, body.request_id)
        connection.execute("INSERT INTO research_cases VALUES(?,?,1)", (str(body.request_id), now))
        connection.execute("INSERT INTO research_revisions VALUES(?,1,?,?,?)", (str(body.request_id), now, "Created research case", serialize(payload)))
        return read_revision(connection, body.request_id)


@router.get("/cases/{case_id}")
def get_case(case_id: UUID):
    with connect() as connection: return read_revision(connection, case_id)


@router.put("/cases/{case_id}")
def update_case(case_id: UUID, body: UpdateCase):
    payload = snapshot(body.draft)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        current = read_revision(connection, case_id)
        if current["revision"] != body.expected_revision:
            raise HTTPException(409, "A newer revision exists. Your draft is retained. Open the latest saved revision before merging your changes.")
        number = current["revision"] + 1
        now = datetime.now(timezone.utc).isoformat()
        connection.execute("INSERT INTO research_revisions VALUES(?,?,?,?,?)", (str(case_id), number, now, body.change_note, serialize(payload)))
        connection.execute("UPDATE research_cases SET current_revision=? WHERE id=?", (number, str(case_id)))
        return read_revision(connection, case_id)


@router.get("/cases/{case_id}/history")
def history(case_id: UUID):
    with connect() as connection:
        read_revision(connection, case_id)
        return [dict(row) for row in connection.execute("SELECT revision,saved_at,change_note FROM research_revisions WHERE case_id=? ORDER BY revision DESC", (str(case_id),))]


@router.get("/cases/{case_id}/revisions/{revision}")
def historical_case(case_id: UUID, revision: int):
    with connect() as connection: return read_revision(connection, case_id, revision)


@router.get("/cases/{case_id}/export")
def export_case(case_id: UUID, revision: int | None = None):
    with connect() as connection: result = read_revision(connection, case_id, revision)
    return JSONResponse({"format": "vertige-research", "version": 1, **result},
        headers={"Content-Disposition": f'attachment; filename="research-{case_id}-r{result["revision"]}.json"'})


def report_text(case):
    draft = case["draft"]; evaluation = case["evaluation"]
    def safe(text):
        return html.escape(str(text)).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
    lines = [f'# {safe(draft["company_name"])} ({safe(draft["ticker"])})',
        f'Revision {case["revision"]} · Reference date {draft["as_of"]} · {draft["currency"]}',
        f'Saved {case["saved_at"]}. Input SHA-256: {case["input_sha256"]}.',
        f'Data: {draft["data_origin"]}. Workflow status: {draft["status"]}; this is an analyst label, not verification.',
        '## Thesis', safe(draft['thesis']) or 'Not recorded.',
        '## Scenario valuation', 'All money and shares are in millions; share values are in currency per share.',
        '| Scenario | Weight | WACC | Terminal growth | Implied price | Upside |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for scenario in draft['scenarios']:
        result = evaluation['scenarios'][scenario['key']]['result']
        lines.append(f'| {scenario["key"].title()} | {scenario["probability"]:.1%} | {scenario["wacc"]:.1%} | {scenario["terminal_growth"]:.1%} | {result["implied_price"]:.2f} | {result["upside"]:.2f}% |')
    lines += [f'Weighted value: {evaluation["weighted_price"]:.2f}; reference market price: {draft["financials"]["current_price"]:.2f}.',
        evaluation['description'], '## Assumptions', 'Year-end FCFF; Gordon terminal value; operating NWC balance ratio; no immediate tax benefit on losses.']
    for key, value in draft['financials'].items(): lines.append(f'- {key}: {value}')
    for scenario in draft['scenarios']:
        lines += [f'### {scenario["key"].title()}', safe(scenario['rationale']) or 'Rationale not recorded.',
            'Annual growth: ' + ', '.join(f'{x:.2%}' for x in scenario['growth_rates']),
            'Annual EBIT margins: ' + ', '.join(f'{x:.2%}' for x in scenario['ebit_margins'])]
        for warning in evaluation['scenarios'][scenario['key']]['result']['warnings']: lines.append('- ' + warning)
    lines += ['## Catalysts'] + [f'- {safe(c["title"])} · {c["due_date"] or "Undated"} · {c["status"]}' for c in draft['catalysts']]
    lines += ['## Risks', safe(draft['risks']) or 'Not recorded.', '## What would change the thesis', safe(draft['invalidation']) or 'Not recorded.', '## Decision notes', safe(draft['decision_notes']) or 'Not recorded.', '## Sources']
    for source in draft['sources']:
        lines += [f'- {safe(source["title"])} · {source["published_date"] or "Date not recorded"}',
            f'  {safe(source["url"])}', '  Supports: ' + safe(source['supports'])]
    lines += ['## Research gaps'] + ['- ' + gap for gap in evaluation['research_gaps']]
    lines += ['## Limits', 'Source links are analyst-entered and are not fetched or verified by this report. Scenario weights are subjective. This local research tool is not an investment recommendation.']
    return re.sub(r'(?<=\|)\n\n(?=\|)', '\n', '\n\n'.join(lines)) + '\n'


@router.get("/cases/{case_id}/report")
def export_report(case_id: UUID, revision: int | None = None):
    with connect() as connection: case = read_revision(connection, case_id, revision)
    return Response(report_text(case), media_type="text/markdown", headers={
        "Content-Disposition": f'attachment; filename="research-{case_id}-r{case["revision"]}.md"'})
