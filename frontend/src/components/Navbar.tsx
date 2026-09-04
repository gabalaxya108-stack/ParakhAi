import React from 'react';
import { Shield, BarChart3, PlusCircle, BookOpen, History, Award, CheckCircle2 } from 'lucide-react';

interface NavbarProps {
  currentTab: 'dashboard' | 'new' | 'rules' | 'history' | 'cockpit';
  onSelectTab: (tab: 'dashboard' | 'new' | 'rules' | 'history') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Info */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => onSelectTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 ring-1 ring-white/20">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-tight">LegalMetrology<span className="text-blue-400">AI</span></span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/400/10 text-blue-400 border border-blue-500/20 font-medium">PCR 2011</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Packaged Commodity Compliance & Screening Platform</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800/80">
            <button
              onClick={() => onSelectTab('dashboard')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => onSelectTab('new')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'new'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <PlusCircle className="w-4 h-4" />
              New Inspection
            </button>
            <button
              onClick={() => onSelectTab('rules')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'rules'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Rules Library
            </button>
            <button
              onClick={() => onSelectTab('history')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                currentTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <History className="w-4 h-4" />
              Inspection History
            </button>
          </nav>

          {/* Officer Status Badge */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/400/10 border border-emerald-500/20 px-2.5 py-1 rounded-full text-xs text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Rule Engine Active
            </div>
            <div className="flex items-center gap-2.5 bg-slate-800/60 border border-slate-700/80 px-3 py-1.5 rounded-xl">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/400/20 text-indigo-300 flex items-center justify-center font-bold text-xs">
                MS
              </div>
              <div className="text-left hidden lg:block">
                <div className="text-xs font-semibold text-slate-200">Insp. M. Sharma</div>
                <div className="text-[10px] text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400">Badge #LM-4089</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
