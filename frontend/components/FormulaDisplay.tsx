'use client';

import React from 'react';
import { Info, Calculator } from 'lucide-react';

interface FormulaDisplayProps {
    label: string;
    formula: string;
    explanation: string;
    example?: string;
}

export default function FormulaDisplay({ label, formula, explanation, example }: FormulaDisplayProps) {
    return (
        <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-xl p-4 mb-4">
            <div className="flex items-start space-x-3">
                <div className="p-2 bg-emerald-100 rounded-lg">
                    <Calculator className="w-5 h-5 text-emerald-700" />
                </div>
                <div className="flex-1">
                    <h4 className="font-semibold text-slate-900 mb-2">{label}</h4>

                    {/* Formula */}
                    <div className="bg-white border border-slate-300 rounded-lg p-3 mb-3">
                        <code className="text-sm font-mono text-slate-900">{formula}</code>
                    </div>

                    {/* Explanation */}
                    <div className="flex items-start space-x-2 mb-2">
                        <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-slate-700">{explanation}</p>
                    </div>

                    {/* Example */}
                    {example && (
                        <div className="bg-emerald-50 border border-emerald-200 rounded p-2 mt-2">
                            <p className="text-xs text-emerald-800">
                                <strong>Example:</strong> {example}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Tooltip component for inline help
export function InlineHelp({ children, tooltip }: { children: React.ReactNode; tooltip: string }) {
    const [show, setShow] = React.useState(false);

    return (
        <div className="relative inline-block">
            <div
                onMouseEnter={() => setShow(true)}
                onMouseLeave={() => setShow(false)}
                className="cursor-help border-b border-dashed border-slate-400"
            >
                {children}
            </div>
            {show && (
                <div className="absolute z-10 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    {tooltip}
                    <div className="absolute w-2 h-2 bg-slate-900 transform rotate-45 left-1/2 -translate-x-1/2 -bottom-1"></div>
                </div>
            )}
        </div>
    );
}

// Calculation breakdown component
interface CalculationStep {
    label: string;
    value: number | string;
    formula?: string;
}

export function CalculationBreakdown({ steps, finalResult }: { steps: CalculationStep[]; finalResult: { label: string; value: number | string } }) {
    return (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
            <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                <Calculator className="w-4 h-4 mr-2 text-emerald-600" />
                Calculation Breakdown
            </h4>

            <div className="space-y-2">
                {steps.map((step, idx) => (
                    <div key={idx} className="flex justify-between items-start py-2 border-b border-slate-100 last:border-0">
                        <div className="flex-1">
                            <p className="text-sm text-slate-700">{step.label}</p>
                            {step.formula && (
                                <code className="text-xs text-slate-500 font-mono">{step.formula}</code>
                            )}
                        </div>
                        <span className="font-mono text-sm text-slate-900 ml-4">{typeof step.value === 'number' ? step.value.toFixed(2) : step.value}</span>
                    </div>
                ))}

                {/* Final Result */}
                <div className="pt-3 mt-2 border-t-2 border-emerald-600">
                    <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-900">{finalResult.label}</span>
                        <span className="font-bold text-2xl text-emerald-600">
                            {typeof finalResult.value === 'number' ? `$${finalResult.value.toFixed(2)}` : finalResult.value}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}
