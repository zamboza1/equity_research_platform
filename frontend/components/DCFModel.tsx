'use client';
import { useState } from 'react';
import api, { errorMessage } from '@/utils/api';
import { TrendingUp, Download, Save, FolderOpen, RefreshCw } from 'lucide-react';

type Assumptions = {
  ticker:string; currency:string; current_price:number; start_revenue_m:number; shares_outstanding_m:number;
  net_debt_m:number; growth_rates:number[]; ebit_margins:number[]; years:number; tax_rate:number;
  da_pct:number; capex_pct:number; nwc_pct:number; nwc_treatment:"balance_ratio"; wacc:number; terminal_growth:number;
  terminal_method:'GORDON'|'EXIT_MULTIPLE'; exit_multiple:number; exit_multiple_basis:'EBIT'|'EBITDA';
  run_monte_carlo:boolean; iterations:number; simulation_seed:number; simulation_wacc_sd:number; simulation_growth_sd:number;
  discount_timing:'year_end'|'mid_year'; minority_interest_m:number; preferred_equity_m:number; nonoperating_assets_m:number;
};
const example:Assumptions={ticker:'EXAMPLE',currency:'USD',current_price:25,start_revenue_m:1000,
  shares_outstanding_m:100,net_debt_m:200,growth_rates:[.08,.06,.05,.04,.03],ebit_margins:[.2,.21,.22,.22,.22],years:5,
  tax_rate:.25,da_pct:.03,capex_pct:.04,nwc_pct:.12,nwc_treatment:"balance_ratio",wacc:.1,terminal_growth:.025,terminal_method:'GORDON',
  run_monte_carlo:false,iterations:1000,simulation_seed:42,simulation_wacc_sd:.005,simulation_growth_sd:.01,exit_multiple:12,exit_multiple_basis:'EBITDA',discount_timing:'year_end',minority_interest_m:0,preferred_equity_m:0,nonoperating_assets_m:0};
type Result = { implied_price:number; current_price:number; upside:number; enterprise_value:number; equity_value:number;
  simulation_accepted:number|null;simulation_rejected:number|null;mean_price:number|null;confidence_interval:number[]|null;terminal_value_share_pct:number|null; currency:string; warnings:string[]; bridge:Record<string,number>;
  forecast:Array<{year:number;revenue:number;ebit:number;depreciation:number;capex:number;change_nwc:number;fcff:number;pv_fcff:number}> };
