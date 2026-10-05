'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calculator, AlertCircle, Loader2, RefreshCw, Zap } from 'lucide-react';
import api,{errorMessage} from '@/utils/api';
import clsx from 'clsx';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

export default function DDMModel() {
    const [ticker, setTicker] = useState('KO'); // Coca-Cola as default DDM candidate
    const [currentPrice, setCurrentPrice] = useState(60.00);
    const [currentDividend, setCurrentDividend] = useState(1.92);
    const [growthRate, setGrowthRate] = useState(0.05);
    const [requiredReturn, setRequiredReturn] = useState(0.08);
    const [terminalGrowth, setTerminalGrowth] = useState(0.03);
    const [years, setYears] = useState(5);
    const [modelType, setModelType] = useState<'gordon' | 'multi'>('gordon');
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

    useEffect(()=>{setResult(null);},[ticker,currentPrice,currentDividend,growthRate,requiredReturn,terminalGrowth,years,modelType]);
    const fetchTickerData = async () => {
        setFetching(true);setResult(null);setError('');
        try {
            const res = await api.get(`/valuation/ddm/fetch-dividend-data/${ticker}`);
            setCurrentPrice(res.data.current_price);
            setCurrentDividend(res.data.current_dividend);
            setError('');
        } catch (err) {
            setError(errorMessage(err));
        } finally {
            setFetching(false);
        }
    };

    const runModel = async () => {
        setLoading(true);setResult(null);
        setError('');
        try {
            const endpoint = modelType === 'gordon' ? '/valuation/ddm/gordon' : '/valuation/ddm/multi-stage';
            const payload = {
                ticker,
                current_dividend: currentDividend,
                current_price: currentPrice,
                dividend_growth_rate: modelType === 'gordon' ? growthRate : terminalGrowth,
                required_return: requiredReturn,
                high_growth_rate: modelType === 'multi' ? growthRate : null,
                high_growth_years: modelType === 'multi' ? years : null
            };
            const res = await api.post(endpoint, payload);
            setResult({ ...res.data, intrinsic_value:res.data.intrinsic_value_per_share, upside:res.data.upside_downside_pct, current_price: currentPrice });
        } catch (err: any) {
            setError(errorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    const chartData = [
        { name: 'Market Price', value: currentPrice, color: '#94a3b8' },
        { name: 'Intrinsic Value', value: result?.intrinsic_value || 0, color: '#4f46e5' },
    ];

    return (
        <fieldset disabled={loading || fetching} className="grid min-w-0 grid-cols-1 lg:grid-cols-3 gap-6">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-slate-100"
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold flex items-center space-x-2">
                        <Calculator className="w-5 h-5 text-brand-600" />
                        <span>DDM assumptions</span>
                    </h2>
                    <div className="flex bg-slate-100 p-1 rounded-lg">
                        <button
                            onClick={() => setModelType('gordon')}
                            className={clsx("px-3 py-1 text-[10px] font-bold rounded-md transition-all", modelType === 'gordon' ? "bg-white text-brand-600 shadow-sm" : "text-slate-400")}
                        >GORDON</button>
                        <button
                            onClick={() => setModelType('multi')}
                            className={clsx("px-3 py-1 text-[10px] font-bold rounded-md transition-all", modelType === 'multi' ? "bg-white text-brand-600 shadow-sm" : "text-slate-400")}
                        >MULTI-STAGE</button>
                    </div>
                </div>

                <p className="mb-4 text-xs text-slate-500">Initial values are illustrative. Dividends and prices use the same currency per share. Growth is an analyst assumption.</p><div className="space-y-4">
                    <div className="flex items-end space-x-2">
                        <div className="flex-1">
                            <label htmlFor="ddmmodel-0" className="block text-sm font-medium text-slate-700 mb-1">Ticker</label>
                            <input id="ddmmodel-0"
                                type="text"
                                aria-label="Ticker" value={ticker}
                                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 outline-none uppercase font-mono"
                            />
                        </div>
                        <button
                            onClick={fetchTickerData}
                            aria-label="Fetch dividend inputs" disabled={fetching}
                            className="p-2.5 bg-brand-50 text-brand-600 rounded-lg hover:bg-brand-100 transition-colors"
                        >
                            {fetching ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                        </button>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="ddmmodel-1" className="block text-xs font-semibold text-slate-500 uppercase mb-1">Annual dividend per share</label>
                            <input id="ddmmodel-1"
                                type="number"
                                aria-label="Annual dividend per share" value={currentDividend}
                                onChange={(e) => setCurrentDividend(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label htmlFor="ddmmodel-2" className="block text-xs font-semibold text-slate-500 uppercase mb-1">Market price per share</label>
                            <input id="ddmmodel-2"
                                type="number"
                                aria-label="Market price per share" value={currentPrice}
                                onChange={(e) => setCurrentPrice(parseFloat(e.target.value) || 0)}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                    </div>

                    <div>
                        <label htmlFor="ddmmodel-3" className="block text-xs font-semibold text-slate-500 uppercase mb-1">Cost of Equity (%)</label>
                        <input id="ddmmodel-3"
                            type="number"
                            aria-label="Cost of equity (%)" value={requiredReturn * 100}
                            onChange={(e) => setRequiredReturn(parseFloat(e.target.value) / 100)}
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="ddmmodel-4" className="block text-xs font-semibold text-slate-500 uppercase mb-1">Growth Rate (%)</label>
                            <input id="ddmmodel-4"
                                type="number"
                                aria-label="Dividend growth (%)" value={growthRate * 100}
                                onChange={(e) => setGrowthRate(parseFloat(e.target.value) / 100)}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                        <div>
                            <label htmlFor="ddmmodel-5" className="block text-xs font-semibold text-slate-500 uppercase mb-1">Terminal g (%) · multi-stage only</label>
                            <input id="ddmmodel-5"
                                type="number"
                                aria-label="Terminal dividend growth (%)" value={terminalGrowth * 100}
                                onChange={(e) => setTerminalGrowth(parseFloat(e.target.value) / 100)}
                                className="w-full px-3 py-2 border rounded-lg"
                            />
                        </div>
                    </div>

                    {modelType === 'multi' && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                            <div className="flex justify-between items-center mb-1">
                                <label htmlFor="ddmmodel-6" className="text-[10px] font-bold text-slate-500 uppercase">Growth Horizon</label>
                                <span className="text-[10px] font-black text-brand-600">{years}Y</span>
                            </div>
                            <input id="ddmmodel-6"
                                type="range"
                                min="1"
                                max="10"
                                aria-label="Growth horizon" value={years}
                                onChange={e => setYears(parseInt(e.target.value))}
                                className="w-full h-1 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-brand-600"
                            />
                        </motion.div>
                    )}

                    <button
                        onClick={runModel}
                        disabled={loading}
                        className="w-full py-4 bg-brand-600 text-white font-black uppercase tracking-widest text-xs rounded-2xl flex items-center justify-center space-x-2 shadow-lg shadow-brand-100 hover:bg-brand-700 transition-all disabled:opacity-70"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>Solve {modelType.toUpperCase()} DDM</span>}
                    </button>

                    {error && (
                        <div role="alert" className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center space-x-2">
                            <AlertCircle className="w-4 h-4" />
                            <span>{error}</span>
                        </div>
                    )}
                </div>
            </motion.div>

            <div className="lg:col-span-2 space-y-6">
                {result ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100"
                    >
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="text-lg font-bold">Solving for {ticker} Intrinsic Value</h3>
                            <div className={clsx(
                                "px-4 py-1 rounded-full text-xs font-bold",
                                result.upside > 0 ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                            )}>
                                {(result.upside).toFixed(1)}% Implied Upside
                            </div>
                        </div>

                        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                            <div className="p-4 bg-brand-50 rounded-xl border border-brand-100">
                                <p className="text-[10px] font-black text-brand-400 uppercase tracking-widest mb-1">Intrinsic Value</p>
                                <p className="text-2xl font-black text-brand-700">{result.intrinsic_value.toFixed(2)}</p>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Market Price</p>
                                <p className="text-2xl font-black text-slate-700">{currentPrice.toFixed(2)}</p>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Div. Yield</p>
                                <p className="text-2xl font-black text-slate-700">{((currentDividend / currentPrice) * 100).toFixed(1)}%</p>
                            </div>

                        </div>

                        <div className="h-64 flex items-center justify-center">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData}>
                                    <XAxis dataKey="name"/><YAxis/><RechartsTooltip/>
                                    <Bar dataKey="value" name="Currency per share" fill="#4f46e5"/>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>
                ) : (
                    <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl h-full flex flex-col items-center justify-center p-12 text-center">
                        <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-4">
                            <Calculator className="w-8 h-8 text-slate-300" />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900">Dividend Discount Model</h3>
                        <p className="text-sm text-slate-500 max-w-sm mt-2">For dividend-paying companies. Use Gordon growth for a stable growth assumption or a multi-stage model for a transition period.</p>
                    </div>
                )}
            </div>
        </fieldset>
    );
}
