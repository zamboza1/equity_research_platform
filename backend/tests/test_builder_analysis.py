from decimal import Decimal
import copy
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def graph():
    return {'nodes': [
        {'id': 'revenue', 'label': 'Revenue', 'type': 'INPUT', 'value': 100},
        {'id': 'margin', 'label': 'Margin', 'type': 'INPUT', 'value': .2},
        {'id': 'profit', 'label': 'Profit', 'type': 'FORMULA', 'formula': '{revenue} * {margin}'}], 'edges': []}


def test_multi_year_cash_flow_independent_reference():
    model = client.get('/api/builder/templates/cash_flow?years=5').json()
    response = client.post('/api/builder/solve', json=model)
    assert response.status_code == 200, response.text
    result = response.json()['results']
    revenue = Decimal('100')
    present_value = Decimal(0)
    for year in range(1, 6):
        prior = revenue
        revenue *= Decimal('1.1')
        cash_flow = revenue * Decimal('.2') * Decimal('.75') + revenue * Decimal('-.01') - (revenue - prior) * Decimal('.12')
        present_value += cash_flow / Decimal('1.1') ** year
        assert result[f'fcff_{year}'] == pytest.approx(float(cash_flow))
    assert result['forecast_value'] == pytest.approx(float(present_value))
    assert result['fcff_1'] == pytest.approx(14.2)
    assert 'terminal value' in model['notes']


def test_cash_flow_losses_receive_no_tax_credit_and_year_limits():
    model = client.get('/api/builder/templates/cash_flow?years=1').json()
    next(n for n in model['nodes'] if n['id'] == 'margin_1')['value'] = -.2
    result = client.post('/api/builder/solve', json=model).json()['results']
    assert result['nopat_1'] == pytest.approx(-22)
    for years in [0, 11]:
        assert client.get(f'/api/builder/templates/cash_flow?years={years}').status_code == 422


def test_scenario_comparison_preserves_base_and_overrides_only_inputs():
    model = graph(); original = copy.deepcopy(model)
    request = {'graph': model, 'target_variable': 'profit', 'scenarios': [
        {'name': 'Downside', 'overrides': {'revenue': 80}},
        {'name': 'Base', 'overrides': {}},
        {'name': 'Upside', 'overrides': {'revenue': 120, 'margin': .25}}]}
    response = client.post('/api/builder/scenarios', json=request)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['baseline'] == 20
    assert [r['value'] for r in result['scenarios']] == [16, 20, 30]
    assert [r['change'] for r in result['scenarios']] == [-4, 0, 10]
    assert model == original
    request['scenarios'][0]['overrides'] = {'profit': 99}
    assert client.post('/api/builder/scenarios', json=request).status_code == 422


def test_scenario_names_and_invalid_models_are_rejected():
    body = {'graph': graph(), 'target_variable': 'profit', 'scenarios': [{'name': 'Same'}, {'name': 'Same'}]}
    assert client.post('/api/builder/scenarios', json=body).status_code == 422
    body['scenarios'] = [{'name': ' ' }]
    assert client.post('/api/builder/scenarios', json=body).status_code == 422
    body['scenarios'] = [{'name': 'Base'}]; body['target_variable'] = 'missing'
    assert client.post('/api/builder/scenarios', json=body).status_code == 422


def test_two_way_sensitivity_matches_independent_products():
    response = client.post('/api/builder/sensitivity', json={'graph_data': graph(), 'config': {
        'x_variable': 'revenue', 'x_values': [80, 100], 'y_variable': 'margin', 'y_values': [.2, .3], 'target_variable': 'profit'}})
    assert response.status_code == 200, response.text
    assert response.json()['results_matrix'] == [[16, 20], [24, 30]]


def test_seeded_simulation_is_reproducible_and_counts_all_draws():
    body = {'graph_data': graph(), 'distributions': [{'node_id': 'revenue', 'distribution': 'uniform', 'params': {'low': 80, 'high': 120}}]}
    path = '/api/builder/simulate?target_variable=profit&iterations=100&seed=7'
    first = client.post(path, json=body)
    assert first.status_code == 200, first.text
    result = first.json()
    assert result == client.post(path, json=body).json()
    assert result['seed'] == 7 and result['iterations'] == 100
    assert sum(result['histogram']['counts']) == 100
    assert 16 <= result['percentile_5'] < result['median'] < result['percentile_95'] <= 24
    assert result != client.post(path.replace('seed=7', 'seed=8'), json=body).json()


@pytest.mark.parametrize('distribution, params', [
    ('normal', {'mean': 100, 'std': -1}), ('uniform', {'low': 100, 'high': 90}),
    ('triangular', {'low': 90, 'mode': 200, 'high': 110}), ('unknown', {}), ('normal', {'mean': 100})])
def test_distribution_parameters_are_validated(distribution, params):
    response = client.post('/api/builder/simulate?target_variable=profit&iterations=10', json={
        'graph_data': graph(), 'distributions': [{'node_id': 'revenue', 'distribution': distribution, 'params': params}]})
    assert response.status_code == 422


def test_zero_dispersion_is_valid_and_bad_draw_aborts():
    body = {'graph_data': graph(), 'distributions': [{'node_id': 'revenue', 'distribution': 'normal', 'params': {'mean': 100, 'std': 0}}]}
    path = '/api/builder/simulate?target_variable=profit&iterations=10'
    response = client.post(path, json=body)
    assert response.status_code == 200
    assert response.json()['mean'] == 20 and response.json()['std'] == 0
    body['graph_data']['nodes'][-1]['formula'] = '1 / ({revenue} - 100)'
    response = client.post(path, json=body)
    assert response.status_code == 422 and 'Invalid numeric formula' in response.text
