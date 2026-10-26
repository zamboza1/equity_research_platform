'use client';
import {useEffect, useRef, useState} from 'react';
import api, {errorMessage} from '@/utils/api';
import {type NAVDraft, type NAVMode, restoreNAVDraft, saveNAVDraft} from '@/utils/navDraft';

type NAVResult = {gross_asset_value?:number; reserve_value?:number; net_asset_value:number; nav_per_share:number};
const labels:Record<string,string> = {noi:'Annual NOI (M)', cap_rate:'Capitalization rate (decimal)', other_assets:'Other assets (M)', total_debt:'Debt (M)', minority_interest:'Minority interest (M)', preferred_equity:'Preferred equity (M)', shares_outstanding:'Diluted shares (M)', reserves:'Reserves (M units)', value_per_unit:'Value per reserve unit', production_cost_per_unit:'Production cost per unit', exploration_upside:'Exploration value (M)', liabilities:'Liabilities (M)'};
const modes:NAVMode[] = ['real-estate', 'resource'];
const draftButton = 'rounded-lg border bg-white px-3 py-2 text-sm disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600';

export default function AdvancedNAV({draft, onDraftChange}:{draft:NAVDraft; onDraftChange:(draft:NAVDraft)=>void}) {
    const [result,setResult] = useState<NAVResult|null>(null);
    const [busy,setBusy] = useState(false);
    const [error,setError] = useState('');
    const [notice,setNotice] = useState('');
    const request = useRef<AbortController|null>(null);
    useEffect(() => () => request.current?.abort(), []);
    const {mode,real,resource} = draft;
    const values = mode === 'real-estate' ? real : resource;

    function update(next:NAVDraft) {
        onDraftChange(next);
        setResult(null);
        setError('');
        setNotice('');
    }

    function save() {
        setError('');
        setNotice('');
        try {
            saveNAVDraft(window.localStorage, draft);
            setNotice('Both NAV drafts saved in this browser.');
        } catch {
            setError('Browser storage is unavailable or full. NAV drafts were not saved; your current inputs are still available on this page.');
        }
    }

    function restore() {
        setError('');
        setNotice('');
        try {
            update(restoreNAVDraft(window.localStorage));
            setNotice('Both NAV drafts restored. Calculate NAV to refresh the results.');
        } catch (err) {
            setError(err instanceof DOMException
                ? 'Browser storage is unavailable. NAV drafts could not be restored; your current inputs are unchanged.'
                : errorMessage(err));
        }
    }

    return <section className="space-y-5">
        <div className="rounded-2xl bg-slate-900 p-6 text-white">
            <h2 className="text-2xl font-semibold">Net asset value</h2>
            <p className="mt-2 text-sm text-slate-300">Review every asset value and claim. Initial inputs are illustrative; use one currency throughout.</p>
        </div>
        <div className="flex flex-wrap gap-2">{modes.map(m => <button disabled={busy} key={m} aria-pressed={mode===m} onClick={()=>update({...draft,mode:m})} className={`rounded-lg px-4 py-2 text-sm ${mode===m?'bg-brand-600 text-white':'border bg-white'}`}>{m==='real-estate'?'Real estate':'Resources'}</button>)}</div>
        <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
                <button disabled={busy} className={draftButton} onClick={save}>Save NAV drafts</button>
                <button disabled={busy} className={draftButton} onClick={restore}>Restore NAV drafts</button>
            </div>
            <p className="text-xs leading-5 text-slate-500">Both drafts stay available when switching models on this page. Save before reloading or leaving. Saving replaces the previous NAV drafts in this browser; restoring replaces your current inputs. Results are recalculated, not saved.</p>
        </div>
        {notice && <p role="status" className="text-sm text-brand-800">{notice}</p>}
        {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
        <form onSubmit={async e=>{
            e.preventDefault();
            const controller = new AbortController();
            request.current = controller;
            setBusy(true); setError(''); setNotice(''); setResult(null);
            try {
                const {data} = await api.post<NAVResult>(`/valuation/nav/${mode}`, values, {signal:controller.signal});
                if (!controller.signal.aborted) setResult(data);
            } catch (err) {
                if (!controller.signal.aborted) setError(errorMessage(err));
            } finally {
                if (!controller.signal.aborted) setBusy(false);
            }
        }}>
            <fieldset disabled={busy} className="rounded-2xl border bg-white p-6">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(values).map(([k,v])=><label key={k} className="text-xs text-slate-600">{labels[k]}
                    <input aria-label={labels[k]} className="mt-1 w-full rounded-lg border px-3 py-2 text-sm" type="number" step="any" required value={v ?? ''} onChange={e=>{
                        const value = Number.isFinite(e.target.valueAsNumber) ? e.target.valueAsNumber : null;
                        update(mode==='real-estate' ? {...draft,real:{...real,[k]:value}} : {...draft,resource:{...resource,[k]:value}});
                    }}/>
                </label>)}</div>
                <p className="mt-5 text-xs text-slate-500">{mode==='real-estate'?'Property value = annual NOI ÷ cap rate. Equity NAV deducts debt, minority interest and preferred equity.':'Resource value = reserves × (unit value − unit production cost). This simplified asset estimate excludes production timing and discounting; it is not a reserve cash-flow model.'}</p>
                <button className="mt-5 rounded-lg bg-brand-600 px-5 py-3 font-semibold text-white" type="submit">{busy?'Calculating…':'Calculate NAV'}</button>
            </fieldset>
        </form>
        {result && <div data-testid="nav-results" className="grid gap-4 rounded-2xl border bg-white p-6 sm:grid-cols-3">{[
            ['Asset value (M)',result.gross_asset_value??result.reserve_value], ['Equity NAV (M)',result.net_asset_value], ['NAV per share',result.nav_per_share],
        ].map(([label,value])=><div key={label}><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold">{Number(value).toLocaleString(undefined,{maximumFractionDigits:2})}</p></div>)}</div>}
    </section>;
}
