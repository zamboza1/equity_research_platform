import {AnalysisPlan, readPlan} from './model-analysis';
export type VariableType = 'INPUT' | 'CONSTANT' | 'FORMULA';
export type Variable = {id: string; label: string; type: VariableType; value: number | null; formula: string; position: {x: number; y: number}};
export type Graph = {name: string; nodes: Variable[]; notes?: string; analysis?: AnalysisPlan};
export const references = (formula: string) => [...new Set(Array.from(formula.matchAll(/\{([^}]+)\}/g), match => match[1]))];
export const connections = (graph: Graph) => graph.nodes.flatMap(node => node.type === 'FORMULA' ? references(node.formula).filter(id => graph.nodes.some(n => n.id === id)).map(source => ({source, target: node.id})) : []);
export const payload = (graph: Graph) => ({nodes: graph.nodes.map(node => ({...node, value: node.type === 'FORMULA' ? null : node.value, formula: node.type === 'FORMULA' ? node.formula : null})), edges: connections(graph)});

export function arrange(graph: Graph): Graph {
  const levels = new Map<string, number>();
  const depth = (id: string, seen = new Set<string>()): number => {
    if (levels.has(id)) return levels.get(id)!;
    if (seen.has(id)) return 0;
    const node = graph.nodes.find(n => n.id === id);
    if (!node || node.type !== 'FORMULA') return 0;
    const refs = references(node.formula).filter(ref => graph.nodes.some(n => n.id === ref));
    const level = refs.length ? Math.min(20, 1 + Math.max(...refs.map(ref => depth(ref, new Set([...seen, id]))))) : 0;
    levels.set(id, level);
    return level;
  };
  const rows = new Map<number, number>();
  return {...graph, nodes: graph.nodes.map(node => {
    const column = depth(node.id), row = rows.get(column) || 0;
    rows.set(column, row + 1);
    return {...node, position: {x: column * 320, y: row * 160}};
  })};
}

export function readGraph(value: unknown): Graph {
  if (!value || typeof value !== 'object') throw new Error('Expected a graph JSON object.');
  const root = value as Record<string, unknown>;
  if (root.format && (root.format !== 'vertige-graph' || root.version !== 2)) throw new Error('Unsupported graph export version.');
  const graph = (root.graph || root) as Record<string, unknown>;
  if (!Array.isArray(graph.nodes) || graph.nodes.length > 200) throw new Error('A graph can contain at most 200 variables.');
  const seen = new Set<string>();
  const nodes = graph.nodes.map((raw: Record<string, unknown>) => {
    if (!raw || typeof raw !== 'object') throw new Error('Invalid variable.');
    const data = (raw.data || raw) as Record<string, unknown>;
    const id = String(raw.id || '');
    if (!/^[A-Za-z_][A-Za-z0-9_.-]{0,79}$/.test(id) || seen.has(id)) throw new Error('Variable IDs must be unique, start with a letter, and contain only letters, numbers, underscores, dots or hyphens.');
    seen.add(id);
    if (!['INPUT', 'CONSTANT', 'FORMULA'].includes(String(data.type))) throw new Error(`${id}: unsupported variable type.`);
    const position = raw.position as {x?: unknown; y?: unknown} | undefined;
    return {id, label: String(data.label || id).slice(0, 160), type: data.type as VariableType,
      value: typeof data.value === 'number' && Number.isFinite(data.value) ? data.value : null,
      formula: typeof data.formula === 'string' ? data.formula : '',
      position: {x: typeof position?.x === 'number' && Number.isFinite(position.x) ? position.x : 0,
        y: typeof position?.y === 'number' && Number.isFinite(position.y) ? position.y : 0}};
  });
  return {name: typeof graph.name === 'string' ? graph.name.slice(0, 160) : 'Untitled model', nodes,
    notes: typeof graph.notes === 'string' ? graph.notes.slice(0, 4000) : '',
    ...(graph.analysis ? {analysis: readPlan(graph.analysis)} : {})};
}

export function inputError(graph: Graph): string | null {
  if (!graph.nodes.length) return 'Add a variable or load an example first.';
  for (const node of graph.nodes) {
    if (!node.label.trim()) return `Enter a label for ${node.id}.`;
    if (node.type !== 'FORMULA' && (node.value === null || !Number.isFinite(node.value))) return `Enter a numeric value for ${node.label} (${node.id}). An empty input is not zero.`;
    if (node.type === 'FORMULA' && !node.formula.trim()) return `Enter a formula for ${node.label} (${node.id}).`;
  }
  return null;
}
