'use client';

import React, { useEffect, useState } from 'react';
import api from '@/utils/api';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';

interface MarketItem {
    symbol: string;
    price: number;
    change: number;
}

export default function MarketSnapshot() {
    const [data, setData] = useState<MarketItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/news/snapshot')
            .then(res => {
                setData(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Snapshot error", err);
                setLoading(false);
            });
    }, []);

    if (loading) return (
        <div className="h-64 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-white/50" />
        </div>
    );

    return (
        <div className="grid grid-cols-2 gap-3">
            {data.map((item) => (
                <div key={item.symbol} className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/10 hover:bg-white/15 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                        <span className="font-semibold text-white text-sm">{item.symbol}</span>
                        <span className={`text-xs flex items-center ${item.change >= 0 ? "text-green-400" : "text-red-400"}`}>
                            {item.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                            {item.change}%
                        </span>
                    </div>
                    <p className="text-xl font-bold text-white tracking-tight">
                        {item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                </div>
            ))}
        </div>
    );
}
