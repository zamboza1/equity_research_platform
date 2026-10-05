'use client';
import {useState} from 'react';
import Link from 'next/link';
import api, {errorMessage} from '@/utils/api';
import {buttonClass, fieldClass, primaryClass} from '@/utils/research';
import {downloadCSV} from '@/utils/export';

type Multiple = 'forward_pe' | 'trailing_pe' | 'ev_ebitda' | 'price_book';
type Peer = {ticker: string; name: string; sector: string; forward_pe: number | null; trailing_pe: number | null; ev_ebitda: number | null; price_book: number | null; market_cap: number | null; revenue_growth: number | null; profit_margin: number | null; provenance: {currency: string; financial_currency: string; fetched_at: string; financial_period_end: number | null}};
type PeerTable = {companies: Peer[]; unavailable: {ticker: string; error: string}[]; methodology: string};
type Valuation = {peer_count: number; multiples: {p25: number; median: number; p75: number}; prices: {p25: number; median: number; p75: number}; methodology: string};
const metrics = [['forward_pe', 'Forward P/E'], ['trailing_pe', 'Trailing P/E'], ['ev_ebitda', 'EV/EBITDA'], ['price_book', 'Price/book']] as const;
const presets: Record<string, string> = {Technology: 'AAPL, MSFT, GOOGL, NVDA, ORCL', 'Real Estate': 'PLD, AMT, EQIX, WELL, PSA', Financials: 'JPM, BAC, WFC, GS, MS', Healthcare: 'LLY, JNJ, ABBV, MRK, PFE', Energy: 'XOM, CVX, COP, SLB, EOG', Consumer: 'AMZN, WMT, HD, PG, COST'};
const fmt = (value: number | null) => value === null ? '—' : value.toLocaleString(undefined, {maximumFractionDigits: 2});

