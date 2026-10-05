'use client';

import React, { useEffect, useState } from 'react';
import AdvancedDCF from '@/components/AdvancedDCF';
import DDMModel from '@/components/DDMModel';
import AdvancedNAV from '@/components/AdvancedNAV';
import ThreeStatementModel from '@/components/ThreeStatementModel';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { HelpButton } from '@/components/HelpOverlay';
import clsx from 'clsx';

export default function ValuationPage() {
    const [mounted, setMounted] = useState(false);
    const [activeTab, setActiveTab] = useState<'dcf' | 'ddm' | 'nav' | '3statement'>('dcf');

    useEffect(() => {
        setMounted(true);
        const tab = new URLSearchParams(window.location.search).get("tab");
        if (tab === "3statement" || tab === "dcf" || tab === "ddm" || tab === "nav") setActiveTab(tab);
    }, []);

    if (!mounted) return (
        <div className="h-screen flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
    );

    const tabs = [
        { id: 'dcf', label: 'DCF Model' },
        { id: 'ddm', label: 'DDM Model' },
        { id: 'nav', label: 'NAV Model' },
        { id: '3statement', label: '3-Statement' },
    ];

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <Link href="/" className="inline-flex items-center text-sm text-slate-500 hover:text-brand-600 transition-colors mb-4">
                    <ArrowLeft className="w-4 h-4 mr-1" />
                    Back to Dashboard
                </Link>
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 gradient-text">Intrinsic Valuation</h1>
                        <p className="text-slate-500 mt-2">
                            Choose a model, review its assumptions, and inspect the calculation.
                        </p>
                    </div>
                    {activeTab !== '3statement' && <HelpButton modelType={activeTab} />}
                </div>
            </div>

            {/* Tab Switcher */}
            <div className="flex flex-wrap gap-2 mb-8 bg-slate-100 p-1.5 rounded-2xl w-fit">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={clsx(
                            "flex items-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all",
                            activeTab === tab.id
                                ? "bg-white text-brand-600 shadow-sm border border-slate-200"
                                : "text-slate-500 hover:text-slate-800 hover:bg-white/50"
                        )}
                    >
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                {activeTab === 'dcf' && <AdvancedDCF />}
                {activeTab === 'ddm' && <DDMModel />}
                {activeTab === 'nav' && <AdvancedNAV />}
                {activeTab === '3statement' && <ThreeStatementModel />}
            </motion.div>
        </div>
    );
}
