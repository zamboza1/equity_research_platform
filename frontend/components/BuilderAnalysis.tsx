'use client';

import {useEffect, useMemo, useRef, useState} from 'react';
import {Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import api, {errorMessage} from '@/utils/api';
import {Graph, inputError, payload} from '@/utils/graph';
import {AnalysisPlan, distribution, Distribution, initialPlan, parseAxis} from '@/utils/model-analysis';
import {buttonClass, fieldClass, primaryClass} from '@/utils/research';

type Mode = 'scenarios' | 'sensitivity' | 'simulation';
type ScenarioResult = {target_variable: string; baseline: number; scenarios: {name: string; value: number; change: number; overrides: Record<string, number>; results: Record<string, number>}[]};
type SensitivityResult = {x_values: number[]; y_values: number[]; results_matrix: number[][]};
type SimulationResult = {mean: number; median: number; std: number; percentile_5: number; percentile_95: number; seed: number; iterations: number; histogram: {bins: number[]; counts: number[]}};
type Output = {mode: 'scenarios'; data: ScenarioResult} | {mode: 'sensitivity'; data: SensitivityResult} | {mode: 'simulation'; data: SimulationResult};
const format = (n: number) => new Intl.NumberFormat('en-US', {maximumFractionDigits: 6}).format(n);
const numeric = (value: string) => value === '' ? null : Number(value);

function downloadCSV(rows: (string | number)[][]) {
  const text = rows.map(row => row.map(value => {
    if (typeof value === 'number') return String(value);
    const safe = /^[=+\-@\t\r]/.test(value) ? "'" + value : value;
    return '"' + safe.replaceAll('"', '""') + '"';
  }).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = 'vertige-model-analysis.csv'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function BuilderAnalysis({graph, onChange, onBusyChange, disabled}: {
  graph: Graph; onChange: (plan: AnalysisPlan) => void; onBusyChange: (busy: boolean) => void; disabled: boolean;
}) {
  const plan = useMemo(() => graph.analysis || initialPlan(graph.nodes), [graph.analysis, graph.nodes]);
  const inputs = graph.nodes.filter(node => node.type !== 'FORMULA');
  const [mode, setMode] = useState<Mode>('scenarios');
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [output, setOutput] = useState<Output | null>(null);
  const request = useRef(0);
  useEffect(() => {request.current++; setOutput(null); setError('');}, [graph]);
  const change = (patch: Partial<AnalysisPlan>) => onChange({...plan, ...patch});
  const label = (id: string) => graph.nodes.find(node => node.id === id)?.label || id;
  const options = inputs.map(node => <option key={node.id} value={node.id}>{node.label} · {node.id}</option>);

  async function run() {
    setOutput(null); setError('');
    const sequence = ++request.current;
    try {
      const invalid = inputError(graph); if (invalid) throw new Error(invalid);
      if (!graph.nodes.some(node => node.id === plan.target)) throw new Error('Choose an existing target variable.');
      setBusy(true); onBusyChange(true);
      if (mode === 'scenarios') {
        const scenarios = plan.scenarios.map(scenario => {
          const seen = new Set<string>();
          for (const override of scenario.overrides) {
            if (!inputs.some(node => node.id === override.id) || override.value === null || !Number.isFinite(override.value)) throw new Error(`${scenario.name}: choose an input and enter a finite value.`);
            if (seen.has(override.id)) throw new Error(`${scenario.name}: an input can only be overridden once.`);
            seen.add(override.id);
          }
          return {name: scenario.name, overrides: Object.fromEntries(scenario.overrides.map(o => [o.id, o.value]))};
        });
        const {data} = await api.post('/builder/scenarios', {graph: payload(graph), target_variable: plan.target, scenarios});
        if (sequence === request.current) setOutput({mode, data});
      } else if (mode === 'sensitivity') {
        const config = {target_variable: plan.target, x_variable: plan.x, y_variable: plan.y, x_values: parseAxis(plan.xValues), y_values: parseAxis(plan.yValues)};
        const {data} = await api.post('/builder/sensitivity', {graph_data: payload(graph), config});
        if (sequence === request.current) setOutput({mode, data});
      } else {
        if (!Number.isInteger(plan.iterations) || plan.iterations === null || plan.iterations < 10 || plan.iterations > 10000) throw new Error('Iterations must be a whole number from 10 to 10,000.');
        if (!Number.isInteger(plan.seed) || plan.seed === null || plan.seed < 0 || plan.seed > 4294967295) throw new Error('Enter a whole-number seed from 0 to 4294967295.');
        if (plan.distributions.some(d => Object.values(d.params).some(value => value === null || !Number.isFinite(value)))) throw new Error('Enter every distribution parameter; blank values are not zero.');
        const distributions = plan.distributions.map(d => ({node_id: d.id, distribution: d.kind, params: d.params}));
        const {data} = await api.post('/builder/simulate', {graph_data: payload(graph), distributions}, {params: {target_variable: plan.target, iterations: plan.iterations, seed: plan.seed}});
        if (sequence === request.current) setOutput({mode, data});
      }
    } catch (e) {if (sequence === request.current) setError(errorMessage(e));}
    finally {setBusy(false); onBusyChange(false);}
  }

  function exportOutput() {
    if (!output) return;
    const rows: (string | number)[][] = [['Model', graph.name], ['Target', label(plan.target)], ['Target ID', plan.target], ['Analysis', output.mode], [], ['Baseline inputs', 'ID', 'Value']];
    inputs.forEach(node => rows.push([node.label, node.id, node.value ?? 'Missing']));
    rows.push([]);
    if (output.mode === 'scenarios') {
      rows.push(['Baseline target', output.data.baseline], ['Scenario', 'Value', 'Change from baseline']);
      output.data.scenarios.forEach(s => rows.push([s.name, s.value, s.change]));
      rows.push([], ['Scenario', 'Override ID', 'Value']);
      output.data.scenarios.forEach(s => Object.entries(s.overrides).forEach(([id, value]) => rows.push([s.name, id, value])));
    } else if (output.mode === 'sensitivity') {
      rows.push(['Rows: ' + label(plan.y) + '; columns: ' + label(plan.x), ...output.data.x_values]);
      output.data.results_matrix.forEach((row, i) => rows.push([output.data.y_values[i], ...row]));
    } else {
      const result = output.data;
      rows.push(['Seed', result.seed], ['Iterations', result.iterations], ['Mean', result.mean], ['Median', result.median], ['Standard deviation', result.std], ['P5', result.percentile_5], ['P95', result.percentile_95], [], ['Input ID', 'Distribution', 'Parameter', 'Value']);
      plan.distributions.forEach(d => Object.entries(d.params).forEach(([key, value]) => rows.push([d.id, d.kind, key, value ?? 'Missing'])));
      rows.push([], ['Lower bin edge', 'Upper bin edge', 'Count']);
      result.histogram.counts.forEach((count, i) => rows.push([result.histogram.bins[i], result.histogram.bins[i+1], count]));
    }
    rows.push([], ['Variable', 'Formula']); graph.nodes.filter(n => n.type === 'FORMULA').forEach(n => rows.push([n.id, n.formula]));
    downloadCSV(rows);
  }

  return <section className="min-w-0 space-y-5 border-t border-slate-300 pt-8">
    <div><h2 className="text-2xl font-semibold">Explore the model</h2><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Compare changes without overwriting the working model. Scenario definitions, sensitivity ranges and simulation settings are included when you save or export the graph. Results are recalculated from the current inputs.</p></div>
    <fieldset disabled={busy || disabled} className="min-w-0 space-y-5">
      <div className="flex flex-wrap gap-2">{([['scenarios', 'Scenario comparison'], ['sensitivity', 'Two-way sensitivity'], ['simulation', 'Simulation']] as const).map(([key, title]) => <button key={key} className={mode === key ? primaryClass : buttonClass} aria-pressed={mode === key} onClick={() => {setMode(key); setOutput(null); setError('');}}>{title}</button>)}</div>
      <label className="block max-w-lg text-xs font-medium">Analysis target<select className={fieldClass} value={plan.target} onChange={e => change({target: e.target.value})}><option value="">Choose a variable</option>{graph.nodes.map(node => <option value={node.id} key={node.id}>{node.label} · {node.id}</option>)}</select></label>

      {mode === 'scenarios' && <div className="space-y-5">
        <p className="text-sm text-slate-600">Each scenario starts from the current inputs and changes only the overrides you enter. Empty scenarios equal the baseline. Names describe your assumptions, not estimated probabilities.</p>
        {plan.scenarios.map((scenario, index) => <section key={index} className="space-y-3 border-y border-slate-200 py-4">
          <div className="flex flex-wrap items-end gap-3"><label className="min-w-48 flex-1 text-xs font-medium">Scenario {index + 1} name<input className={fieldClass} maxLength={80} value={scenario.name} onChange={e => change({scenarios: plan.scenarios.map((s, i) => i === index ? {...s, name: e.target.value} : s)})}/></label><button className={buttonClass} onClick={() => change({scenarios: plan.scenarios.filter((_, i) => i !== index)})}>Remove scenario {index + 1}</button></div>
          {scenario.overrides.map((override, row) => <div key={row} className="grid items-end gap-3 sm:grid-cols-[1fr_160px_auto]">
            <label className="min-w-0 text-xs font-medium">Scenario {index + 1} input {row + 1}<select className={fieldClass} value={override.id} onChange={e => change({scenarios: plan.scenarios.map((s, i) => i === index ? {...s, overrides: s.overrides.map((o, j) => j === row ? {id: e.target.value, value: inputs.find(n => n.id === e.target.value)?.value ?? null} : o)} : s)})}>{options}</select></label>
            <label className="text-xs font-medium">Scenario {index + 1} value {row + 1}<input type="number" step="any" className={fieldClass} value={override.value ?? ''} onChange={e => change({scenarios: plan.scenarios.map((s, i) => i === index ? {...s, overrides: s.overrides.map((o, j) => j === row ? {...o, value: numeric(e.target.value)} : o)} : s)})}/></label>
            <button className={buttonClass} onClick={() => change({scenarios: plan.scenarios.map((s, i) => i === index ? {...s, overrides: s.overrides.filter((_, j) => j !== row)} : s)})}>Remove override {index + 1}.{row + 1}</button>
          </div>)}
          <button className={buttonClass} disabled={!inputs.some(node => !scenario.overrides.some(o => o.id === node.id))} onClick={() => {const node = inputs.find(n => !scenario.overrides.some(o => o.id === n.id)); if (node) change({scenarios: plan.scenarios.map((s, i) => i === index ? {...s, overrides: [...s.overrides, {id: node.id, value: node.value}]} : s)});}}>Add override to scenario {index + 1}</button>
        </section>)}
        <button className={buttonClass} disabled={plan.scenarios.length >= 8} onClick={() => change({scenarios: [...plan.scenarios, {name: `Scenario ${plan.scenarios.length + 1}`, overrides: []}]})}>Add scenario</button>
      </div>}

      {mode === 'sensitivity' && <div className="grid gap-4 sm:grid-cols-2">
        <label className="min-w-0 text-xs font-medium">Column input<select className={fieldClass} value={plan.x} onChange={e => change({x: e.target.value})}><option value="">Choose input</option>{options}</select></label>
        <label className="min-w-0 text-xs font-medium">Row input<select className={fieldClass} value={plan.y} onChange={e => change({y: e.target.value})}><option value="">Choose input</option>{options}</select></label>
        <label className="text-xs font-medium">Column values<input className={fieldClass} value={plan.xValues} onChange={e => change({xValues: e.target.value})}/></label>
        <label className="text-xs font-medium">Row values<input className={fieldClass} value={plan.yValues} onChange={e => change({yValues: e.target.value})}/></label>
        <p className="text-sm text-slate-600 sm:col-span-2">Use comma-separated values in the input's units, with rates as decimals. Up to 30 values per axis. Each cell changes both inputs together. An invalid cell stops the run and reports the formula error.</p>
      </div>}

      {mode === 'simulation' && <div className="space-y-5">
        <p className="text-sm leading-6 text-slate-600">Inputs are sampled independently; correlations and economic constraints are not inferred. Defaults are illustrative. A failed draw stops the run, with no partial summary. Percentiles describe these assumptions, not a statistical forecast or confidence interval.</p>
        <div className="grid gap-4 sm:grid-cols-2"><label className="text-xs font-medium">Simulation iterations<input type="number" min={10} max={Math.min(10000, Math.floor(200000 / Math.max(1, graph.nodes.length)))} className={fieldClass} value={plan.iterations ?? ''} onChange={e => change({iterations: numeric(e.target.value)})}/></label><label className="text-xs font-medium">Simulation seed<input type="number" min={0} max={4294967295} className={fieldClass} value={plan.seed ?? ''} onChange={e => change({seed: numeric(e.target.value)})}/></label></div>
        {plan.distributions.map((d, index) => <section key={index} className="grid items-end gap-3 border-y border-slate-200 py-4 sm:grid-cols-2">
          <label className="min-w-0 text-xs font-medium">Simulation input {index + 1}<select className={fieldClass} value={d.id} onChange={e => change({distributions: plan.distributions.map((item, i) => i === index ? distribution(e.target.value, inputs.find(n => n.id === e.target.value)?.value ?? 0, item.kind) : item)})}>{options}</select></label>
          <label className="text-xs font-medium">Distribution {index + 1}<select className={fieldClass} value={d.kind} onChange={e => change({distributions: plan.distributions.map((item, i) => i === index ? distribution(item.id, inputs.find(n => n.id === item.id)?.value ?? 0, e.target.value as Distribution['kind']) : item)})}><option value="normal">Normal</option><option value="uniform">Uniform</option><option value="triangular">Triangular</option></select></label>
          {Object.entries(d.params).map(([key, value]) => <label className="text-xs font-medium" key={key}>Distribution {index + 1} {key}<input className={fieldClass} type="number" step="any" value={value ?? ''} onChange={e => change({distributions: plan.distributions.map((item, i) => i === index ? {...item, params: {...item.params, [key]: numeric(e.target.value)}} : item)})}/></label>)}
          <button className={buttonClass} onClick={() => change({distributions: plan.distributions.filter((_, i) => i !== index)})}>Remove distribution {index + 1}</button>
        </section>)}
        <button className={buttonClass} disabled={!inputs.some(n => !plan.distributions.some(d => d.id === n.id))} onClick={() => {const node = inputs.find(n => !plan.distributions.some(d => d.id === n.id)); if (node) change({distributions: [...plan.distributions, distribution(node.id, node.value ?? 0, 'normal')]});}}>Add input distribution</button>
      </div>}
      <button className={primaryClass} disabled={!graph.nodes.length || !inputs.length} onClick={run}>{busy ? 'Running analysis…' : 'Run analysis'}</button>
    </fieldset>
    {error && <p role="alert" className="border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</p>}
    {output && <section className="min-w-0 space-y-5 border-t border-slate-300 pt-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-lg font-semibold">{label(plan.target)} · analysis results</h3><button className={buttonClass} onClick={exportOutput}>Download analysis CSV</button></div>
      <p role="status" className="text-xs text-slate-600">Results match the current model and analysis settings.</p>
      {output.mode === 'scenarios' && <>
        <p className="text-sm">Current model value: <strong>{format(output.data.baseline)}</strong></p>
        <div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Scenario comparison results</caption><thead><tr><th className="p-3">Scenario</th><th className="p-3">Value</th><th className="p-3">Change from current model</th></tr></thead><tbody>{output.data.scenarios.map(s => <tr key={s.name} className="border-t border-slate-200"><th className="p-3 font-medium">{s.name}</th><td className="p-3 tabular-nums">{format(s.value)}</td><td className="p-3 tabular-nums">{format(s.change)}</td></tr>)}</tbody></table></div>
        <details><summary className="cursor-pointer text-sm font-medium">Inspect every scenario output</summary><div className="mt-3 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-3">Variable</th>{output.data.scenarios.map(s => <th className="p-3" key={s.name}>{s.name}</th>)}</tr></thead><tbody>{graph.nodes.map(node => <tr key={node.id} className="border-t border-slate-200"><th className="p-3 font-medium">{node.label} ({node.id})</th>{output.data.scenarios.map(s => <td className="p-3" key={s.name}>{format(s.results[node.id])}</td>)}</tr>)}</tbody></table></div></details>
      </>}
      {output.mode === 'sensitivity' && <div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="pb-3 text-left text-xs">Rows: {label(plan.y)}. Columns: {label(plan.x)}. Output: {label(plan.target)}.</caption><thead><tr><th className="p-3">Row / column</th>{output.data.x_values.map((x, i) => <th key={i} className="p-3">{format(x)}</th>)}</tr></thead><tbody>{output.data.results_matrix.map((row, index) => <tr key={index} className="border-t border-slate-200"><th className="bg-slate-100 p-3">{format(output.data.y_values[index])}</th>{row.map((value, i) => <td key={i} className="p-3 tabular-nums">{format(value)}</td>)}</tr>)}</tbody></table></div>}
      {output.mode === 'simulation' && <>
        <p className="text-xs text-slate-600">{output.data.iterations} independent-input draws · seed {output.data.seed}. Values use the target's units.</p>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-5">{([['Mean', output.data.mean], ['Median', output.data.median], ['Std. deviation', output.data.std], ['5th percentile', output.data.percentile_5], ['95th percentile', output.data.percentile_95]] as const).map(([name, value]) => <div key={name}><dt className="text-xs text-slate-500">{name}</dt><dd className="mt-1 font-semibold tabular-nums">{format(value)}</dd></div>)}</dl>
        <div className="h-72 w-full min-w-0" aria-label="Simulation outcome histogram"><ResponsiveContainer width="100%" height="100%"><BarChart data={output.data.histogram.counts.map((count, i) => ({range: `${format(output.data.histogram.bins[i])} to ${format(output.data.histogram.bins[i+1])}`, count}))}><CartesianGrid vertical={false} stroke="#e2e8f0"/><XAxis dataKey="range" tick={false} label={{value: 'Target outcome (bin ranges in tooltip)', position: 'insideBottom', offset: -5}}/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="count" name="Draws" fill="#637be6"/></BarChart></ResponsiveContainer></div>
      </>}
    </section>}
  </section>;
}