export default function Comparables() {
  const [tickers, setTickers] = useState('AAPL, MSFT, GOOGL'), [basketName, setBasketName] = useState('Technology peers');
  const [data, setData] = useState<PeerTable | null>(null), [excluded, setExcluded] = useState<string[]>([]);
  const [metric, setMetric] = useState<Multiple>('forward_pe'), [currency, setCurrency] = useState('USD');
  const [target, setTarget] = useState<number | null>(null), [debt, setDebt] = useState<number | null>(0), [shares, setShares] = useState<number | null>(null);
  const [result, setResult] = useState<Valuation | null>(null), [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false);
  const selected = data?.companies.filter(row => !excluded.includes(row.ticker) && row[metric] !== null && row[metric]! > 0) || [];
  const sorted = [...(data?.companies || [])].sort((a, b) => (a[metric] ?? Infinity) - (b[metric] ?? Infinity));
  const edit = () => {setResult(null); setError(''); setNotice('');};
  async function load() {
    edit(); setData(null); setBusy(true);
    try {
      const symbols = tickers.split(/[\s,]+/).filter(Boolean);
      if (!symbols.length || symbols.length > 12) throw new Error('Enter 1 to 12 ticker symbols.');
      setData((await api.post('/comparables/table', {tickers: symbols}, {timeout: 60000})).data);
    } catch (e) {setError(errorMessage(e));} finally {setBusy(false);}
  }
  async function value() {
    edit(); setBusy(true);
    try {
      if (target === null || target <= 0) throw new Error('Enter a positive target financial measure.');
      if (!/^[A-Z]{3}$/.test(currency)) throw new Error('Use a three-letter currency code.');
      if (metric === 'ev_ebitda' && (debt === null || shares === null || shares <= 0)) throw new Error('Enter net debt and a positive diluted share count.');
      setResult((await api.post('/comparables/value', {metric, multiples: selected.map(row => row[metric]), target_metric: target, net_debt_m: metric === 'ev_ebitda' ? debt : 0, shares_m: metric === 'ev_ebitda' ? shares : 1})).data);
    } catch (e) {setError(errorMessage(e));} finally {setBusy(false);}
  }
  function save() {try {localStorage.setItem('vertige-peers-v1', JSON.stringify({basketName, tickers, excluded, metric, currency, target, debt, shares})); setNotice('Peer basket and target assumptions saved in this browser. Provider data will be refreshed on restore.');} catch {setError('Browser storage is unavailable. Export the peer table instead.');}}
  function restore() {
    try {
      const p = JSON.parse(localStorage.getItem('vertige-peers-v1') || 'null');
      if (!p || typeof p.tickers !== 'string' || typeof p.basketName !== 'string' || !metrics.some(([key]) => key === p.metric) || !Array.isArray(p.excluded) || p.excluded.some((x: unknown) => typeof x !== 'string') || typeof p.currency !== 'string' || [p.target, p.debt, p.shares].some(x => x !== null && (typeof x !== 'number' || !Number.isFinite(x)))) throw new Error('No valid saved peer basket is available.');
      setBasketName(p.basketName); setTickers(p.tickers); setExcluded(p.excluded); setMetric(p.metric); setCurrency(p.currency); setTarget(p.target); setDebt(p.debt); setShares(p.shares); setData(null); edit(); setNotice('Basket restored. Load comparables to fetch current provider data.');
    } catch (e) {setError(errorMessage(e));}
  }
  function exportTable() {
    const rows: (string | number | null)[][] = [['Basket', basketName], ['Source', 'Yahoo Finance via yfinance'], ['Ticker', 'Name', 'Quote currency', 'Financial currency', 'Period end', 'Fetched at', ...metrics.map(([, label]) => label), 'Market cap (native currency billions)', 'Revenue growth %', 'Profit margin %', 'Included in valuation']];
    data?.companies.forEach(row => rows.push([row.ticker, row.name, row.provenance.currency, row.provenance.financial_currency, row.provenance.financial_period_end ? new Date(row.provenance.financial_period_end * 1000).toISOString().slice(0, 10) : null, row.provenance.fetched_at, ...metrics.map(([key]) => row[key]), row.market_cap, row.revenue_growth, row.profit_margin, selected.some(p => p.ticker === row.ticker) ? 'Yes' : 'No']));
    data?.unavailable.forEach(row => rows.push([row.ticker, 'Unavailable', row.error]));
    if (result) rows.push([], ['Valuation method', metric], ['Target currency', currency], ['Target measure', target], ['Net debt and other claims (millions)', debt], ['Diluted shares (millions)', shares], ['Percentile', 'Multiple', 'Implied price'], ...(['p25', 'median', 'p75'] as const).map(key => [key, result.multiples[key], result.prices[key]]), ['Methodology', result.methodology]);
    downloadCSV('vertige-comparables.csv', rows);
  }
  return <section className="mx-auto max-w-7xl space-y-7">
    <header className="border-b border-slate-300 pb-6"><h1 className="text-3xl font-semibold">Company comparables</h1><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">Build a peer basket, inspect periods and choose which companies belong in the valuation. A sector directory is a starting point; business models, capital structures and accounting can still differ.</p></header>
    {error && <p role="alert" className="border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</p>}{notice && <p role="status" className="text-sm text-slate-600">{notice}</p>}
    <fieldset disabled={busy} className="min-w-0 space-y-5">
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-xs font-medium">Peer basket name<input className={fieldClass} value={basketName} onChange={e => setBasketName(e.target.value)}/></label><label className="text-xs font-medium">Sector starting list<select className={fieldClass} value="" onChange={e => {setTickers(presets[e.target.value]); setExcluded([]); setData(null); edit();}}><option value="" disabled>Choose a starting list</option>{Object.keys(presets).map(sector => <option key={sector}>{sector}</option>)}</select></label></div>
      <label className="block text-xs font-medium">Peer tickers<input className={fieldClass} value={tickers} onChange={e => {setTickers(e.target.value.toUpperCase()); setData(null); edit();}}/><span className="mt-2 block font-normal text-slate-500">Up to 12 symbols separated by commas. Partial provider failures remain visible.</span></label>
      <div className="flex flex-wrap gap-3"><button className={primaryClass} onClick={load}>{busy ? 'Loading…' : 'Load comparables'}</button><button className={buttonClass} onClick={save}>Save peer basket</button><button className={buttonClass} onClick={restore}>Restore peer basket</button><button className={buttonClass} disabled={!data} onClick={exportTable}>Export peer table</button></div>
      {data?.unavailable.length ? <div role="status" className="border border-amber-200 bg-amber-50 p-4 text-sm">{data.unavailable.map(row => <p key={row.ticker}>{row.ticker}: {row.error}</p>)}</div> : null}
      {data && !data.companies.length && <p>No peer data is available. Adjust the basket or retry the provider.</p>}
      {!!data?.companies.length && <>
        <label className="block max-w-sm text-xs font-medium">Valuation multiple<select className={fieldClass} value={metric} onChange={e => {setMetric(e.target.value as Multiple); setTarget(null); edit();}}>{metrics.map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
        <div className="overflow-x-auto"><table className="w-full min-w-[950px] text-right text-sm"><caption className="pb-3 text-left text-xs text-slate-600">Sorted by the selected multiple. Positive, available multiples are eligible; exclude peers using the first column.</caption><thead><tr><th className="p-3 text-left">Use / company</th>{metrics.map(([key, label]) => <th className="p-3" key={key}>{label} (x)</th>)}<th className="p-3">Market cap (B)</th><th className="p-3">Growth %</th><th className="p-3">Margin %</th><th className="p-3 text-left">Period and source</th></tr></thead><tbody>{sorted.map(row => <tr className="border-t border-slate-200" key={row.ticker}><th className="p-3 text-left font-normal"><label className="flex items-center gap-2"><input type="checkbox" aria-label={`Include ${row.ticker}`} checked={!excluded.includes(row.ticker)} onChange={e => {setExcluded(e.target.checked ? excluded.filter(t => t !== row.ticker) : [...excluded, row.ticker]); edit();}}/><strong>{row.ticker}</strong></label><p className="mt-1 text-xs">{row.name}</p><Link className="mt-2 block text-xs text-brand-800 underline" href={`/research?ticker=${encodeURIComponent(row.ticker)}&name=${encodeURIComponent(row.name)}`}>Start research</Link></th>{metrics.map(([key]) => <td className="p-3 tabular-nums" key={key}>{fmt(row[key])}</td>)}<td className="p-3">{fmt(row.market_cap)} {row.provenance.currency}</td><td className="p-3">{fmt(row.revenue_growth)}</td><td className="p-3">{fmt(row.profit_margin)}</td><td className="p-3 text-left text-xs leading-5">Financial period: {row.provenance.financial_period_end ? new Date(row.provenance.financial_period_end * 1000).toISOString().slice(0, 10) : 'unavailable'}<br/>Fetched: {row.provenance.fetched_at}<br/>Financial currency: {row.provenance.financial_currency || 'unavailable'}</td></tr>)}</tbody></table></div>
        <p className="text-xs leading-5 text-slate-600">{data.methodology} {selected.length} eligible peers selected. Verify forecast and accounting periods before using implied values.</p>
        <details className="border-t border-slate-300 pt-5"><summary className="cursor-pointer text-lg font-semibold">Apply peer multiples to a target company</summary><div className="mt-5 space-y-4"><p className="text-sm text-slate-600">Enter a verified measure consistent with the multiple. These are your assumptions; target financials are not inferred from peers.</p><div className="grid gap-4 sm:grid-cols-2"><label className="text-xs font-medium">Target currency<input className={fieldClass} maxLength={3} value={currency} onChange={e => {setCurrency(e.target.value.toUpperCase()); edit();}}/></label><label className="text-xs font-medium">{metric === 'ev_ebitda' ? 'Target EBITDA (millions)' : metric === 'price_book' ? 'Target book value per share' : 'Target earnings per share'}<input type="number" step="any" className={fieldClass} value={target ?? ''} onChange={e => {setTarget(e.target.value === '' ? null : Number(e.target.value)); edit();}}/></label>{metric === 'ev_ebitda' && <><label className="text-xs font-medium">Net debt and other equity claims (millions)<input type="number" step="any" className={fieldClass} value={debt ?? ''} onChange={e => {setDebt(e.target.value === '' ? null : Number(e.target.value)); edit();}}/></label><label className="text-xs font-medium">Diluted shares (millions)<input type="number" step="any" className={fieldClass} value={shares ?? ''} onChange={e => {setShares(e.target.value === '' ? null : Number(e.target.value)); edit();}}/></label></>}</div><button disabled={!selected.length} className={primaryClass} onClick={value}>Calculate relative value</button></div></details>
      </>}
    </fieldset>
    {result && <section className="space-y-4 border-t border-slate-300 pt-5"><h2 className="text-xl font-semibold">Peer-implied value</h2><table className="w-full text-left text-sm"><thead><tr><th className="p-3">Peer percentile</th><th className="p-3">Multiple</th><th className="p-3">{currency} per share</th></tr></thead><tbody>{(['p25', 'median', 'p75'] as const).map(key => <tr className="border-t border-slate-200" key={key}><th className="p-3 font-medium">{key === 'median' ? 'Median' : key === 'p25' ? '25th percentile' : '75th percentile'}</th><td className="p-3">{fmt(result.multiples[key])}×</td><td className="p-3">{fmt(result.prices[key])}</td></tr>)}</tbody></table><p className="text-xs leading-5 text-slate-600">{result.methodology}</p></section>}
  </section>;
}
