'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface Assumptions {
    wacc: number;
    taxRate: number;
    terminalGrowth: number;
    riskFreeRate: number;
    marketPremium: number;
}

interface AssumptionsContextType {
    assumptions: Assumptions;
    updateAssumptions: (newAssumptions: Partial<Assumptions>) => void;
    isSyncing: boolean;
}

const defaultAssumptions: Assumptions = {
    wacc: 0.085,
    taxRate: 0.25,
    terminalGrowth: 0.02,
    riskFreeRate: 0.042,
    marketPremium: 0.055,
};

const AssumptionsContext = createContext<AssumptionsContextType | undefined>(undefined);

export function AssumptionsProvider({ children }: { children: React.ReactNode }) {
    const [assumptions, setAssumptions] = useState<Assumptions>(defaultAssumptions);
    const [isSyncing, setIsSyncing] = useState(false);

    // Load from local storage on mount
    useEffect(() => {
        const saved = localStorage.getItem('global-assumptions');
        if (saved) {
            try {
                setAssumptions(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to parse assumptions", e);
            }
        }
    }, []);

    const updateAssumptions = (newAssumptions: Partial<Assumptions>) => {
        setIsSyncing(true);
        const updated = { ...assumptions, ...newAssumptions };
        setAssumptions(updated);
        localStorage.setItem('global-assumptions', JSON.stringify(updated));

        // Mock API call to backend (to be implemented)
        setTimeout(() => setIsSyncing(false), 500);
    };

    return (
        <AssumptionsContext.Provider value={{ assumptions, updateAssumptions, isSyncing }}>
            {children}
        </AssumptionsContext.Provider>
    );
}

export function useAssumptions() {
    const context = useContext(AssumptionsContext);
    if (context === undefined) {
        throw new Error('useAssumptions must be used within an AssumptionsProvider');
    }
    return context;
}
