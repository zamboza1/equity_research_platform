'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import api from '@/utils/api';
import { TrendingUp, Activity, Percent, BarChart3, Loader2 } from 'lucide-react';
import clsx from 'clsx';

export default function AdvancedMacro() {
    const [yieldCurve, setYieldCurve] = useState<any[]>([]);
    const [unemploymentData, setUnemploymentData] = useState<any[]>([]);
    const [cpiData, setCpiData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>({
        spread_10y_2y: -0.35,
        fed_funds: 5.33,
        cpi_yoy: 3.1
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [curveRes, usRes] = await Promise.all([
                    api.get('/macro/yield-curve'),
                    api.get('/macro/us')
                ]);

                setYieldCurve(curveRes.data);
                setStats((prev: typeof stats) => ({
                    ...prev,
                    spread_10y_2y: usRes.data.spread_10y_2y,
                    fed_funds: usRes.data.fed_funds,
                    cpi_yoy: usRes.data.cpi_yoy
                }));

                // Set historical data for charts
                setUnemploymentData(usRes.data.unemployment || []);
                setCpiData(usRes.data.cpi || []);

                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch macro data:", err);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) return (
        <div className="h-64 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
    );

    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Yield Curve Card */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="lg:col-span-2 bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h3 className="text-xl font-black text-slate-900 tracking-tight flex items-center">
                                <TrendingUp className="w-5 h-5 mr-3 text-brand-500" />
                                US Treasury Yield Curve
                            </h3>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Real-time benchmark yields</p>
                        </div>
                        <div className={clsx(
                            "px-4 py-2 rounded-2xl text-white text-[10px] font-black uppercase tracking-widest",
                            stats.spread_10y_2y < 0 ? "bg-red-600" : "bg-green-600"
                        )}>
                            {stats.spread_10y_2y < 0 ? "Inverted" : "Normal"}: {stats.spread_10y_2y.toFixed(2)} bps
                        </div>
                    </div>

                    <div className="h-72 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={yieldCurve}>
                                <defs>
                                    <linearGradient id="colorYield" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#637be6" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#637be6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="tenor" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} tickFormatter={v => `${v.toFixed(1)}%`} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    formatter={(v: any) => [`${v.toFixed(2)}%`, 'Yield']}
                                />
                                <Area type="monotone" dataKey="value" stroke="#637be6" strokeWidth={4} fillOpacity={1} fill="url(#colorYield)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Macro Indicators */}
                <div className="space-y-6">
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="bg-brand-600 p-8 rounded-[2.5rem] text-white shadow-xl shadow-brand-100">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 bg-white/10 rounded-2xl flex items-center justify-center">
                                <Percent className="w-5 h-5 text-brand-200" />
                            </div>
                            <h4 className="text-sm font-black uppercase tracking-widest">Key Policy Rates</h4>
                        </div>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center py-2 border-b border-brand-400/30">
                                <span className="text-xs font-bold text-brand-100">Fed Funds Rate</span>
                                <span className="text-xl font-black">{stats.fed_funds.toFixed(2)}%</span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                                <span className="text-xs font-bold text-brand-100">CPI YoY (Inflation)</span>
                                <span className="text-xl font-black">{stats.cpi_yoy}%</span>
                            </div>
                        </div>
                    </motion.div>

                    <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm">
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Inversion Alert</h4>
                        <div className="space-y-3">
                            <div className="p-3 bg-slate-50 rounded-2xl">
                                <p className="text-[10px] font-black text-slate-500 uppercase mb-1">10Y-2Y Spread</p>
                                <p className="text-2xl font-black text-slate-900">{stats.spread_10y_2y.toFixed(2)} bps</p>
                                <p className="text-[9px] font-bold text-slate-400 mt-2">
                                    {stats.spread_10y_2y < 0 ? "⚠️ Yield curve inverted - historically signals recession" : "✓ Normal yield curve shape"}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Economic Indicators Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Unemployment Chart */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
                    <div className="mb-6">
                        <h3 className="text-xl font-black text-slate-900 tracking-tight flex items-center">
                            <Activity className="w-5 h-5 mr-3 text-amber-500" />
                            Unemployment Rate
                        </h3>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">US Labor Market Trend</p>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={unemploymentData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} tickFormatter={v => `${v.toFixed(1)}%`} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    formatter={(v: any) => [`${v.toFixed(2)}%`, 'Unemployment']}
                                    labelFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                                />
                                <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={3} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* CPI Chart */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-100">
                    <div className="mb-6">
                        <h3 className="text-xl font-black text-slate-900 tracking-tight flex items-center">
                            <BarChart3 className="w-5 h-5 mr-3 text-rose-500" />
                            Consumer Price Index
                        </h3>
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Inflation Measure (Index Level)</p>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={cpiData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 'bold' }} domain={[310, 320]} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '1rem', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    formatter={(v: any) => [v.toFixed(2), 'CPI Index']}
                                    labelFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                                />
                                <Line type="monotone" dataKey="value" stroke="#f43f5e" strokeWidth={3} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
