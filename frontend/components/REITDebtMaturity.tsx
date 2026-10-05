'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Landmark, ShieldCheck } from 'lucide-react';

export default function REITDebtMaturity({ analytics }: { analytics: any }) {
    if (!analytics) return null;

    // Transform for Recharts (Pivot by type if needed, but here simple mapping)
    const chartData = analytics.debt_maturity_wall.map((item: any) => ({
        year: item.year,
        fixed: item.type === 'Fixed' ? item.amount : 0,
        floating: item.type === 'Floating' ? item.amount : 0,
        total: item.amount
    }));

    return (
        <div className="bg-[#0F172A] p-8 rounded-[3rem] text-white shadow-2xl relative overflow-hidden">
            <div className="relative z-10">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <h3 className="text-xl font-black tracking-tight flex items-center">
                            <Landmark className="w-6 h-6 mr-3 text-amber-400" />
                            Capital Structure Maturity Wall
                        </h3>
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Debt refinancing schedule ($ Millions)</p>
                    </div>
                    <div className="hidden md:flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-brand-500 rounded-full" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase">Fixed</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-amber-500 rounded-full" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase">Floating</span>
                        </div>
                    </div>
                </div>

                <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                            <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold', fill: '#64748b' }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold', fill: '#64748b' }} tickFormatter={v => `$${v}M`} />
                            <Tooltip
                                cursor={{ fill: '#1e293b' }}
                                contentStyle={{ backgroundColor: '#0F172A', borderRadius: '1rem', border: '1px solid #334155', boxShadow: 'none' }}
                                itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                            />
                            <Bar dataKey="fixed" stackId="a" fill="#637be6" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="floating" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-6 bg-white/5 rounded-3xl border border-white/10">
                        <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2">Unencumbered Assets</p>
                        <p className="text-2xl font-black text-white">{(analytics.operating_metrics.unencumbered_assets_pct * 100).toFixed(1)}%</p>
                    </div>
                    <div className="p-6 bg-white/5 rounded-3xl border border-white/10">
                        <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2">Refinancing Risk</p>
                        <div className="flex items-center space-x-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-500" />
                            <p className="text-2xl font-black text-white">Low</p>
                        </div>
                    </div>
                    <div className="p-6 bg-brand-500/10 rounded-3xl border border-brand-500/20">
                        <p className="text-[9px] font-black text-brand-400 uppercase tracking-widest mb-2">Avg Debt Maturity</p>
                        <p className="text-2xl font-black text-white">5.8 Years</p>
                    </div>
                </div>
            </div>
            {/* Background Glows */}
            <div className="absolute -top-24 -left-24 w-64 h-64 bg-brand-600/10 rounded-full blur-3xl" />
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-amber-600/10 rounded-full blur-3xl" />
        </div>
    );
}
