'use client';
import {useEffect, useMemo, useRef, useState} from 'react';
import ReactFlow, {Handle, Position, NodeProps, ReactFlowInstance, applyNodeChanges} from 'reactflow';
import 'reactflow/dist/style.css';
import api, {errorMessage} from '@/utils/api';
import {Graph, Variable, VariableType, arrange, connections, inputError, payload, readGraph, references} from '@/utils/graph';
import {buttonClass, primaryClass, fieldClass, downloadJSON} from '@/utils/research';
import BuilderAnalysis from '@/components/BuilderAnalysis';

type Result = {results: Record<string, number>; steps: string[]};
type SavedModel = {id: string; revision: number; updated: string; graph: Graph};
function savedModels(): SavedModel[] {
  const parsed = JSON.parse(localStorage.getItem('vertige-graph-library-v1') || '[]');
  if (!Array.isArray(parsed) || parsed.length > 100) throw new Error('Saved model library is invalid. Export your working graph before resetting browser storage.');
  return parsed.map(item => {
    if (!item || typeof item.id !== 'string' || !Number.isInteger(item.revision) || item.revision < 1 || typeof item.updated !== 'string') throw new Error('A saved model entry is invalid.');
    return {...item, graph: readGraph(item.graph)};
  });
}
type DiagramData = {label: string; kind: VariableType; formula: string; value: number | null};
const format = (value: number) => new Intl.NumberFormat('en-US', {maximumFractionDigits: 6}).format(value);
const examples = {dcf: ['Revenue and EBIT', 'A two-period operating example, not a full DCF valuation.'], cash_flow: ['Multi-year operating cash flow', 'Year-specific growth and margins, operating working capital, cash taxes and discounted free cash flow. Excludes terminal value and equity claims.'], ddm: ['Dividend perpetuity', 'Annual next dividend / (required return − growth). Rates use decimals; require return > growth for a meaningful perpetuity.'], three_statement: ['Operating profit bridge', 'Revenue, gross profit and EBIT. Use the valuation workspace for linked financial statements.']} as const;

function DiagramNode({id, data}: NodeProps<DiagramData>) {
  return <div className="w-[250px] rounded border border-slate-300 bg-white px-4 py-3 text-slate-900">
    <Handle type="target" position={Position.Left} isConnectable={false} className="!bg-brand-500" />
    <p className="text-[10px] uppercase tracking-wide text-slate-500">{data.kind.toLowerCase()}</p>
    <p className="mt-1 truncate text-sm font-semibold">{data.label}</p>
    <p className="mt-1 truncate font-mono text-xs text-slate-500">{id}</p>
    <p className="mt-2 truncate text-xs">{data.value === null ? (data.kind === 'FORMULA' ? data.formula || 'Formula missing' : 'Value missing') : format(data.value)}</p>
    <Handle type="source" position={Position.Right} isConnectable={false} className="!bg-brand-500" />
  </div>;
}
const nodeTypes = {variable: DiagramNode};

