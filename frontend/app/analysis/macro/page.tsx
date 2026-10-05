'use client';
import {useEffect, useState} from 'react';
import {CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import api, {errorMessage} from '@/utils/api';
import {buttonClass, fieldClass, primaryClass} from '@/utils/research';
import {downloadCSV} from '@/utils/export';

type Observation = {date: string; value: number};
type Country = {cpi_yoy: number; cpi: Observation[]; unemployment: Observation[]; fed_funds_history?: Observation[]; interest_rate?: Observation[]; provenance: {source: string; fetched_at: string}};
type Curve = {date: string; points: {tenor: string; value: number | null; series: string}[]; spread_10y_2y_bps: number | null; unavailable: {tenor: string; error: string}[]; methodology: string; provenance: {source: string; fetched_at: string}};
const fmt = (value: number | null | undefined) => value === null || value === undefined ? 'Unavailable' : value.toFixed(2);

function yoy(series: Observation[]) {
  const values = new Map(series.map(p => [p.date.slice(0, 7), p.value]));
  return series.map(p => {const prior = values.get(`${Number(p.date.slice(0, 4))-1}${p.date.slice(4, 7)}`); return {date: p.date, value: prior && prior > 0 ? (p.value/prior-1)*100 : null};});
}

export default function Macro() {
  const [us, setUS] = useState<Country | null>(null), [ca, setCA] = useState<Country | null>(null);
  const [loading, setLoading] = useState(true), [errors, setErrors] = useState<string[]>([]), [refresh, setRefresh] = useState(0);
  const [months, setMonths] = useState(24), [view, setView] = useState('inflation');
  const [curve, setCurve] = useState<Curve | null>(null), [curveError, setCurveError] = useState(''), [curveBusy, setCurveBusy] = useState(false);
  useEffect(() => {
    let cancelled = false; setLoading(true); setErrors([]); setUS(null); setCA(null);
    Promise.allSettled([api.get('/macro/us', {timeout: 45000}), api.get('/macro/canada', {timeout: 45000})]).then(([a, b]) => {
      if (cancelled) return;
      if (a.status === 'fulfilled') setUS(a.value.data);
      if (b.status === 'fulfilled') setCA(b.value.data);
      setErrors([...(a.status === 'rejected' ? [`US: ${errorMessage(a.reason)}`] : []), ...(b.status === 'rejected' ? [`Canada: ${errorMessage(b.reason)}`] : [])]); setLoading(false);
    });
    return () => {cancelled = true;};
  }, [refresh]);
  const series = (country: Country | null, key: 'us' | 'ca') => {
    if (!country) return [];
    const values = view === 'inflation' ? yoy(country.cpi) : view === 'unemployment' ? country.unemployment : view === 'rates' ? (key === 'us' ? country.fed_funds_history || [] : country.interest_rate || []) : country.cpi;
    return values.slice(-months);
  };
  const rows = new Map<string, {date: string; us?: number | null; ca?: number | null}>();
  for (const [key, country] of [['us', us], ['ca', ca]] as const) for (const point of series(country, key)) {const date = point.date.slice(0, 7); rows.set(date, {...rows.get(date), date, [key]: point.value});}
  const chart = [...rows.values()].sort((a, b) => a.date.localeCompare(b.date));
  async function loadCurve() {setCurveBusy(true); setCurve(null); setCurveError(''); try {setCurve((await api.get('/macro/treasury-curve')).data);} catch (e) {setCurveError(errorMessage(e));} finally {setCurveBusy(false);}}
  function exportData() {
    const result: (string | number | null)[][] = [['Country', 'Series', 'Date', 'Value', 'Source', 'Fetched at']];
    for (const [name, country] of [['US', us], ['Canada', ca]] as const) if (country) for (const [key, values] of Object.entries({CPI: country.cpi, Unemployment: country.unemployment, [name === 'US' ? 'Fed funds' : '10-year bond yield']: country.fed_funds_history || country.interest_rate || []})) values.forEach(point => result.push([name, key, point.date, point.value, country.provenance.source, country.provenance.fetched_at]));
    if (curve) {result.push([], ['Treasury common date', curve.date], ['Tenor', 'Yield percent', 'FRED series']); curve.points.forEach(point => result.push([point.tenor, point.value, point.series]));}
    downloadCSV('vertige-macro-observations.csv', result);
  }
  return <section className="mx-auto max-w-7xl space-y-7">
    <header className="border-b border-slate-300 pb-6"><h1 className="text-3xl font-semibold">Macroeconomic overview</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">Compare inflation, labor markets and rates using dated observations. Explore the underlying monthly records and the US Treasury curve. Data is revised by providers; retrieval time is not the observation date.</p></header>
    <div className="flex flex-wrap gap-3"><button disabled={loading} className={primaryClass} onClick={() => setRefresh(value => value+1)}>Refresh macro data</button><button disabled={!us && !ca} className={buttonClass} onClick={exportData}>Export macro observations</button></div>
    {loading && <p role="status">Loading macro observations…</p>}
    {!!errors.length && <div role="alert" className="space-y-2 border border-amber-200 bg-amber-50 p-4 text-sm">{errors.map(error => <p key={error}>{error}</p>)}<p>Available country data remains visible. Retry using Refresh macro data.</p></div>}
    {(us || ca) && <>
      <dl className="grid grid-cols-2 gap-5 border-y border-slate-200 py-6 md:grid-cols-4">{[['US CPI, year over year', us?.cpi_yoy], ['Canada CPI, year over year', ca?.cpi_yoy], ['US unemployment', us?.unemployment.at(-1)?.value], ['Canada unemployment', ca?.unemployment.at(-1)?.value]].map(([label, value]) => <div key={String(label)}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-2 text-2xl font-semibold">{typeof value === 'number' ? fmt(value)+'%' : 'Unavailable'}</dd></div>)}</dl>
      <div className="space-y-2 text-xs leading-5 text-slate-600">{[['US', us], ['Canada', ca]].map(([label, country]) => {const c = country as Country | null; return c && <p key={String(label)}>{String(label)}: CPI {c.cpi.at(-1)?.date}; unemployment {c.unemployment.at(-1)?.date}; rates {(c.fed_funds_history || c.interest_rate)?.at(-1)?.date}. {c.provenance.source}. Fetched {c.provenance.fetched_at}. {[c.cpi, c.unemployment, c.fed_funds_history || c.interest_rate || []].some(points => points.at(-1) && Date.now()-Date.parse(points.at(-1)!.date)>120*86400000) && <strong>Some observations are more than 120 days old.</strong>}</p>;})}</div>
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-xs font-medium">Macro series<select className={fieldClass} value={view} onChange={e => setView(e.target.value)}><option value="inflation">CPI growth, year over year (%)</option><option value="index">CPI index levels</option><option value="unemployment">Unemployment (%)</option><option value="rates">US policy rate and Canada bond yield (%)</option></select></label><label className="text-xs font-medium">Monthly history<select className={fieldClass} value={months} onChange={e => setMonths(Number(e.target.value))}>{[12,24,60].map(value => <option key={value} value={value}>Last {value} observations</option>)}</select></label></div>
      <p className="text-xs leading-5 text-slate-600">{view === 'inflation' ? 'Year-over-year growth uses the same month in the prior year. Missing year-ago observations leave gaps. US CPI is seasonally adjusted; Canadian CPI is not seasonally adjusted.' : view === 'index' ? 'The index bases differ: US 1982–1984=100; Canada 2002=100. Comparing these raw levels does not compare price levels between countries.' : view === 'rates' ? 'US Fed Funds is a policy rate; the Canadian series is a 10-year government bond yield. These are different instruments, not equivalent policy rates.' : 'Unemployment definitions and survey methods can differ between countries.'}</p>
      <div className="h-80 min-w-0 w-full" aria-label="Macro history chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={chart}><CartesianGrid vertical={false} stroke="#e2e8f0"/><XAxis dataKey="date" minTickGap={65} tick={{fontSize:11}}/><YAxis width={55}/><Tooltip/><Legend/><Line type="linear" dataKey="us" name={view === 'rates' ? 'US Fed Funds' : 'US'} stroke="#637be6" dot={false} connectNulls={false}/><Line type="linear" dataKey="ca" name={view === 'rates' ? 'Canada 10-year bond' : 'Canada'} stroke="#b47a35" dot={false} connectNulls={false}/></LineChart></ResponsiveContainer></div>
      <details className="border-t border-slate-200 pt-4"><summary className="cursor-pointer text-sm font-medium">Inspect selected monthly observations</summary><div className="mt-4 max-h-80 overflow-auto"><table className="w-full text-right text-sm"><thead><tr><th className="p-3">Month</th><th className="p-3">US</th><th className="p-3">Canada</th></tr></thead><tbody>{chart.map(row => <tr key={row.date} className="border-t border-slate-200"><th className="p-3 font-normal">{row.date}</th><td className="p-3">{fmt(row.us)}</td><td className="p-3">{fmt(row.ca)}</td></tr>)}</tbody></table></div></details>
    </>}
    <details className="border-t border-slate-300 pt-5"><summary className="cursor-pointer text-lg font-semibold">US Treasury curve and term spread</summary><div className="mt-5 space-y-5"><p className="text-sm leading-6 text-slate-600">Constant-maturity Treasury yields from FRED, using a common date across available maturities. This curve provides rate context; it is not a spot curve for discounting individual bond cash flows.</p><button disabled={curveBusy} className={buttonClass} onClick={loadCurve}>{curveBusy ? 'Loading Treasury yields…' : 'Load Treasury curve'}</button>{curveError && <p role="alert" className="text-sm text-red-800">{curveError}</p>}{curve && <>
      <p className="text-sm">Observation date <strong>{curve.date}</strong>. 10Y − 2Y spread: <strong>{curve.spread_10y_2y_bps === null ? 'Unavailable' : fmt(curve.spread_10y_2y_bps)+' basis points'}</strong>.</p>
      {!!curve.unavailable.length && <p role="status" className="text-sm text-amber-800">Unavailable tenors: {curve.unavailable.map(item => item.tenor).join(', ')}.</p>}
      <div className="h-72 min-w-0 w-full" aria-label="Treasury yield curve"><ResponsiveContainer width="100%" height="100%"><LineChart data={curve.points}><CartesianGrid vertical={false} stroke="#e2e8f0"/><XAxis dataKey="tenor"/><YAxis tickFormatter={value => `${value}%`} domain={['auto','auto']}/><Tooltip formatter={(value: number) => `${value.toFixed(2)}%`}/><Line type="linear" dataKey="value" name="Yield" stroke="#637be6" connectNulls={false}/></LineChart></ResponsiveContainer></div>
      <table className="w-full text-left text-sm"><thead><tr><th className="p-3">Tenor</th><th className="p-3">Yield (%)</th><th className="p-3">Source series</th></tr></thead><tbody>{curve.points.map(point => <tr className="border-t border-slate-200" key={point.tenor}><th className="p-3 font-normal">{point.tenor}</th><td className="p-3">{fmt(point.value)}</td><td className="p-3"><a className="text-brand-800 underline" target="_blank" rel="noreferrer" href={`https://fred.stlouisfed.org/series/${point.series}`}>{point.series}</a></td></tr>)}</tbody></table>
      <p className="text-xs leading-5 text-slate-600">{curve.methodology} Fetched {curve.provenance.fetched_at}. An inverted spread is an observation, not a recession forecast.</p>
    </>}</div></details>
  </section>;
}
