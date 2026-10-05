from copy import deepcopy
from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def research_database(monkeypatch, tmp_path):
    monkeypatch.setenv("VERTIGE_RESEARCH_DB", str(tmp_path / "research.sqlite3"))


def draft():
    return {"company_name": "Synthetic research company", "ticker": "EXAMPLE", "currency": "USD",
        "as_of": "2026-10-05", "data_origin": "illustrative", "thesis": "A boundary-case study",
        "financials": {"current_price": 10, "shares_outstanding_m": 10, "start_revenue_m": 100,
            "net_debt_m": 20, "tax_rate": .25, "da_pct": .03, "capex_pct": .04, "nwc_pct": .12},
        "scenarios": [{"key": key, "probability": weight, "growth_rates": [.1], "ebit_margins": [.2],
            "wacc": wacc, "terminal_growth": .02, "rationale": "Explicit discount-rate scenario"}
            for key, weight, wacc in [("bear", .25, .12), ("base", .5, .1), ("bull", .25, .08)]]}


def create(value=None, request_id=None):
    return client.post('/api/research/cases', json={"request_id": str(request_id or uuid4()), "draft": value or draft()})


def test_research_independent_scenarios_and_sensitivity():
    response = create(); assert response.status_code == 201, response.text
    case = response.json(); evaluation = case['evaluation']
    expected = {}
    for key, wacc in [('bear', '.12'), ('base', '.10'), ('bull', '.08')]:
        w = Decimal(wacc)
        expected[key] = ((Decimal('14.2') + Decimal('15.444') / (w-Decimal('.02'))) / (1+w)-20)/10
        assert evaluation['scenarios'][key]['result']['implied_price'] == pytest.approx(float(expected[key]))
    weighted = expected['bear']/4 + expected['base']/2 + expected['bull']/4
    assert evaluation['weighted_price'] == pytest.approx(float(weighted))
    assert evaluation['sensitivity']['prices'][2][2] == pytest.approx(float(expected['base']))
    assert len(case['input_sha256']) == 64
    assert client.get('/api/research/cases').json()[0]['source_count'] == 0


def test_revision_history_conflict_and_exact_export():
    first = create().json(); changed = deepcopy(first['draft']); changed['thesis'] = 'Changed thesis'
    changed['financials']['net_debt_m'] = 30
    second = client.put(f'/api/research/cases/{first["id"]}', json={'expected_revision': 1, 'draft': changed, 'change_note': 'Debt updated'}).json()
    assert second['revision'] == 2
    assert second['evaluation']['weighted_price'] == pytest.approx(first['evaluation']['weighted_price'] - 1)
    stale = client.put(f'/api/research/cases/{first["id"]}', json={'expected_revision': 1, 'draft': draft()})
    assert stale.status_code == 409
    assert client.get(f'/api/research/cases/{first["id"]}').json()['draft']['thesis'] == 'Changed thesis'
    old = client.get(f'/api/research/cases/{first["id"]}/revisions/1').json()
    assert old['draft'] == first['draft'] and old['evaluation'] == first['evaluation']
    assert old['current_revision'] == 2
    history = client.get(f'/api/research/cases/{first["id"]}/history').json()
    assert [x['revision'] for x in history] == [2, 1]
    exported = client.get(f'/api/research/cases/{first["id"]}/export?revision=1')
    assert exported.json()['draft'] == first['draft']
    assert 'attachment;' in exported.headers['content-disposition']


def test_creation_retry_does_not_duplicate_or_overwrite():
    request_id = uuid4()
    first = create(request_id=request_id).json()
    assert create(request_id=request_id).json()['id'] == first['id']
    assert len(client.get('/api/research/cases').json()) == 1
    altered = draft(); altered['company_name'] = 'Different company'
    assert create(altered, request_id).status_code == 409


@pytest.mark.parametrize('mutation', ['weights', 'duplicate', 'bad_rate', 'invalid_url', 'currency', 'array_length'])
def test_invalid_research_never_persists(mutation):
    value = draft()
    if mutation == 'weights': value['scenarios'][0]['probability'] = .6
    if mutation == 'duplicate': value['scenarios'][0]['key'] = 'base'
    if mutation == 'bad_rate': value['scenarios'][0]['wacc'] = .02
    if mutation == 'invalid_url': value['sources'] = [{'title': 'Unsafe URL', 'url': 'javascript:alert(1)'}]
    if mutation == 'currency': value['currency'] = 'usd'
    if mutation == 'array_length': value['scenarios'][0]['ebit_margins'] = [.2, .3]
    assert create(value).status_code == 422
    assert client.get('/api/research/cases').json() == []


def test_report_provenance_and_archived_case_retention():
    value = draft(); value.update(status='archived', risks='Concentration', invalidation='Revenue contracts')
    value['sources'] = [{'title': '<script>bad</script>', 'url': 'https://example.com/filing', 'published_date': '2026-09-30', 'supports': 'Revenue baseline'}]
    case = create(value).json()
    report = client.get(f'/api/research/cases/{case["id"]}/report')
    assert report.status_code == 200
    assert '<script>' not in report.text
    assert 'https://example.com/filing' in report.text and 'Revenue baseline' in report.text
    assert case['input_sha256'] in report.text and 'Revision 1' in report.text
    assert 'archived' in report.text and 'not a statistical forecast' in report.text
    assert client.get('/api/research/cases').json()[0]['status'] == 'archived'


def test_missing_case_and_revision_are_not_synthetic():
    assert client.get(f'/api/research/cases/{uuid4()}').status_code == 404
    case = create().json()
    assert client.get(f'/api/research/cases/{case["id"]}/revisions/99').status_code == 404