export default function ModelBuilderPage() {
  const [graph, setGraph] = useState<Graph>({name: 'Untitled model', nodes: []});
  const [view, setView] = useState<'variables' | 'graph'>('variables');
  const [example, setExample] = useState<keyof typeof examples>('dcf');
  const [years, setYears] = useState(5), [search, setSearch] = useState(''), [filter, setFilter] = useState('all');
  const [library, setLibrary] = useState<SavedModel[]>([]), [chosen, setChosen] = useState('');
  const [activeSave, setActiveSave] = useState<{id: string; revision: number} | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [result, setResult] = useState<Result | null>(null), [changed, setChanged] = useState(false);
  const [recovery, setRecovery] = useState<Graph | null>(null), [importing, setImporting] = useState(false), [importText, setImportText] = useState('');
  const [newId, setNewId] = useState(''), [newLabel, setNewLabel] = useState(''), [newType, setNewType] = useState<VariableType>('INPUT');
  const [flow, setFlow] = useState<ReactFlowInstance | null>(null), [layoutVersion, setLayoutVersion] = useState(0);
  const sequence = useRef(0);

  useEffect(() => {try {const raw = localStorage.getItem('vertige-graph-draft-v2'); if (raw) setRecovery(readGraph(JSON.parse(raw)));} catch {setNotice('Browser draft is unavailable. Restore a saved graph or import an export.');}}, []);
  useEffect(() => {try {setLibrary(savedModels());} catch (e) {setError(errorMessage(e));}}, []);
  useEffect(() => {if (!changed) return; try {localStorage.setItem('vertige-graph-draft-v2', JSON.stringify(graph));} catch {setNotice('Browser draft storage is unavailable. Export the graph before leaving.');}}, [graph, changed]);
  useEffect(() => {if (view === 'graph' && flow) {const frame = requestAnimationFrame(() => flow.fitView({padding: .15, maxZoom: 1})); return () => cancelAnimationFrame(frame);}}, [flow, view, layoutVersion]);

  function replace(next: Graph, message = '') {sequence.current++; setGraph(next); setResult(null); setError(''); setNotice(message); setChanged(true); setRecovery(null);}
  function update(id: string, patch: Partial<Variable>) {replace({...graph, nodes: graph.nodes.map(n => n.id === id ? {...n, ...patch} : n)});}
  async function loadExample() {
    setBusy(true); setError(''); const request = ++sequence.current;
    try {const data = (await api.get(`/builder/templates/${example}`, {params: example === 'cash_flow' ? {years} : {}})).data; if (request !== sequence.current) return; replace(arrange(readGraph({...data, name: data.name || examples[example][0]})), examples[example][1]); setActiveSave(null); setSearch(''); setFilter('all'); setLayoutVersion(n => n + 1);}
    catch (e) {setError(errorMessage(e));} finally {setBusy(false);}
  }
  async function calculate() {
    const invalid = inputError(graph); setResult(null); setError(invalid || ''); setNotice(''); if (invalid) return;
    setBusy(true); const request = ++sequence.current;
    try {const data = (await api.post('/builder/solve', payload(graph))).data; if (request === sequence.current) setResult(data);}
    catch (e) {if (request === sequence.current) setError(errorMessage(e));} finally {setBusy(false);}
  }
  function save(asNew = false) {
    try {
      const models = savedModels(), existing = !asNew && activeSave ? models.find(item => item.id === activeSave.id) : undefined;
      if (!asNew && activeSave && (!existing || existing.revision !== activeSave.revision)) throw new Error('This saved model changed in another tab. Save as a new template to preserve your draft, or load the latest saved model.');
      if (!existing && models.length >= 100) throw new Error('This browser has 100 saved models. Export your graph for portability.');
      const record: SavedModel = {id: existing?.id || crypto.randomUUID(), revision: (existing?.revision || 0) + 1, updated: new Date().toISOString(), graph};
      const next = [record, ...models.filter(item => item.id !== record.id)];
      localStorage.setItem('vertige-graph-library-v1', JSON.stringify(next));
      setLibrary(next); setActiveSave({id: record.id, revision: record.revision}); setChosen(record.id);
      localStorage.setItem('vertige-graph-v2', JSON.stringify(graph)); localStorage.removeItem('vertige-graph-draft-v2');
      setChanged(false); setRecovery(null); setError(''); setNotice(`Saved “${graph.name}”, revision ${record.revision}, in this browser. Export a copy for portability.`);
    } catch (e) {setError(errorMessage(e));}
  }
  function restore() {try {const raw = localStorage.getItem('vertige-graph-v2') || localStorage.getItem('vertige-graph-v1'); if (!raw) throw new Error('No saved graph in this browser.'); replace(arrange(readGraph(JSON.parse(raw))), 'Saved graph restored. Recalculate to refresh results.'); setActiveSave(null); setSearch(''); setFilter('all'); setLayoutVersion(n => n + 1);} catch (e) {setError(errorMessage(e));}}
  function loadSaved() {try {const models = savedModels(), saved = models.find(item => item.id === chosen); if (!saved) throw new Error('Choose an available saved model.'); setLibrary(models); replace(arrange(saved.graph), `Loaded “${saved.graph.name}”, revision ${saved.revision}. Recalculate to refresh results.`); setActiveSave({id: saved.id, revision: saved.revision}); setSearch(''); setFilter('all'); setLayoutVersion(n => n + 1);} catch (e) {setError(errorMessage(e));}}
  function add() {
    if (!/^[A-Za-z_][A-Za-z0-9_.-]{0,79}$/.test(newId)) {setError('Use a variable ID beginning with a letter or underscore, followed by letters, numbers, underscores, dots or hyphens.'); return;}
    if (graph.nodes.some(n => n.id === newId)) {setError('That variable ID is already in use.'); return;}
    if (graph.nodes.length >= 200) {setError('A graph can contain at most 200 variables.'); return;}
    replace(arrange({...graph, nodes: [...graph.nodes, {id: newId, label: newLabel.trim() || newId, type: newType, value: null, formula: '', position: {x: 0, y: 0}}]}));
    setNewId(''); setNewLabel(''); setLayoutVersion(n => n + 1); setView('variables');
  }
  const diagramNodes = useMemo(() => graph.nodes.map(node => ({id: node.id, type: 'variable', position: node.position, data: {label: node.label, kind: node.type, formula: node.formula, value: result?.results[node.id] ?? (node.type === 'FORMULA' ? null : node.value)}})), [graph, result]);
  const diagramEdges = useMemo(() => connections(graph).map(edge => ({...edge, id: `${edge.source}:${edge.target}`, style: {stroke: '#637be6', strokeWidth: 1.5}})), [graph]);
  const shown = graph.nodes.filter(node => (filter === 'all' || (filter === 'inputs' ? node.type !== 'FORMULA' : node.type === 'FORMULA')) && `${node.label} ${node.id}`.toLowerCase().includes(search.toLowerCase()));
  const periods = graph.nodes.map(node => /^revenue_(\d+)$/.exec(node.id)?.[1]).filter((year): year is string => !!year && Number(year) > 0).sort((a, b) => Number(a) - Number(b));

  return <div className="mx-auto max-w-7xl space-y-6">
    <header className="border-b border-slate-300 pb-6"><p className="text-xs uppercase tracking-[.15em] text-brand-700">Financial modeling</p><h1 className="mt-2 text-3xl font-semibold">Model builder</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">Define inputs and formulas, then inspect their dependencies and calculation order. Formula references create the connections automatically. All values use the units you choose; enter rates as decimals, for example 0.08 for 8%.</p></header>
    {error && <p role="alert" className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</p>}
    {notice && <p role="status" className="text-sm text-slate-600">{notice}</p>}
    {recovery && <div className="flex flex-wrap items-center gap-4 border border-amber-200 bg-amber-50 p-4"><p className="text-sm">A browser draft of “{recovery.name}” is available.</p><button disabled={busy} className={buttonClass} onClick={() => {replace(recovery, 'Browser draft recovered. Recalculate to refresh results.'); setLayoutVersion(n => n + 1);}}>Resume graph draft</button></div>}
    <fieldset disabled={busy} className="space-y-5">
      <div className="flex flex-wrap items-end gap-3"><label className="min-w-48 flex-1 text-xs font-medium">Model name<input className={fieldClass} value={graph.name} maxLength={160} onChange={e => replace({...graph, name: e.target.value})} /></label><button className={buttonClass} onClick={() => save()}>Save graph</button><button className={buttonClass} onClick={() => save(true)}>Save as new template</button><button className={buttonClass} onClick={restore}>Restore graph</button><button className={buttonClass} onClick={() => downloadJSON({format: 'vertige-graph', version: 2, graph}, 'vertige-model.json')}>Export graph</button><button className={buttonClass} onClick={() => setImporting(!importing)}>Import graph JSON</button></div>
      {!!library.length && <div className="flex flex-wrap items-end gap-3"><label className="min-w-0 flex-1 text-xs font-medium">Saved models<select className={fieldClass} value={chosen} onChange={e => setChosen(e.target.value)}><option value="">Choose a model</option>{library.map(item => <option key={item.id} value={item.id}>{item.graph.name} · revision {item.revision} · {item.updated.slice(0, 10)}</option>)}</select></label><button disabled={!chosen} className={buttonClass} onClick={loadSaved}>Load selected model</button><p className="text-xs text-slate-500">Loads a saved copy. Save or export current work before replacing it.</p></div>}
      {importing && <form className="space-y-3 border-y border-slate-200 py-4" onSubmit={e => {e.preventDefault(); try {replace(arrange(readGraph(JSON.parse(importText))), 'Graph imported. Connections were rebuilt from the formulas; recalculate to validate.'); setLayoutVersion(n => n + 1); setImporting(false);} catch (e) {setError(errorMessage(e));}}}><label className="block text-sm">Graph JSON<textarea className={fieldClass + ' h-32 font-mono text-xs'} maxLength={500000} value={importText} onChange={e => setImportText(e.target.value)} /></label><button className={buttonClass}>Replace with imported graph</button></form>}
      <div className="flex flex-wrap items-end gap-3"><label className="min-w-0 text-xs font-medium">Example<select className={fieldClass} value={example} onChange={e => setExample(e.target.value as keyof typeof examples)}>{Object.entries(examples).map(([key, [name]]) => <option value={key} key={key}>{name}</option>)}</select></label>{example === 'cash_flow' && <label className="text-xs font-medium">Forecast years<select className={fieldClass} value={years} onChange={e => setYears(Number(e.target.value))}>{Array.from({length: 10}, (_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select></label>}<button className={buttonClass} onClick={loadExample}>{graph.nodes.length ? 'Replace graph with example' : 'Load example'}</button><p className="max-w-lg text-xs leading-5 text-slate-500">{examples[example][1]} Save or export existing work before replacing it.</p></div>
      <details><summary className="cursor-pointer text-sm font-medium">Model notes and assumptions</summary><label className="mt-3 block text-xs font-medium">Model notes<textarea className={fieldClass + ' h-28'} maxLength={4000} value={graph.notes || ''} onChange={e => replace({...graph, notes: e.target.value})}/></label></details>
      <form onSubmit={e => {e.preventDefault(); add();}} className="grid items-end gap-3 border-y border-slate-200 py-5 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_180px_auto]"><label className="text-xs font-medium">New variable ID<input required placeholder="revenue" className={fieldClass} value={newId} onChange={e => setNewId(e.target.value)} maxLength={80} /></label><label className="text-xs font-medium">New variable label<input placeholder="Revenue (millions)" className={fieldClass} value={newLabel} onChange={e => setNewLabel(e.target.value)} maxLength={160} /></label><label className="text-xs font-medium">Variable type<select className={fieldClass} value={newType} onChange={e => setNewType(e.target.value as VariableType)}><option value="INPUT">Input</option><option value="CONSTANT">Constant</option><option value="FORMULA">Formula</option></select></label><button className={buttonClass}>Add variable</button></form>
      <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex flex-wrap gap-2"><button aria-pressed={view === 'variables'} className={view === 'variables' ? primaryClass : buttonClass} onClick={() => setView('variables')}>Variables and formulas</button><button aria-pressed={view === 'graph'} className={view === 'graph' ? primaryClass : buttonClass} onClick={() => setView('graph')}>Dependency graph</button></div><button disabled={!graph.nodes.length || busy} className={primaryClass} onClick={calculate}>{busy ? 'Calculating…' : 'Calculate model'}</button></div>
      <p role="status" className="text-xs text-slate-600">{graph.nodes.length} variables · {diagramEdges.length} formula connections · {result ? 'Results match the current inputs.' : 'Recalculate after editing to see current results.'}</p>
      {view === 'variables' && !!graph.nodes.length && <div className="flex flex-wrap items-end gap-3"><label className="min-w-48 flex-1 text-xs font-medium">Find a variable<input className={fieldClass} value={search} onChange={e => setSearch(e.target.value)} placeholder="Label, variable ID or year"/></label><label className="text-xs font-medium">Show variables<select className={fieldClass} value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All variables</option><option value="inputs">Input assumptions</option><option value="formulas">Formulas</option></select></label><p className="text-xs text-slate-500">Showing {shown.length} of {graph.nodes.length}</p></div>}
      {!graph.nodes.length ? <div className="border border-dashed border-slate-300 p-10 text-sm leading-6 text-slate-600">Load an example or add your first input. Then add a formula such as <code>{'{revenue} * 0.2'}</code>. Use variable IDs in braces; labels are for display.</div> : view === 'variables' ? <div className="divide-y divide-slate-200 border-y border-slate-300">{!shown.length && <p className="py-8 text-sm">No variables match these filters.</p>}{shown.map(node => <section key={node.id} className="grid gap-4 py-5 lg:grid-cols-[220px_1fr_auto]">
        <div><label className="block text-xs font-medium">Label for {node.id}<input className={fieldClass} value={node.label} onChange={e => update(node.id, {label: e.target.value})} /></label><p className="mt-2 break-all font-mono text-xs text-slate-500">{node.id} · {node.type.toLowerCase()}</p></div>
        <div>{node.type === 'FORMULA' ? <><label className="block text-xs font-medium">Formula for {node.id}<input className={fieldClass + ' font-mono'} value={node.formula} maxLength={500} onChange={e => update(node.id, {formula: e.target.value})} /></label><p className="mt-2 break-words text-xs text-slate-500">References: {references(node.formula).join(', ') || 'none'}</p></> : <label className="block text-xs font-medium">Value for {node.id}<input type="number" step="any" className={fieldClass} value={node.value ?? ''} onChange={e => update(node.id, {value: e.target.value === '' ? null : Number(e.target.value)})} /></label>}{result && <p className="mt-2 text-sm font-medium">Calculated value: {format(result.results[node.id])}</p>}</div>
        <button className={buttonClass + ' self-start'} onClick={() => replace({...graph, nodes: graph.nodes.filter(n => n.id !== node.id)})}>Remove {node.id}</button>
      </section>)}</div> : <section className="min-w-0 border border-slate-300 bg-slate-50"><div className="flex flex-wrap gap-2 border-b border-slate-200 p-3"><button className={buttonClass} onClick={() => {replace(arrange(graph), 'Graph arranged without overlapping nodes.'); setLayoutVersion(n => n + 1);}}>Arrange graph</button><button className={buttonClass} onClick={() => flow?.fitView({padding: .15, maxZoom: 1})}>Fit graph</button><button className={buttonClass} onClick={() => flow?.zoomIn()}>Zoom in</button><button className={buttonClass} onClick={() => flow?.zoomOut()}>Zoom out</button></div><div aria-label="Formula dependency canvas" className="h-[540px] w-full min-w-0"><ReactFlow nodes={diagramNodes} edges={diagramEdges} nodeTypes={nodeTypes} onInit={setFlow} nodesDraggable={!busy} nodesConnectable={false} edgesUpdatable={false} deleteKeyCode={null} fitView minZoom={.1} maxZoom={1.5} onNodesChange={changes => {const positions = changes.filter(c => c.type === 'position'); if (positions.length) {const moved = applyNodeChanges(positions, diagramNodes); setGraph(current => ({...current, nodes: current.nodes.map(node => ({...node, position: moved.find(n => n.id === node.id)?.position || node.position}))})); setChanged(true);}}} /></div><p className="border-t border-slate-200 p-3 text-xs leading-5 text-slate-600">Read connections from left to right. Drag nodes to arrange them. Edit the formulas in the variables view to change their connections.</p></section>}
    </fieldset>
    {result && periods.length > 0 && graph.nodes.some(node => node.id === 'forecast_value') && <section className="space-y-3 border-t border-slate-300 pt-6"><h2 className="text-xl font-semibold">Annual operating schedule</h2><p className="text-sm text-slate-600">Present value of explicit forecast cash flows: <strong>{format(result.results.forecast_value)}</strong>. Terminal value and equity claims are excluded.</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Annual operating cash-flow schedule in model units</caption><thead><tr><th className="p-3">Model units</th>{periods.map(year => <th className="p-3" key={year}>Year {year}</th>)}</tr></thead><tbody>{[['revenue', 'Revenue'], ['ebit', 'EBIT'], ['nopat', 'NOPAT'], ['delta_nwc', 'Change in operating NWC'], ['fcff', 'Unlevered FCF'], ['pv_fcff', 'Present value']].map(([id, label]) => <tr className="border-t border-slate-200" key={id}><th className="p-3 font-medium">{label}</th>{periods.map(year => <td className="p-3 tabular-nums" key={year}>{result.results[`${id}_${year}`] === undefined ? '—' : format(result.results[`${id}_${year}`])}</td>)}</tr>)}</tbody></table></div></section>}
    {result && <section className="space-y-4 border-t border-slate-300 pt-6"><h2 className="text-xl font-semibold">Calculation results</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-3">Variable</th><th className="p-3">ID</th><th className="p-3 text-right">Value</th></tr></thead><tbody>{graph.nodes.map(node => <tr key={node.id} className="border-t border-slate-200"><th className="p-3 font-medium">{node.label}</th><td className="p-3 font-mono text-xs">{node.id}</td><td className="p-3 text-right tabular-nums">{format(result.results[node.id])}</td></tr>)}</tbody></table></div><details><summary className="cursor-pointer text-sm font-medium">Calculation order</summary><ol className="mt-3 list-decimal space-y-2 pl-5 text-xs text-slate-600">{result.steps.map((step, index) => <li key={index}>{step}</li>)}</ol></details></section>}
    <details className="border-t border-slate-300 pt-5"><summary className="cursor-pointer text-lg font-semibold">Scenario, sensitivity and simulation tools</summary><BuilderAnalysis graph={graph} disabled={busy} onBusyChange={setBusy} onChange={analysis => {setGraph(current => ({...current, analysis})); setChanged(true);}}/></details>
    <details className="border-t border-slate-200 pt-4"><summary className="cursor-pointer text-sm font-medium">Formula syntax and limits</summary><p className="mt-3 text-sm leading-6 text-slate-600">Use {'{variable_id}'} references and +, −, *, /, **, parentheses, min, max, sum, abs, pow, round, sqrt, log and exp. Exponents are limited to 16 in magnitude. Missing references, circular dependencies, division by zero and non-finite results are rejected. Maximum 200 variables and 500 characters per formula. This is a scalar arithmetic engine; financial assumptions still require your review.</p></details>
  </div>;
}
