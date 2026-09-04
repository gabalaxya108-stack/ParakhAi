import React, { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, Layers, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { BoundingBox, ExtractedDeclarationDTO, RuleEvaluationResult } from '../types';
import { api } from '../services/api';

interface EvidenceCanvasProps {
  imageUrl: string;
  declarations: ExtractedDeclarationDTO[];
  ruleResults: RuleEvaluationResult[];
  selectedDeclId?: string;
  onSelectDeclaration: (declId: string) => void;
}

export const EvidenceCanvas: React.FC<EvidenceCanvasProps> = ({
  imageUrl,
  declarations,
  ruleResults,
  selectedDeclId,
  onSelectDeclaration
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [filterMode, setFilterMode] = useState<'all' | 'violations' | 'compliant'>('all');
  const [dimBackground, setDimBackground] = useState<boolean>(true);
  const [hoveredBox, setHoveredBox] = useState<any>(null);

  // Map declarations to their rule statuses
  const declStatusMap = new Map<string, { status: 'PASS' | 'FAIL' | 'WARNING'; reason?: string; ruleCode?: string }>();
  
  ruleResults.forEach(r => {
    const effectiveStatus = r.override_verdict || r.status;
    r.evidence_boxes.forEach(box => {
      // match box by coordinate proximity
      declarations.forEach(d => {
        if (
          Math.abs(d.bounding_box.ymin - box.ymin) < 0.05 &&
          Math.abs(d.bounding_box.xmin - box.xmin) < 0.05
        ) {
          declStatusMap.set(d.id, {
            status: effectiveStatus === 'FAIL' ? 'FAIL' : effectiveStatus === 'WARNING' ? 'WARNING' : 'PASS',
            reason: r.violation_reason,
            ruleCode: r.rule_id
          });
        }
      });
    });
  });

  const fullImageUrl = api.getImageUrl(imageUrl);

  return (
    <div className="relative flex flex-col h-full bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
      {/* Canvas Top Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 z-20 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            Grounding Evidence Canvas
          </span>
          <span className="text-xs text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">({declarations.length} grounded declarations)</span>
        </div>

        {/* Filter controls & Zoom */}
        <div className="flex items-center gap-2">
          {/* Layer Filter Pills */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-0.5 rounded-md transition-all ${
                filterMode === 'all' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterMode('violations')}
              className={`px-2.5 py-0.5 rounded-md transition-all flex items-center gap-1 ${
                filterMode === 'violations' ? 'bg-rose-600 text-white' : 'text-rose-400 hover:bg-rose-950/40'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
              Violations
            </button>
            <button
              onClick={() => setFilterMode('compliant')}
              className={`px-2.5 py-0.5 rounded-md transition-all flex items-center gap-1 ${
                filterMode === 'compliant' ? 'bg-emerald-600 text-white' : 'text-emerald-400 hover:bg-emerald-950/40'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Compliant
            </button>
          </div>

          {/* Dimmer Toggle */}
          <button
            onClick={() => setDimBackground(!dimBackground)}
            title="Toggle contrast dimming"
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-all ${
              dimBackground ? 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Highlight</span>
          </button>

          {/* Zoom Buttons */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setZoom(Math.max(0.7, zoom - 0.2))}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
              title="Zoom out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-400 px-1">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom(Math.min(2.5, zoom + 0.2))}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
              title="Zoom in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setZoom(1)}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
              title="Reset view"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Image Canvas Container */}
      <div className="relative flex-1 overflow-auto flex items-center justify-center p-6 bg-slate-950/80">
        <div
          className="relative transition-transform duration-200 ease-out origin-center select-none shadow-2xl rounded-lg"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* Packaging Image */}
          <img
            src={fullImageUrl}
            alt="Packaging inspection label"
            className={`max-h-[640px] max-w-full rounded-lg object-contain transition-all ${
              dimBackground ? 'brightness-[0.80] contrast-[1.10]' : ''
            }`}
          />

          {/* Bounding Box SVG / Overlay */}
          <div className="absolute inset-0 pointer-events-auto">
            {declarations.map(decl => {
              const info = declStatusMap.get(decl.id) || { status: 'PASS' };
              const isViolation = info.status === 'FAIL';
              const isWarning = info.status === 'WARNING';
              const isSelected = selectedDeclId === decl.id;

              if (filterMode === 'violations' && !isViolation) return null;
              if (filterMode === 'compliant' && isViolation) return null;

              const box = decl.bounding_box;
              const top = `${box.ymin * 100}%`;
              const left = `${box.xmin * 100}%`;
              const width = `${(box.xmax - box.xmin) * 100}%`;
              const height = `${(box.ymax - box.ymin) * 100}%`;

              // Border and background coloring
              let borderClass = 'border-emerald-400/80 bg-emerald-50 dark:bg-emerald-950/400/15 hover:bg-emerald-50 dark:bg-emerald-950/400/25';
              let badgeBg = 'bg-emerald-50 dark:bg-emerald-950/400 text-white';

              if (isViolation) {
                borderClass = 'border-rose-500 bg-rose-50 dark:bg-rose-950/400/25 hover:bg-rose-50 dark:bg-rose-950/400/35 ring-1 ring-rose-400/50 animate-pulse';
                badgeBg = 'bg-rose-600 text-white';
              } else if (isWarning) {
                borderClass = 'border-amber-400 bg-amber-50 dark:bg-amber-950/400/20 hover:bg-amber-50 dark:bg-amber-950/400/30';
                badgeBg = 'bg-amber-600 text-white';
              }

              if (isSelected) {
                borderClass += ' ring-4 ring-sky-400 ring-offset-2 ring-offset-slate-950 scale-[1.01]';
              }

              return (
                <div
                  key={decl.id}
                  onClick={() => onSelectDeclaration(decl.id)}
                  onMouseEnter={() => setHoveredBox({ decl, info })}
                  onMouseLeave={() => setHoveredBox(null)}
                  style={{ top, left, width, height }}
                  className={`absolute border-2 rounded transition-all cursor-pointer group ${borderClass}`}
                >
                  {/* Mini Pill Tag on Top Left of Box */}
                  <div className={`absolute -top-3 left-0 px-1.5 py-0.2 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 shadow-md ${badgeBg}`}>
                    {isViolation && <AlertTriangle className="w-2.5 h-2.5" />}
                    {!isViolation && !isWarning && <CheckCircle className="w-2.5 h-2.5" />}
                    <span>{box.label || decl.declaration_type.replace('_', ' ')}</span>
                  </div>

                  {/* Estimated Font Height Tag if available */}
                  {box.estimated_font_height_mm && (
                    <div className="absolute -bottom-3 right-0 bg-slate-900/90 text-slate-300 border border-slate-700 px-1 rounded text-[9px] font-mono">
                      {box.estimated_font_height_mm}mm
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Hover Floating Details Card at bottom */}
      {hoveredBox && (
        <div className="absolute bottom-4 left-4 right-4 bg-slate-900/95 border border-slate-700 rounded-xl p-3 shadow-2xl backdrop-blur-md z-30 flex items-center justify-between text-xs animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              hoveredBox.info.status === 'FAIL' ? 'bg-rose-50 dark:bg-rose-950/400/20 text-rose-400' : 'bg-emerald-50 dark:bg-emerald-950/400/20 text-emerald-400'
            }`}>
              <Info className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-200">{hoveredBox.decl.declaration_type}</span>
                <span className="text-[10px] px-2 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                  Confidence: {Math.round(hoveredBox.decl.confidence * 100)}%
                </span>
                {hoveredBox.info.ruleCode && (
                  <span className="text-[10px] px-2 py-0.2 rounded bg-blue-50 dark:bg-blue-950/400/20 text-blue-400 font-semibold">
                    {hoveredBox.info.ruleCode}
                  </span>
                )}
              </div>
              <p className="text-slate-300 font-mono mt-0.5 font-medium">"{hoveredBox.decl.raw_text}"</p>
              {hoveredBox.info.reason && (
                <p className="text-rose-400 font-semibold mt-0.5">⚠️ Violation: {hoveredBox.info.reason}</p>
              )}
            </div>
          </div>
          <button
            onClick={() => onSelectDeclaration(hoveredBox.decl.id)}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-50 dark:bg-blue-950/400 text-white rounded-lg font-medium text-xs shadow"
          >
            Inspect in Panel
          </button>
        </div>
      )}
    </div>
  );
};
