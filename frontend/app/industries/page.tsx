'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import api,{errorMessage} from '@/utils/api';
import { Building2, TrendingUp, DollarSign, ChevronRight, Loader2, Info } from 'lucide-react';
import clsx from 'clsx';

interface KeyDriver {
    why_important?: string;
    example?: string;
  name: string;
  description: string;
  typical_range: string;
  importance: string;
}

interface SectorProfile {
  sector: string;
  description: string;
  key_drivers: KeyDriver[];
  key_metrics: string[];
  typical_multiples: Record<string, string>;
  regulatory_considerations: string[];
}

export default function IndustryAnalysis() {
  const [sectors, setSectors] = useState<any[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>('real_estate');
  const [profile, setProfile] = useState<SectorProfile | null>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/industries/sectors').then(res => setSectors(res.data.sectors)).catch(e=>{setError(errorMessage(e));setLoading(false);});
  }, []);

  useEffect(() => {
    let active=true;
    if (selectedSector) {
      setLoading(true);setError('');setProfile(null);setCompanies([]);
      Promise.all([
        api.get(`/industries/sectors/${selectedSector}/profile`),
        api.get(`/industries/sectors/${selectedSector}/companies`)
      ]).then(([profileRes, companiesRes]) => {
        if(!active)return;
        setProfile(profileRes.data);
        setCompanies(companiesRes.data);
      }).catch(e=>{if(active)setError(errorMessage(e));}).finally(()=>{if(active)setLoading(false);});
    }
    return ()=>{active=false;};
  }, [selectedSector]);

  const getImportanceColor = (importance: string) => {
    switch (importance.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="p-3 bg-brand-700 rounded-xl text-white ">
          <Building2 className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Industry Analysis</h1>
          <p className="text-slate-500">Deep-dive into sector-specific drivers, key metrics, and company universes</p>
        </div>
      </div>

      {/* Sector Selector */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-4">Select Industry</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {sectors.map(sector => (
            <button
              key={sector.id}
              onClick={() => setSelectedSector(sector.id)}
              className={clsx(
                "px-4 py-3 rounded-xl font-medium text-sm transition-all text-left",
                selectedSector === sector.id
                  ? "bg-brand-600 text-white "
                  : "bg-slate-50 text-slate-700 hover:bg-slate-100"
              )}
            >
              {sector.name}
            </button>
          ))}
        </div>
      </div>

      {error&&<p role="alert" className="rounded-lg bg-amber-50 p-4 text-amber-900">{error} Choose another sector to continue.</p>}
      <p className="text-sm text-slate-600">Educational reference. Ranges, multiples and company figures are illustrative, undated examples, not current market observations. Verify applicable jurisdiction and current rules separately.</p>
      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
      ) : profile && (
        <>
          {/* Sector Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-slate-50 p-6 rounded-2xl border border-brand-100"
          >
            <h2 className="text-xl font-bold text-slate-900 mb-2">{profile.sector}</h2>
            <p className="text-slate-600">{profile.description}</p>
          </motion.div>

          {/* Key Drivers */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="text-lg font-bold mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-brand-600" />
              Key Value Drivers
            </h3>
            <div className="space-y-3">
              {profile.key_drivers.map((driver, idx) => (
                <div key={idx} className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-bold text-slate-900">{driver.name}</h4>
                    <span className={clsx("px-2 py-1 rounded-full text-xs font-semibold", getImportanceColor(driver.importance))}>
                      {driver.importance}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{driver.description}</p>
                  <p className="text-xs text-brand-600 font-mono mb-3">Illustrative range: {driver.typical_range}</p>

                  {driver.why_important && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                      <p className="text-xs font-bold text-blue-900 mb-1">Why It Matters:</p>
                      <p className="text-xs text-blue-800">{driver.why_important}</p>
                    </div>
                  )}

                  {false && driver.example && (
                    <div className="mt-2 p-3 bg-amber-50 rounded-lg border border-amber-100">
                      <p className="text-xs font-bold text-amber-900 mb-1">Real Example:</p>
                      <p className="text-xs text-amber-800">{driver.example}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Key Metrics & Multiples */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h3 className="text-lg font-bold mb-4">Key Financial Metrics</h3>
              <div className="grid grid-cols-2 gap-2">
                {profile.key_metrics.map((metric, idx) => (
                  <div key={idx} className="px-3 py-2 bg-brand-50 rounded-lg text-sm font-medium text-brand-900">
                    {metric}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h3 className="text-lg font-bold mb-4">Illustrative valuation multiples</h3>
              <div className="space-y-2">
                {Object.entries(profile.typical_multiples).map(([metric, range]) => (
                  <div key={metric} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                    <span className="font-semibold text-slate-700">{metric}</span>
                    <span className="text-brand-600 font-mono text-sm">{range}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Company Universe */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="text-lg font-bold mb-4 flex items-center">
              <DollarSign className="w-5 h-5 mr-2 text-green-600" />
              Illustrative company examples
            </h3>
            <div className="space-y-3">
              {companies.map((company, idx) => (
                <div key={idx} className="p-4 bg-slate-50 rounded-xl relative">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-bold text-slate-900 text-lg">{company.ticker}</h4>
                      <p className="text-sm text-slate-600">{company.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Example market cap (USD)</p>
                      <p className="font-bold text-slate-900">${(company.market_cap / 1000).toFixed(1)}B</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-600 mb-3">{company.description}</p>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(company.key_metrics).slice(0, 3).map(([key, val]: [string, any]) => (
                      <div key={key} className="px-2 py-1 bg-white rounded border border-slate-200">
                        <p className="text-xs text-slate-500 capitalize">{key.replace('_', ' ')}</p>
                        <p className="text-sm font-semibold text-slate-900">
                          {typeof val === 'number' && val < 1 ? (val * 100).toFixed(1) + '%' : val}
                        </p>
                      </div>
                    ))}
                  </div>
                  <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))}
            </div>
          </div>

          {/* Regulatory topics to verify */}
          <div className="bg-amber-50 p-6 rounded-2xl border border-amber-200">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <h3 className="text-lg font-bold text-amber-900 mb-2">Regulatory topics to verify</h3>
                <ul className="space-y-1 text-sm text-amber-800">
                  {profile.regulatory_considerations.map((item, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
