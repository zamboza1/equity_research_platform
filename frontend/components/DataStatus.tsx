'use client';
import {useEffect, useState} from 'react';
import api from '@/utils/api';

export default function DataStatus() {
  const [status, setStatus] = useState<{data_mode: string; fred_key_configured: boolean} | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    api.get('/status').then(response => {if (active) setStatus(response.data);})
      .catch(() => {if (active) setFailed(true);});
    return () => {active = false;};
  }, []);
  if (!status && !failed) return null;
  const message = failed ? 'Cannot reach the research API. Start the backend and reload.'
    : status?.data_mode === 'offline' ? 'Offline test mode. External data is disabled; manual models and saved research remain available. Restart the backend with VERTIGE_OFFLINE=0 to enable providers.'
    : status?.fred_key_configured ? 'Live providers enabled · FRED key configured. Availability and source dates are shown with the data.'
    : 'Live providers enabled · FRED key missing. Add FRED_API_KEY to backend/.env and restart the backend for macro data. Yahoo Finance does not require a key.';
  return <p role="status" className={`no-print mb-6 rounded border px-4 py-3 text-xs leading-5 ${failed || status?.data_mode === 'offline' || !status?.fred_key_configured ? 'border-amber-200 bg-amber-50 text-amber-950' : 'border-slate-200 bg-white text-slate-600'}`}>{message}</p>;
}
