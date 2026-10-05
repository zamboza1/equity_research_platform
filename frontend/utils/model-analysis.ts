export type Override = {id: string; value: number | null};
export type Scenario = {name: string; overrides: Override[]};
export type Distribution = {id: string; kind: 'normal' | 'uniform' | 'triangular'; params: Record<string, number | null>};
export type AnalysisPlan = {
  target: string; x: string; y: string; xValues: string; yValues: string;
  scenarios: Scenario[]; distributions: Distribution[]; iterations: number | null; seed: number | null;
};

export function distribution(id: string, value: number, kind: Distribution['kind']): Distribution {
  const spread = Math.abs(value) * .1 || .01;
  return {id, kind, params: kind === 'normal' ? {mean: value, std: spread} : kind === 'uniform'
    ? {low: value - spread, high: value + spread} : {low: value - spread, mode: value, high: value + spread}};
}

export function initialPlan(nodes: {id: string; type: string; value: number | null}[]): AnalysisPlan {
  const inputs = nodes.filter(node => node.type !== 'FORMULA');
  const axis = (value: number) => [value - (Math.abs(value) * .2 || .1), value, value + (Math.abs(value) * .2 || .1)].map(x => Number(x.toPrecision(6))).join(', ');
  return {target: nodes.at(-1)?.id || '', x: inputs[0]?.id || '', y: inputs[1]?.id || '',
    xValues: axis(inputs[0]?.value ?? 0), yValues: axis(inputs[1]?.value ?? 0),
    scenarios: ['Downside', 'Base', 'Upside'].map(name => ({name, overrides: []})),
    distributions: inputs.length ? [distribution(inputs[0].id, inputs[0].value ?? 0, 'normal')] : [], iterations: 1000, seed: 42};
}

export function readPlan(value: unknown): AnalysisPlan {
  if (!value || typeof value !== 'object') throw new Error('Invalid saved analysis settings.');
  const p = value as AnalysisPlan;
  const numeric = (n: unknown) => n === null || (typeof n === 'number' && Number.isFinite(n));
  if (![p.target, p.x, p.y, p.xValues, p.yValues].every(s => typeof s === 'string' && s.length <= 3000)
    || !numeric(p.iterations) || !numeric(p.seed) || !Array.isArray(p.scenarios) || p.scenarios.length > 8
    || !Array.isArray(p.distributions) || p.distributions.length > 200) throw new Error('Invalid saved analysis settings.');
  for (const s of p.scenarios) {
    if (!s || typeof s.name !== 'string' || s.name.length > 80 || !Array.isArray(s.overrides) || s.overrides.length > 200
      || s.overrides.some(o => !o || typeof o.id !== 'string' || !numeric(o.value))) throw new Error('Invalid saved scenario.');
  }
  for (const d of p.distributions) {
    if (!d || typeof d.id !== 'string' || !['normal', 'uniform', 'triangular'].includes(d.kind)
      || !d.params || typeof d.params !== 'object' || Object.keys(d.params).length > 3 || Object.values(d.params).some(v => !numeric(v))) throw new Error('Invalid saved distribution.');
  }
  return p;
}

export function parseAxis(text: string): number[] {
  const tokens = text.split(',').map(x => x.trim());
  const values = tokens.map(Number);
  if (!tokens.length || tokens.length > 30 || tokens.some(x => !x) || values.some(x => !Number.isFinite(x))) {
    throw new Error('Enter 1 to 30 finite numbers per axis, separated by commas.');
  }
  return values;
}
