import React, { useState } from 'react';
import { ExtractedDeclarationDTO } from '../types';
import { Edit3, Check, AlertCircle, Sparkles, Tag, Eye } from 'lucide-react';

interface DeclarationsListProps {
  declarations: ExtractedDeclarationDTO[];
  selectedDeclId?: string;
  onSelectDeclaration: (id: string) => void;
  onUpdateDeclaration: (declId: string, updatedRawText: string) => Promise<void>;
}

export const DeclarationsList: React.FC<DeclarationsListProps> = ({
  declarations,
  selectedDeclId,
  onSelectDeclaration,
  onUpdateDeclaration
}) => {
  const [editingDecl, setEditingDecl] = useState<ExtractedDeclarationDTO | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const handleStartEdit = (decl: ExtractedDeclarationDTO, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingDecl(decl);
    setEditText(decl.raw_text);
  };

  const handleSaveEdit = async () => {
    if (!editingDecl) return;
    try {
      setIsSaving(true);
      await onUpdateDeclaration(editingDecl.id, editText);
      setEditingDecl(null);
    } catch (err) {
      alert('Failed to update declaration: ' + err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-3 p-1">
      <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
        <span>Transcribed Entities ({declarations.length})</span>
        <span>Click to inspect or correct OCR</span>
      </div>

      <div className="space-y-2.5">
        {declarations.map(decl => {
          const isSelected = selectedDeclId === decl.id;
          const confPct = Math.round(decl.confidence * 100);

          let confColor = 'bg-emerald-50 dark:bg-emerald-950/400';
          if (confPct < 85) confColor = 'bg-amber-50 dark:bg-amber-950/400';
          if (confPct < 70) confColor = 'bg-rose-50 dark:bg-rose-950/400';

          return (
            <div
              key={decl.id}
              onClick={() => onSelectDeclaration(decl.id)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer group ${
                isSelected
                  ? 'bg-blue-950/40 border-blue-500 ring-1 ring-blue-500/50 shadow-lg'
                  : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-200 tracking-wide flex items-center gap-1.5">
                    <Tag className="w-3 h-3 text-blue-400" />
                    {decl.declaration_type.replace(/_/g, ' ')}
                  </span>
                  {decl.is_manually_edited && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-50 dark:bg-purple-950/400/20 text-purple-300 border border-purple-500/30">
                      Edited
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {/* Confidence meter */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-mono">{confPct}%</span>
                    <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${confColor}`} style={{ width: `${confPct}%` }}></div>
                    </div>
                  </div>

                  {/* Edit button */}
                  <button
                    onClick={(e) => handleStartEdit(decl, e)}
                    className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
                    title="Correct transcription"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Raw OCR Text */}
              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60 text-xs font-mono text-slate-300 break-words">
                "{decl.raw_text}"
              </div>

              {/* Normalized Value & Font Height */}
              <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
                <span className="text-slate-300">
                  Value: <strong className="text-white">{String(decl.normalized_value)}</strong>
                </span>
                {decl.bounding_box.estimated_font_height_mm && (
                  <span className="font-mono text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
                    Font: <span className="text-amber-400">{decl.bounding_box.estimated_font_height_mm}mm</span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Edit Modal */}
      {editingDecl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
                <Edit3 className="w-4 h-4 text-blue-400" />
                Correct Declaration Transcription
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/400/10 text-blue-400 border border-blue-500/20">
                {editingDecl.declaration_type}
              </span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                Transcribed Text (Verbatim from package):
              </label>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-200 font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Saving will automatically re-run the deterministic legal rule engine.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setEditingDecl(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                disabled={isSaving}
                onClick={handleSaveEdit}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-50 dark:bg-blue-950/400 text-white shadow-lg shadow-blue-500/20 disabled:opacity-50"
              >
                {isSaving ? 'Recalculating Rules...' : 'Save & Re-Evaluate'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