type Grid={wacc_values:number[];growth_values:number[];prices:(number|null)[][]};
const format=(n:number)=>n.toLocaleString(undefined,{maximumFractionDigits:2});
const inputStyle='mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500';
const buttonStyle='inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50';
export default function DCFModel(){
  const [a,setA]=useState<Assumptions>(example);
  const [result,setResult]=useState<Result|null>(null),[grid,setGrid]=useState<Grid|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('Illustrative inputs. Replace them with verified company data.');
  const [source,setSource]=useState<any>({source:'Analyst input / illustrative example'});
  const [pasteImport,setPasteImport]=useState(false),[importText,setImportText]=useState('');
  const update=(key:keyof Assumptions,value:any)=>{setA(old=>({...old,[key]:value}));setResult(null);setGrid(null);setNotice('Inputs changed. Calculate to refresh the results.');};
  const number=(key:keyof Assumptions,label:string,percent=false)=><label className="block text-xs font-medium text-slate-600" key={key}>{label}<input aria-label={label} className={inputStyle} type="number" step="any" required value={Number.isFinite(a[key])?Number(a[key])*(percent?100:1):''} onChange={e=>update(key,e.target.value===''?NaN:Number(e.target.value)/(percent?100:1))}/></label>;
  async function run(){
    setBusy(true);setError('');setResult(null);setGrid(null);
    try{
      const {data}=await api.post('/valuation/dcf',a);setResult(data);
      if(a.terminal_method==='GORDON'){
        const {data:g}=await api.post('/valuation/dcf/sensitivity',{assumptions:a,wacc_values:[-.02,-.01,0,.01,.02].map(x=>a.wacc+x),growth_values:[-.01,-.005,0,.005,.01].map(x=>a.terminal_growth+x)});setGrid(g);
      }
      setNotice('Calculated from the assumptions shown below.');
    }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  async function fetchData(){
    setBusy(true);setError('');setResult(null);setGrid(null);
    try{const {data}=await api.get(`/market/${encodeURIComponent(a.ticker)}`);
      setA(old=>({...old,ticker:data.ticker,currency:data.currency,current_price:data.current_price,start_revenue_m:data.start_revenue_m,shares_outstanding_m:data.shares_outstanding_m,net_debt_m:data.net_debt_m}));
      setSource(data.provenance);setNotice(data.warnings.join(' '));
    }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  const snapshot=()=>({version:1,assumptions:a,provenance:source,saved_at:new Date().toISOString()});
  async function load(saved:any){
    if(saved?.version!==1||!saved.assumptions||saved.assumptions.nwc_treatment!=='balance_ratio'||!Array.isArray(saved.assumptions.growth_rates))throw new Error('This is not a Vertige valuation case.');
    const {data}=await api.post('/valuation/dcf',saved.assumptions);
    setA({...example,...saved.assumptions});setSource(saved.provenance||{source:'Imported analyst case'});setResult(data);setGrid(null);setNotice('Saved assumptions restored and recalculated.');
  }
  const download=(data:unknown,name:string)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=name;link.click();URL.revokeObjectURL(url);};
  return <section className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-slate-900 p-6 text-white"><div><p className="text-xs uppercase tracking-widest text-brand-300">Valuation workspace</p><h2 className="mt-2 text-2xl font-semibold">Discounted cash flow</h2><p className="mt-2 max-w-2xl text-sm text-slate-300">Project operating cash flows, inspect assumptions, and reconcile enterprise value to equity value.</p></div><TrendingUp className="h-8 w-8 text-brand-300"/></div>
    <div role="status" className="rounded-xl border border-brand-100 bg-brand-50 p-4 text-sm text-brand-950">{notice}</div>
    {error&&<div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
    <div className="flex flex-wrap gap-2">
      <button className={buttonStyle} disabled={busy} onClick={()=>{try{localStorage.setItem('vertige-dcf-v1',JSON.stringify(snapshot()));setNotice('Case saved in this browser. Export a copy for backup.');}catch{setError('Browser storage is unavailable. Export the case instead.');}}}><Save size={16}/>Save case</button>
      <button className={buttonStyle} disabled={busy} onClick={async()=>{setBusy(true);setError('');try{const saved=localStorage.getItem('vertige-dcf-v1');if(!saved)throw new Error('No saved case in this browser.');await load(JSON.parse(saved));}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}}><FolderOpen size={16}/>Restore case</button>
      <button className={buttonStyle} disabled={busy} onClick={()=>download(snapshot(),'vertige-case.json')}><Download size={16}/>Export case</button>
      <label className={buttonStyle}>Import case<input aria-label="Import valuation case" type="file" accept=".json" className="max-w-40 text-xs" disabled={busy} onChange={async e=>{const f=e.target.files?.[0];if(!f)return;setBusy(true);setError('');try{if(f.size>200000)throw new Error('Case file is too large.');await load(JSON.parse(await f.text()));}catch(err){setError(errorMessage(err));}finally{setBusy(false);e.target.value='';}}}/></label>
      <button className={buttonStyle} disabled={busy} onClick={()=>setPasteImport(!pasteImport)}>Paste case JSON</button>
    </div>
    {pasteImport&&<form className="space-y-3 border-y border-slate-200 py-4" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{await load(JSON.parse(importText));setPasteImport(false);}catch(err){setError(errorMessage(err));}finally{setBusy(false);}}}><label className="block text-sm">Valuation case JSON<textarea disabled={busy} required maxLength={200000} className={inputStyle+' h-32 font-mono text-xs'} value={importText} onChange={e=>setImportText(e.target.value)}/></label><button disabled={busy} className={buttonStyle}>Import and recalculate case</button></form>}
    <form onSubmit={e=>{e.preventDefault();run();}}>
    <fieldset disabled={busy} className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="font-semibold">Company and capital structure</h3><p className="mt-1 text-xs text-slate-500">All money in millions of the selected currency. Shares in millions. Price in currency per share.</p>
        <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <label className="text-xs font-medium text-slate-600">Ticker<input aria-label="Ticker" className={inputStyle} value={a.ticker} onChange={e=>update('ticker',e.target.value.toUpperCase())}/></label>
          <label className="text-xs font-medium text-slate-600">Currency<input aria-label="Currency" className={inputStyle} maxLength={3} value={a.currency} onChange={e=>update('currency',e.target.value.toUpperCase())}/></label>
          {number('current_price','Share price')}{number('shares_outstanding_m','Diluted shares (M)')}
          {number('start_revenue_m','Base revenue (M)')}{number('net_debt_m','Net debt (M)')}{number('minority_interest_m','Minority interest (M)')}{number('preferred_equity_m','Preferred equity (M)')}{number('nonoperating_assets_m','Nonoperating assets (M)')}
        </div>
        <button type="button" className={`${buttonStyle} mt-4`} onClick={fetchData}><RefreshCw size={15}/>Fetch provider inputs</button>
        <p className="mt-3 text-xs text-slate-500">Source: {source.source}{source.fetched_at?` · fetched ${new Date(source.fetched_at).toLocaleString()}`:''}. Check financial period and fully diluted shares; edited values are analyst overrides.</p>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6"><h3 className="font-semibold">Operating assumptions</h3>
          <div className="mt-4 grid grid-cols-2 gap-4">{number('tax_rate','Tax rate (%)',true)}{number('da_pct','D&A / revenue (%)',true)}{number('capex_pct','Capex / revenue (%)',true)}{number('nwc_pct','NWC / revenue (%)',true)}</div>
          <label className="mt-4 block text-xs font-medium text-slate-600">Forecast years<input aria-label="Forecast years" className={inputStyle} type="number" min={1} max={30} value={a.years} onChange={e=>{const n=Math.max(1,Math.min(30,Number(e.target.value)||1));setA(old=>({...old,years:n,growth_rates:Array.from({length:n},(_,i)=>old.growth_rates[i]??.03),ebit_margins:Array.from({length:n},(_,i)=>old.ebit_margins[i]??.2)}));setResult(null);setGrid(null);}}/></label>
          <div className="mt-4 max-h-72 overflow-auto"><table className="w-full text-sm"><thead><tr className="text-left text-xs text-slate-500"><th>Year</th><th>Revenue growth %</th><th>EBIT margin %</th></tr></thead><tbody>{a.growth_rates.map((g,i)=><tr key={i}><td>{i+1}</td>{(['growth_rates','ebit_margins'] as const).map(k=><td key={k} className="p-1"><input className={inputStyle} aria-label={`${k==='growth_rates'?'Growth':'Margin'} year ${i+1}`} type="number" step="any" required value={Number.isFinite(a[k][i])?a[k][i]*100:''} onChange={e=>{const values=[...a[k]];values[i]=e.target.value===''?NaN:Number(e.target.value)/100;update(k,values);}}/></td>)}</tr>)}</tbody></table></div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6"><h3 className="font-semibold">Discounting and terminal value</h3><div className="mt-4 grid grid-cols-2 gap-4">
          {number('wacc','WACC (%)',true)}{number('terminal_growth','Terminal growth (%)',true)}
          <label className="text-xs font-medium text-slate-600">Terminal method<select aria-label="Terminal method" className={inputStyle} value={a.terminal_method} onChange={e=>update('terminal_method',e.target.value)}><option value="GORDON">Perpetual growth</option><option value="EXIT_MULTIPLE">Exit multiple</option></select></label>
          <label className="text-xs font-medium text-slate-600">Cash flow timing<select aria-label="Cash flow timing" className={inputStyle} value={a.discount_timing} onChange={e=>update('discount_timing',e.target.value)}><option value="year_end">Year end</option><option value="mid_year">Mid year</option></select></label>
          {a.terminal_method==='EXIT_MULTIPLE'&&<>{number('exit_multiple','Exit multiple (x)')}<label className="text-xs font-medium text-slate-600">Multiple basis<select className={inputStyle} value={a.exit_multiple_basis} onChange={e=>update('exit_multiple_basis',e.target.value)}><option>EBIT</option><option>EBITDA</option></select></label></>}
        </div><div className="mt-6 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600"><p>FCFF = after-tax EBIT + D&A − capex − change in NWC.</p><p className="mt-2">Opening NWC equals base revenue × NWC ratio. Terminal cash flow uses the stable growth rate and final EBIT margin. Terminal value is discounted from the final year end. Losses receive no immediate tax credit.</p></div>
        <label className="mt-5 flex items-center gap-2 text-sm"><input type="checkbox" checked={a.run_monte_carlo} onChange={e=>update('run_monte_carlo',e.target.checked)}/>Run Monte Carlo scenarios</label>
        {a.run_monte_carlo&&<div className="mt-4 space-y-3"><div className="grid grid-cols-2 gap-4">{number('iterations','Simulation draws')}{number('simulation_seed','Simulation seed')}{number('simulation_wacc_sd','WACC dispersion (percentage points)',true)}{number('simulation_growth_sd','Growth dispersion (percentage points)',true)}</div><p className="text-xs leading-5 text-slate-500">Independent normal shocks to WACC and the common shift in annual growth. Dispersions are standard deviations; zero holds an input fixed. Invalid draws are excluded and counted. These distributions are analyst assumptions.</p></div>}
        <button type="submit" className="mt-6 w-full rounded-xl bg-brand-600 px-5 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-50">{busy?'Calculating…':'Calculate valuation'}</button></div>
      </div>
    </fieldset></form>
    {result&&<div className="space-y-6" data-testid="dcf-results"><div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[['Implied price',`${result.currency} ${format(result.implied_price)}`],['Share price',format(result.current_price)],['Upside / downside',`${format(result.upside)}%`],['Terminal share of EV',`${format(result.terminal_value_share_pct??0)}%`]].map(([label,value])=><div key={label} className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p></div>)}</div>
      {result.mean_price!==null&&result.confidence_interval&&<p data-testid="monte-carlo-result" className="rounded-lg bg-brand-50 p-4 text-sm text-brand-900">Scenario mean: {format(result.mean_price)} per share. P5–P95: {format(result.confidence_interval[0])}–{format(result.confidence_interval[1])}. Accepted draws: {result.simulation_accepted}; excluded: {result.simulation_rejected}. These percentiles reflect the chosen assumptions, not a statistical confidence interval.</p>}
      {result.warnings.map(w=><p key={w} className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{w}</p>)}
      <div className="overflow-auto rounded-2xl border border-slate-200 bg-white p-6"><h3 className="mb-4 font-semibold">Cash flow forecast · {result.currency} millions</h3><table className="w-full text-right text-sm tabular-nums"><thead><tr>{['Year','Revenue','EBIT','D&A','Capex','Δ NWC','FCFF','PV of FCFF'].map(x=><th key={x} className="p-2 font-medium text-slate-500">{x}</th>)}</tr></thead><tbody>{result.forecast.map(p=><tr key={p.year} className="border-t border-slate-100">{[p.year,p.revenue,p.ebit,p.depreciation,p.capex,p.change_nwc,p.fcff,p.pv_fcff].map((x,i)=><td key={i} className="p-2">{format(x)}</td>)}</tr>)}</tbody></table></div>
      <div className="rounded-2xl border border-slate-200 bg-white p-6"><h3 className="mb-4 font-semibold">Enterprise to equity bridge · millions</h3>{Object.entries(result.bridge).map(([k,v])=><div key={k} className="flex justify-between border-b border-slate-100 py-2 text-sm"><span className="capitalize">{k.replaceAll('_',' ')}</span><span className="font-mono">{format(v)}</span></div>)}</div>
      {grid&&<div className="overflow-auto rounded-2xl border border-slate-200 bg-white p-6"><h3 className="font-semibold">Price sensitivity</h3><p className="my-2 text-xs text-slate-500">Rows: terminal growth. Columns: WACC. An em dash marks an invalid rate pair.</p><table className="w-full text-right text-sm tabular-nums"><thead><tr><th>Growth / WACC</th>{grid.wacc_values.map(w=><th key={w} className="p-3">{format(w*100)}%</th>)}</tr></thead><tbody>{grid.growth_values.map((g,i)=><tr key={g} className="border-t border-slate-100"><th className="p-3">{format(g*100)}%</th>{grid.prices[i].map((v,j)=><td key={j} className={`p-3 ${i===2&&j===2?'bg-brand-50 font-semibold text-brand-800':''}`}>{v===null?'—':format(v)}</td>)}</tr>)}</tbody></table></div>}
      <button className={buttonStyle} onClick={()=>download({...snapshot(),result,sensitivity:grid},'vertige-valuation.json')}><Download size={16}/>Export valuation and assumptions</button>
    </div>}
  </section>;
}
