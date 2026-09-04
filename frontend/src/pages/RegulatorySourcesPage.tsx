import React from 'react';
import { ExternalLink, Shield, BookOpen, Scale, Calendar } from 'lucide-react';

interface GazetteDocument {
  id: string;
  title: string;
  category: string;
  publishedDate: string;
  description: string;
  sourceUrl: string;
  publisher: string;
}

const GAZETTE_DOCUMENTS: GazetteDocument[] = [
  {
    id: 'doc_pcr_2011',
    title: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    category: 'Primary Rules',
    publishedDate: '2011-03-01',
    description: 'Principal rules governing mandatory declarations on pre-packaged commodities sold in India. Covers MRP, Net Quantity, Manufacturer/Packer details, Date of Manufacturing, Consumer Care, and Country of Origin.',
    sourceUrl: 'https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011',
    publisher: 'Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution',
  },
  {
    id: 'doc_ecom_2017',
    title: 'GSR 629(E) — E-Commerce Marketplace Amendment, 2017',
    category: 'Amendment',
    publishedDate: '2017-06-26',
    description: 'Amendment introducing mandatory declaration requirements for e-commerce marketplace listings.',
    sourceUrl: 'https://consumeraffairs.nic.in/sites/default/files/GSR629E.pdf',
    publisher: 'Gazette of India, Extraordinary, Part II, Section 3(i)',
  },
  {
    id: 'doc_amendment_2022',
    title: 'Legal Metrology (Packaged Commodities) Amendment Rules, 2022',
    category: 'Amendment',
    publishedDate: '2022-07-01',
    description: 'Amendment updating Unit Sale Price requirements, electronic product declarations, and QR-code based declaration provisions.',
    sourceUrl: 'https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011',
    publisher: 'Department of Consumer Affairs, Ministry of Consumer Affairs',
  },
  {
    id: 'doc_lm_act_2009',
    title: 'The Legal Metrology Act, 2009',
    category: 'Primary Act',
    publishedDate: '2010-03-01',
    description: 'The parent statute establishing standards of weights and measures, regulating trade and commerce in weights, measures, and other goods sold by weight, measure, or number.',
    sourceUrl: 'https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/legal-metrology-act-2009',
    publisher: 'Parliament of India',
  },
  {
    id: 'doc_pcr_2026',
    title: 'Consolidated Packaged Commodities Rules — 2026 Effective Version',
    category: 'Consolidated Version',
    publishedDate: '2026-01-01',
    description: 'Consolidated version incorporating all amendments up to 2026. Used as the effective statutory reference for current inspections on the PARAKH AI platform.',
    sourceUrl: 'https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/packaged-commodities-rules-2011',
    publisher: 'Department of Consumer Affairs (Consolidated by PARAKH AI Team)',
  },
];

export const RegulatorySourcesPage: React.FC = () => {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white rounded-2xl shadow-xl border border-slate-800">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-xs font-mono font-semibold border border-amber-400/20 flex items-center gap-1">
            <Scale className="w-3 h-3" /> OFFICIAL GAZETTE REFERENCES
          </span>
        </div>
        <h1 className="text-2xl font-black tracking-tight">Regulatory Sources & Publications</h1>
        <p className="text-sm text-slate-300 mt-1 max-w-2xl">
          All statutory requirements on the PARAKH AI platform are sourced from official Department of Consumer Affairs (DCA) Gazette Notifications.
        </p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30 rounded-xl p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="text-sm font-bold text-amber-900 dark:text-amber-200">Source Traceability Principle</h3>
          <p className="text-xs text-amber-800 dark:text-amber-300 mt-0.5">
            Every statutory rule evaluated by PARAKH AI is linked to its official Gazette source document, page number, and excerpt.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {GAZETTE_DOCUMENTS.map((doc) => (
          <div key={doc.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    doc.category === 'Primary Act' ? 'bg-indigo-100 text-indigo-800 border-indigo-300' :
                    doc.category === 'Primary Rules' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                    doc.category === 'Amendment' ? 'bg-amber-100 text-amber-800 border-amber-300' :
                    'bg-emerald-100 text-emerald-800 border-emerald-300'
                  }`}>{doc.category}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{doc.id}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-snug">{doc.title}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{doc.description}</p>
                <div className="flex items-center gap-4 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{doc.publishedDate}</span>
                  <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{doc.publisher}</span>
                </div>
              </div>
              <a href={doc.sourceUrl} target="_blank" rel="noreferrer"
                className="self-start sm:self-center px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 hover:bg-blue-500 transition shadow-sm whitespace-nowrap">
                <ExternalLink className="w-3.5 h-3.5" /><span>View Official Source</span>
              </a>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center text-[11px] text-slate-400 py-4">
        All sources are maintained as part of the PARAKH AI Regulatory Knowledge Base.
      </div>
    </div>
  );
};
