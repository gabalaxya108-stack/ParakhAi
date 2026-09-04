import React, { useEffect, useState } from 'react';
import { healthApi } from '../api/health';
import { HealthResponse } from '../types/health';
import { Activity } from 'lucide-react';

export const HealthStatusBadge: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [online, setOnline] = useState<boolean>(true);

  useEffect(() => {
    healthApi
      .getHealth()
      .then((h) => {
        setHealth(h);
        setOnline(h.status === 'healthy');
      })
      .catch(() => {
        setOnline(false);
      });
  }, []);

  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
      <span
        className={`w-2 h-2 rounded-full ${
          online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
        }`}
      ></span>
      <span className="text-[11px] font-mono text-slate-300">
        {online ? 'API Online' : 'API Offline'}
      </span>
    </div>
  );
};
