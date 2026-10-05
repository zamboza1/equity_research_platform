'use client';

import React, { useState } from 'react';
import { X, Info, BookOpen, Calculator, HelpCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TutorialStep {
    title: string;
    description: string;
    formula?: string;
    explanation?: string;
}

interface TutorialConfig {
    model: string;
    steps: TutorialStep[];
}

const tutorials: Record<string, TutorialConfig> = {
    dcf: {
        model: 'Discounted Cash Flow (DCF)',
        steps: [
            {
                title: 'What is DCF?',
                description: 'DCF values a company based on its future cash flows, discounted to present value.',
                explanation: 'Think of it as: "If this company generates $X in cash each year, what\'s that worth today?"'
            },
            {
                title: 'Step 1: Project Free Cash Flows',
                description: 'Forecast how much cash the business will generate each year.',
                formula: 'FCF = EBIT × (1 - Tax Rate) + D&A - CapEx - ΔWorking Capital',
                explanation: 'Start with operating profit, adjust for taxes, add back non-cash charges, subtract investments.'
            },
            {
                title: 'Step 2: Calculate WACC',
                description: 'Determine the discount rate (Weighted Average Cost of Capital).',
                formula: 'WACC = (E/V × Re) + (D/V × Rd × (1-T))',
                explanation: 'This is the average rate investors expect. Higher risk = higher WACC = lower valuation.'
            },
            {
                title: 'Step 3: Calculate Terminal Value',
                description: 'Estimate the value of all cash flows beyond your forecast period.',
                formula: 'TV = normalized next-year FCFF / (WACC - g)',
                explanation: 'Gordon Growth Model: assumes cash flows grow at constant rate "g" forever (typically 2-3%).'
            },
            {
                title: 'Step 4: Discount to Present',
                description: 'Bring all future values back to today using WACC.',
                formula: 'PV = Σ [FCF_t / (1 + WACC)^t] + [TV / (1 + WACC)^n]',
                explanation: 'Sum the present value of each year\'s cash flow plus the terminal value.'
            },
            {
                title: 'Step 5: Calculate Equity Value',
                description: 'Convert enterprise value to equity value per share.',
                formula: 'Equity = EV - Net Debt - Minority Interest - Preferred Equity + Nonoperating Assets',
                explanation: 'Subtract debt, add cash, then divide by shares outstanding to get price per share.'
            }
        ]
    },
    nav: {
        model: 'Net Asset Value (NAV)',
        steps: [
            {
                title: 'What is NAV?',
                description: 'NAV values a company by the fair market value of its assets minus liabilities.',
                explanation: 'For REITs and other asset-heavy companies. "If we sold everything, what would shareholders get?"'
            },
            {
                title: 'Step 1: Value Individual Assets',
                description: 'Determine fair market value of each property or asset.',
                formula: 'Property Value = NOI / Cap Rate',
                explanation: 'For real estate: divide Net Operating Income by the market Cap Rate for that property type.'
            },
            {
                title: 'Step 2: Sum Total Assets',
                description: 'Add up all asset values at fair market value.',
                formula: 'Total Assets = Σ Individual Property Values',
                explanation: 'Include operating properties, development projects, land, and other investments.'
            },
            {
                title: 'Step 3: Subtract Liabilities',
                description: 'Deduct all debt and liabilities.',
                formula: 'NAV = Total Assets - Total Debt - Other Liabilities',
                explanation: 'Net Debt = Total Debt - Cash. This gives you net equity value.'
            },
            {
                title: 'Step 4: NAV Per Share',
                description: 'Divide by shares outstanding.',
                formula: 'NAV/Share = NAV / Shares Outstanding',
                explanation: 'Compare this to current stock price. Trading below NAV = potential value opportunity.'
            }
        ]
    },
    lbo: {
        model: 'Leveraged Buyout (LBO)',
        steps: [
            {
                title: 'What is an LBO?',
                description: 'LBO uses significant debt to acquire a company, aiming for high equity returns through leverage.',
                explanation: 'Buy a company with mostly debt, improve operations, pay down debt, sell for profit.'
            },
            {
                title: 'Step 1: Sources & Uses',
                description: 'Determine how much capital is needed and where it comes from.',
                formula: 'Sources = Debt + Equity | Uses = Purchase Price + Fees',
                explanation: 'Typically 60-70% debt, 30-40% equity. Uses include transaction fees (~2-3%).'
            },
            {
                title: 'Step 2: Build Financial Model',
                description: 'Project cash flows and debt paydown over 5-7 years.',
                formula: 'Free Cash Flow = EBITDA - CapEx - ΔWC - Cash Interest - Cash Taxes',
                explanation: 'Excess cash goes to paying down debt (debt sweep). Shows improving equity value.'
            },
            {
                title: 'Step 3: Model Exit',
                description: 'Estimate sale value at exit using EBITDA multiple.',
                formula: 'Exit EV = Exit EBITDA × Exit Multiple',
                explanation: 'Exit multiple often same as entry. Conservative assumption.'
            },
            {
                title: 'Step 4: Calculate Returns',
                description: 'Determine IRR and MOIC for equity investors.',
                formula: 'MOIC = Exit Equity Value / Initial Equity Invested',
                explanation: 'IRR accounts for time value. Target: >20% IRR, >2.5x MOIC for PE funds.'
            }
        ]
    },
    '3statement': {
        model: '3-Statement Model',
        steps: [
            {
                title: 'What is a 3-Statement Model?',
                description: 'It links the Income Statement, Balance Sheet, and Cash Flow Statement into one cohesive system.',
                explanation: 'This is the "Holy Grail" of finance. Every dollar is tracked across all three views of the business.'
            },
            {
                title: 'Step 1: Income Statement',
                description: 'Project revenue and expenses down to Net Income.',
                formula: 'Net Income = Revenue - COGS - OpEx - Interest - Taxes',
                explanation: 'Start here. Net Income is the primary driver for Retained Earnings on the Balance Sheet.'
            },
            {
                title: 'Step 2: Balance Sheet',
                description: 'State the company\'s assets, liabilities, and equity at a point in time.',
                formula: 'Assets = Liabilities + Equity',
                explanation: 'The Balance Sheet must ALWAYS balance. Cash is usually the "plug" or revolver-linked.'
            },
            {
                title: 'Step 3: Cash Flow Statement',
                description: 'Track the actual cash movement across operating, investing, and financing.',
                formula: 'Net Cash = Cash from Operations + Investing + Financing',
                explanation: 'Converts accrual accounting (Net Income) to actual cash in the bank.'
            },
            {
                title: 'Step 4: Linking & Circularity',
                description: 'Ensure statements interact. Interest depends on debt; debt depends on cash flow.',
                explanation: 'The model iterates until circular references (Interest <-> Debt) converge on a stable value.'
            }
        ]
    }
};

interface HelpOverlayProps {
    modelType: 'dcf' | 'nav' | 'lbo' | 'ddm';
    onClose: () => void;
}

export default function HelpOverlay({ modelType, onClose }: HelpOverlayProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const tutorial = tutorials[modelType];

    if (!tutorial) return null;

    const step = tutorial.steps[currentStep];
    const isLastStep = currentStep === tutorial.steps.length - 1;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-brand-600 to-amber-600 text-white p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <div className="flex items-center space-x-2 mb-2">
                                    <BookOpen className="w-6 h-6" />
                                    <h2 className="text-2xl font-bold">{tutorial.model}</h2>
                                </div>
                                <p className="text-brand-100 text-sm">Interactive Tutorial - Step {currentStep + 1} of {tutorial.steps.length}</p>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="p-6 overflow-y-auto max-h-[50vh]">
                        <h3 className="text-xl font-bold text-slate-900 mb-3">{step.title}</h3>
                        <p className="text-slate-600 mb-4 leading-relaxed">{step.description}</p>

                        {step.formula && (
                            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-4">
                                <div className="flex items-start space-x-2 mb-2">
                                    <Calculator className="w-5 h-5 text-brand-600 mt-0.5" />
                                    <span className="text-sm font-semibold text-slate-700">Formula:</span>
                                </div>
                                <code className="block bg-white p-3 rounded border border-slate-300 font-mono text-sm text-slate-900">
                                    {step.formula}
                                </code>
                            </div>
                        )}

                        {step.explanation && (
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                                <div className="flex items-start space-x-2">
                                    <Info className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <span className="text-sm font-semibold text-amber-900 block mb-1">Plain English:</span>
                                        <p className="text-sm text-amber-800">{step.explanation}</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Progress Bar */}
                    <div className="px-6 py-2 bg-slate-50">
                        <div className="flex space-x-1">
                            {tutorial.steps.map((_, idx) => (
                                <div
                                    key={idx}
                                    className={`h-1 flex-1 rounded-full transition-colors ${idx <= currentStep ? 'bg-brand-600' : 'bg-slate-200'
                                        }`}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-slate-200 flex justify-between items-center">
                        <button
                            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                            disabled={currentStep === 0}
                            className="px-4 py-2 text-slate-600 hover:text-slate-900 disabled:opacity-30 disabled:cursor-not-allowed font-medium"
                        >
                            ← Previous
                        </button>

                        <div className="flex items-center space-x-2">
                            {tutorial.steps.map((_, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setCurrentStep(idx)}
                                    className={`w-2 h-2 rounded-full transition-all ${idx === currentStep
                                        ? 'bg-brand-600 w-8'
                                        : 'bg-slate-300 hover:bg-slate-400'
                                        }`}
                                />
                            ))}
                        </div>

                        {isLastStep ? (
                            <button
                                onClick={onClose}
                                className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
                            >
                                Get Started →
                            </button>
                        ) : (
                            <button
                                onClick={() => setCurrentStep(Math.min(tutorial.steps.length - 1, currentStep + 1))}
                                className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 font-medium transition-colors"
                            >
                                Next →
                            </button>
                        )}
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

// Reusable Help Button Component
export function HelpButton({ modelType }: { modelType: 'dcf' | 'nav' | 'lbo' | 'ddm' }) {
    const [showHelp, setShowHelp] = useState(false);

    return (
        <>
            <button
                onClick={() => setShowHelp(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors font-medium"
            >
                <HelpCircle className="w-4 h-4" />
                <span>How it Works</span>
            </button>

            {showHelp && <HelpOverlay modelType={modelType} onClose={() => setShowHelp(false)} />}
        </>
    );
}
