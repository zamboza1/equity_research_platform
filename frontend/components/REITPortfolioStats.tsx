'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Map, Activity, Clock } from 'lucide-react';

export default function REITPortfolioStats({ analytics }: { analytics: any }) {
    if (!analytics) return null;

    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Lease Expiry Wall */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h3 className="text-xl font-black text-slate-900 tracking-tight flex items-center">
                                <Clock className="w-5 h-5 mr-3 text-brand-500" />
                                Lease Expiry Schedule
                            </h3>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Portfolio rent at risk by year</p>
                        </div>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={analytics.lease_expiry_schedule}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                                <Tooltip
                                    cursor={{ fill: '#f8fafc' }}
                                    contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    formatter={(val: number) => [`${(val * 100).toFixed(1)}%`, '% of Portfolio']}
                                />
                                <Bar dataKey="pct_of_portfolio" radius={[6, 6, 0, 0]}>
                                    {analytics.lease_expiry_schedule.map((entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={entry.year === 2024 ? '#f43f5e' : '#637be6'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 flex items-center justify-center space-x-6 text-[10px] font-black uppercase tracking-widest text-slate-400">
                        <div className="flex items-center"><div className="w-2 h-2 bg-rose-500 rounded-full mr-2" /> Current Year Risk</div>
                        <div className="flex items-center"><div className="w-2 h-2 bg-brand-500 rounded-full mr-2" /> Future Expiries</div>
                    </div>
                </motion.div>

                {/* Geographic / Concentration */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, x: 0 }} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h3 className="text-xl font-black text-slate-900 tracking-tight flex items-center">
                                <Map className="w-5 h-5 mr-3 text-emerald-500" />
                                Geographic Concentration
                            </h3>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">% of NOI by Region</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {analytics.geographic_concentration.map((item: any, idx: number) => (
                            <div key={idx} className="group">
                                <div className="flex items-center justify-between text-xs font-bold mb-2">
                                    <span className="text-slate-600 group-hover:text-brand-600 transition-colors uppercase">{item.region}</span>
                                    <span className="text-slate-900">{(item.pct_of_noi * 100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full h-2 bg-slate-50 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${item.pct_of_noi * 100}%` }}
                                        className="h-full bg-emerald-500 rounded-full group-hover:bg-brand-500 transition-all"
                                    />
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="mt-8 p-6 bg-slate-50 rounded-3xl flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center">
                                <Activity className="w-5 h-5 text-brand-500" />
                            </div>
                            <div>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">WALT</p>
                                <p className="text-lg font-black text-slate-900">7.2 Years</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Diversification Score</p>
                            <p className="text-lg font-black text-emerald-600">Strong</p>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
