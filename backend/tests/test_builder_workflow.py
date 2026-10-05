import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_formula_dependencies_work_before_inputs_without_drawing_edges():
    graph = {'nodes': [
        {'id': 'profit', 'label': 'Profit', 'type': 'FORMULA', 'formula': '{revenue} * {margin}'},
        {'id': 'revenue', 'label': 'Revenue', 'type': 'FORMULA', 'formula': '{opening} * 1.1'},
        {'id': 'opening', 'label': 'Opening revenue', 'type': 'INPUT', 'value': 100},
        {'id': 'margin', 'label': 'Margin', 'type': 'CONSTANT', 'value': .25}], 'edges': []}
    response = client.post('/api/builder/solve', json=graph)
    assert response.status_code == 200
    assert response.json()['results']['profit'] == pytest.approx(27.5)
    graph['nodes'].reverse()
    assert client.post('/api/builder/solve', json=graph).json()['results']['profit'] == pytest.approx(27.5)


@pytest.mark.parametrize('formula, message', [
    ('1 +', 'Invalid formula syntax'), ('{missing} + 1', 'unknown input missing'),
    ('{result} + 1', 'Circular reference'), ('1 / 0', 'Invalid numeric formula')])
def test_invalid_formula_is_a_readable_client_error(formula, message):
    response = client.post('/api/builder/solve', json={'nodes': [
        {'id': 'result', 'label': 'Result', 'type': 'FORMULA', 'formula': formula}], 'edges': []})
    assert response.status_code == 400
    assert message in response.json()['detail']


def test_blank_input_is_not_silently_zero():
    graph = {'nodes': [{'id': 'x', 'label': 'X', 'type': 'INPUT', 'value': None}], 'edges': []}
    assert client.post('/api/builder/solve', json=graph).status_code == 400
    graph['nodes'][0]['value'] = 0
    assert client.post('/api/builder/solve', json=graph).json()['results']['x'] == 0


@pytest.mark.parametrize('formula, expected', [
    ('round(sum([1.111, 2.222]), 2)', 3.33),
    ('max(2, min(4, 3)) + sqrt(16)', 7),
    ('pow(2, 3) + 2 ** 4', 24)])
def test_documented_numeric_functions(formula, expected):
    response = client.post('/api/builder/solve', json={'nodes': [
        {'id': 'result', 'label': 'Result', 'type': 'FORMULA', 'formula': formula}], 'edges': []})
    assert response.status_code == 200
    assert response.json()['results']['result'] == pytest.approx(expected)


@pytest.mark.parametrize('formula', ['[1] * 1000000000', '((999 ** 16) ** 16) ** 16', 'round(1, 1.5)'])
def test_unbounded_or_invalid_numeric_operations_are_rejected(formula):
    response = client.post('/api/builder/solve', json={'nodes': [
        {'id': 'result', 'label': 'Result', 'type': 'FORMULA', 'formula': formula}], 'edges': []})
    assert response.status_code == 400
