'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Landmark, AlertCircle, Loader2 } from 'lucide-react';
import api from '@/utils/api';
import clsx from 'clsx';

export default function NAVModel() {
    const [ticker, setTicker] = useState('BXP'); // Boston Properties as default REIT
    const [assets, setAssets] = useState(25000);
    const [liabilities, setLiabilities] = useState(15000);
    const [shares, setShares] = useState(157);
    const [price, setPrice] = useState(75.50);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

    const runModel = async () => {
        setLoading(true);
        setError('');
        try {
            const res = await api.post('/valuation/nav', null, {
                params: {
                    ticker,
                    assets,
                    liabilities,
                    shares_out: shares,
                    current_price: price
                }
            });
            setResult(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error calculating NAV');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-slate-100"
            >
                <h2 className="text-xl font-bold mb-4 flex items-center space-x-2">
                    <Landmark className="w-5 h-5 text-amber-600" />
                    <span>NAV Assumptions</span>
                </h2>

                <div className="space-y-4">
                    <div>
                        <label htmlFor="navmodel-0" className="block text-sm font-medium text-slate-700 mb-1">Ticker</label>
                        <input id="navmodel-0"
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 outline-none uppercase font-mono"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="navmodel-1" className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Assets ($M)</label>
                            <input id="navmodel-1"
                                type="number"
                                value={assets}
                                onChange={(e) => setAssets(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-1 focus:ring-amber-500"
                            />
                        </div>
                        <div>
                            <label htmlFor="navmodel-2" className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Total Liabilities ($M)</label>
                            <input id="navmodel-2"
                                type="number"
                                value={liabilities}
                                onChange={(e) => setLiabilities(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-1 focus:ring-amber-500"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="navmodel-3" className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Shares Out. (M)</label>
                            <input id="navmodel-3"
                                type="number"
                                value={shares}
                                onChange={(e) => setShares(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-1 focus:ring-amber-500"
                            />
                        </div>
                        <div>
                            <label htmlFor="navmodel-4" className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Current Price ($)</label>
                            <input id="navmodel-4"
                                type="number"
                                value={price}
                                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-1 focus:ring-amber-500"
                            />
                        </div>
                    </div>

                    <button
                        onClick={runModel}
                        disabled={loading}
                        className="w-full py-4 bg-slate-900 border border-slate-800 text-white font-black uppercase tracking-widest text-xs rounded-2xl flex items-center justify-center space-x-2 shadow-lg hover:bg-slate-800 transition-all disabled:opacity-70"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>Execute NAV Engine</span>}
                    </button>

                    {error && (
                        <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center space-x-2">
                            <AlertCircle className="w-4 h-4" />
                            <span>{error}</span>
                        </div>
                    )}
                </div>
            </motion.div>

            <div className="lg:col-span-2">
                {result ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 h-full flex flex-col justify-center"
                    >
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h3 className="text-sm font-black text-slate-400 uppercase tracking-[0.2em]">Valuation Output</h3>
                                <p className="text-3xl font-black text-slate-900 mt-1">{ticker} Asset-Based Value</p>
                            </div>
                            <div className={clsx(
                                "px-6 py-2 rounded-full text-sm font-black uppercase tracking-widest",
                                result.upside > 0 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                            )}>
                                {result.upside.toFixed(1)}% {result.upside > 0 ? 'Discount' : 'Premium'} to NAV
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="p-6 bg-slate-50 rounded-3xl border border-slate-100">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">NAV per Share</p>
                                <p className="text-4xl font-black text-brand-600">${result.nav_per_share.toFixed(2)}</p>
                            </div>
                            <div className="p-6 bg-amber-50 rounded-3xl border border-amber-100">
                                <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest mb-2">Net Asset Value</p>
                                <p className="text-2xl font-black text-slate-900">${(result.net_asset_value / 1000).toFixed(1)}B</p>
                            </div>
                            <div className="p-6 bg-slate-100 rounded-3xl border border-slate-200">
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Loan to Value (LTV)</p>
                                <p className="text-2xl font-black text-slate-900">{((result.liabilities / result.assets) * 100).toFixed(1)}%</p>
                            </div>
                        </div>

                        <div className="mt-8 p-6 bg-slate-900 rounded-3xl text-white">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Summary Conclusion</p>
                            <p className="text-sm leading-relaxed text-slate-300">
                                Based on fair market value of <span className="text-white font-bold">${(result.assets / 1000).toFixed(1)}B</span> in assets and <span className="text-white font-bold">${(result.liabilities / 1000).toFixed(1)}B</span> in liabilities,
                                the implied intrinsic value of equity is <span className="text-amber-400 font-bold">${(result.net_asset_value / 1000).toFixed(1)}B</span>.
                                {result.upside > 0
                                    ? ` At a current market price of $${price}, the stock is trading at a significant discount to its underlying asset base.`
                                    : ` The current market price suggests a premium valuation relative to the liquidation value of its assets.`}
                            </p>
                        </div>
                    </motion.div>
                ) : (
                    <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl h-full flex flex-col items-center justify-center p-12 text-center">
                        <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-4">
                            <Landmark className="w-8 h-8 text-slate-300" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900">Ready for NAV Calculation</h3>
                        <p className="text-sm text-slate-500 max-w-xs mt-2">Enter asset and liability fair values from the latest balance sheet to estimate the net liquidation value.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
