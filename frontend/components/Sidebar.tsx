'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {useState} from 'react';

const items = [
  ['Dashboard', '/'], ['Research desk', '/research'],
  ['Valuations', '/analysis/valuation'], ['Model builder', '/builder'],
  ['Comparables', '/analysis/comparables'], ['Macro data', '/analysis/macro'],
  ['Quant statistics', '/analysis/stats'], ['Industry notes', '/industries'],
  ['Sector research', '/sectors/real-estate'], ['Research primers', '/education']
] as const;

export default function Sidebar() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return <>
    {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/30 md:hidden" onClick={() => setOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-slate-700 bg-brand-dark text-white ${open ? 'w-[240px]' : 'w-16'} md:w-[240px]`}>
      <button aria-expanded={open} aria-controls="primary-navigation" className="m-2 rounded border border-slate-500 px-1 py-3 text-xs focus-visible:outline-2 focus-visible:outline-offset-2 md:hidden" onClick={() => setOpen(!open)}>{open ? 'Close menu' : 'Menu'}</button>
      <div className={`${open ? 'block' : 'hidden'} px-6 pb-7 pt-6 md:block md:pt-9`}>
        <p className="text-xl tracking-[.2em]">VERTIGE</p>
        <p className="mt-2 border-t border-secondary/60 pt-3 text-xs tracking-wide text-slate-300">Research workspace</p>
      </div>
      <nav id="primary-navigation" aria-label="Main navigation" className={`${open ? 'block' : 'hidden'} flex-1 space-y-1 overflow-auto px-3 md:block`}>
        {items.map(([name, url]) => {
          const active = path === url || (url !== '/' && path.startsWith(url + '/'));
          return <Link key={url} href={url} aria-current={active ? 'page' : undefined} onClick={() => setOpen(false)} className={`block rounded px-3 py-3 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 ${active ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}>{name}</Link>;
        })}
      </nav>
      <p className={`${open ? 'block' : 'hidden'} border-t border-slate-700 p-6 text-xs leading-5 text-slate-400 md:block`}>Local research workspace.<br/>Verify inputs and source dates.</p>
    </aside>
  </>;
}
