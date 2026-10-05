'use client';

import React from 'react';
import { useAssumptions } from '../context/AssumptionsContext';
import { Save, RefreshCcw, Info } from 'lucide-react';

export default function AssumptionsPanel() {
    const { assumptions, updateAssumptions, isSyncing } = useAssumptions();

    const handleChange = (key: string, value: string) => {
        const numValue = parseFloat(value) / 100;
        if (!isNaN(numValue)) {
            updateAssumptions({ [key]: numValue });
        }
    };

    return (
        <div className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                    <div className="p-2 bg-brand-50 rounded-lg">
                        <Save className="w-4 h-4 text-brand-600" />
                    </div>
                    <h3 className="font-bold text-slate-800">Global Assumptions</h3>
                </div>
                {isSyncing && (
                    <RefreshCcw className="w-4 h-4 text-brand-500 animate-spin" />
                )}
            </div>

            <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                    <label htmlFor="assumptionspanel-0" className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center">
                        Cost of Capital (WACC)
                        <Info className="w-3 h-3 ml-1 cursor-help" />
                    </label>
                    <div className="relative">
                        <input id="assumptionspanel-0"
                            type="number"
                            value={(assumptions.wacc * 100).toFixed(2)}
                            onChange={(e) => handleChange('wacc', e.target.value)}
                            className="w-full bg-slate-50 border-none rounded-xl px-4 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-brand-500 transition-all"
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">%</span>
                    </div>
                </div>

                <div className="space-y-2">
                    <label htmlFor="assumptionspanel-1" className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center">
                        Terminal Growth Rate
                        <Info className="w-3 h-3 ml-1 cursor-help" />
                    </label>
                    <div className="relative">
                        <input id="assumptionspanel-1"
                            type="number"
                            value={(assumptions.terminalGrowth * 100).toFixed(2)}
                            onChange={(e) => handleChange('terminalGrowth', e.target.value)}
                            className="w-full bg-slate-50 border-none rounded-xl px-4 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-brand-500 transition-all"
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">%</span>
                    </div>
                </div>

                <div className="space-y-2">
                    <label htmlFor="assumptionspanel-2" className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center">
                        Marginal Tax Rate
                        <Info className="w-3 h-3 ml-1 cursor-help" />
                    </label>
                    <div className="relative">
                        <input id="assumptionspanel-2"
                            type="number"
                            value={(assumptions.taxRate * 100).toFixed(2)}
                            onChange={(e) => handleChange('taxRate', e.target.value)}
                            className="w-full bg-slate-50 border-none rounded-xl px-4 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-brand-500 transition-all"
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">%</span>
                    </div>
                </div>

                <div className="space-y-2">
                    <label htmlFor="assumptionspanel-3" className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center">
                        Risk-Free Rate
                        <Info className="w-3 h-3 ml-1 cursor-help" />
                    </label>
                    <div className="relative">
                        <input id="assumptionspanel-3"
                            type="number"
                            value={(assumptions.riskFreeRate * 100).toFixed(2)}
                            onChange={(e) => handleChange('riskFreeRate', e.target.value)}
                            className="w-full bg-slate-50 border-none rounded-xl px-4 py-2 font-bold text-slate-900 focus:ring-2 focus:ring-brand-500 transition-all"
                        />
                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">%</span>
                    </div>
                </div>
            </div>

            <p className="mt-6 text-[10px] text-slate-400 italic">
                Changes here will automatically update all open DCF, DDM, and NAV models to maintain consistency.
            </p>
        </div>
    );
}
