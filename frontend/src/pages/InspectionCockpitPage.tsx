import React, { useState, useEffect } from 'react';
import { ArrowLeft, RefreshCw, Layers, CheckCircle2, AlertOctagon, Scale, ShieldAlert } from 'lucide-react';
import { InspectionDetailResponse, ComplianceStatus } from '../types';
import { api } from '../services/api';
import { EvidenceCanvas } from '../components/EvidenceCanvas';
import { DeclarationsList } from '../components/DeclarationsList';
import { RuleResultsList } from '../components/RuleResultsList';
import { InspectorActionDock } from '../components/InspectorActionDock';

interface InspectionCockpitPageProps {
  inspectionId: string;
  onBack: () => void;
}

export const InspectionCockpitPage: React.FC<InspectionCockpitPageProps> = ({ inspectionId, onBack }) => {
  const [inspection, setInspection] = useState<InspectionDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'rules' | 'declarations'>('rules');
  const [selectedDeclId, setSelectedDeclId] = useState<string | undefined>(undefined);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      const data = await api.getInspection(inspectionId);
      setInspection(data);
    } catch (err) {
      alert('Error fetching inspection: ' + err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [inspectionId]);

  const handleUpdateDeclaration = async (declId: string, updatedRawText: string) => {
    const updated = await api.updateDeclaration(inspectionId, declId, { raw_text: updatedRawText });
    setInspection(updated);
  };

  const handleSubmitOverride = async (ruleId: string, overrideVerdict: ComplianceStatus, reason: string) => {
    if (!inspection) return;
    const updated = await api.submitReview(inspectionId, {
      final_verdict: inspection.overall_compliance,
      inspector_notes: inspection.inspector_notes || 'Inspector manual review override',
      inspector_signature: 'Inspector M. Sharma',
      overrides: [{ rule_id: ruleId, override_verdict: overrideVerdict, override_reason: reason }]
    });
    setInspection(updated);
  };

  const handleFinalizeReview = async (verdict: ComplianceStatus, notes: string) => {
    const updated = await api.submitReview(inspectionId, {
      final_verdict: verdict,
      inspector_notes: notes,
      inspector_signature: 'Inspector M. Sharma'
    });
    setInspection(updated);
  };

  if (loading || !inspection) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400">Loading Inspection Cockpit...</span>
        </div>
      </div>
    );
  }

  const isPass = inspection.overall_compliance === 'PASS';
  const isFail = inspection.overall_compliance === 'FAIL';
  const score = inspection.compliance_scorecard;

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-slate-950">
      {/* Top Cockpit Header */}
      <div className="px-6 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between z-20 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">{inspection.commodity_name}</h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {inspection.inspection_number}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>{inspection.commodity_category}</span>
              <span>•</span>
              <span>PDP Area: <strong className="text-slate-200">{inspection.pdp_area_sq_cm} cm²</strong></span>
              <span>•</span>
              <span>Batch: <strong className="text-slate-200">{inspection.batch_number || 'N/A'}</strong></span>
            </div>
          </div>
        </div>

        {/* Status Scorecard Pill */}
        <div className="flex items-center gap-3">
          {isPass ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/400/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4" />
              FULLY COMPLIANT
            </div>
          ) : isFail ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 dark:bg-rose-950/400/10 border border-rose-500/20 text-rose-400 text-xs font-bold animate-pulse">
              <AlertOctagon className="w-4 h-4" />
              {score.failed_count} STATUTORY VIOLATIONS
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/400/10 border border-amber-500/20 text-amber-400 text-xs font-bold">
              MANUAL VERIFICATION REQUIRED
            </div>
          )}

          <button
            onClick={fetchDetail}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-xs flex items-center gap-1"
            title="Refresh Inspection Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Split-Screen Workstation */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Column: Evidence Canvas (7 cols = ~58%) */}
        <div className="lg:col-span-7 p-4 h-full overflow-hidden flex flex-col">
          <EvidenceCanvas
            imageUrl={inspection.image_url}
            declarations={inspection.declarations}
            ruleResults={score.results}
            selectedDeclId={selectedDeclId}
            onSelectDeclaration={(id) => {
              setSelectedDeclId(id);
              setActiveTab('declarations');
            }}
          />
        </div>

        {/* Right Column: Tabbed Review Panel (5 cols = ~42%) */}
        <div className="lg:col-span-5 border-l border-slate-800 h-full flex flex-col bg-slate-900/40">
          {/* Panel Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-900 px-4 pt-3 gap-2">
            <button
              onClick={() => setActiveTab('rules')}
              className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'rules'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Scale className="w-4 h-4" />
              Rule Engine Results ({score.results.length})
            </button>
            <button
              onClick={() => setActiveTab('declarations')}
              className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-1.5 ${
                activeTab === 'declarations'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              Extracted Declarations ({inspection.declarations.length})
            </button>
          </div>

          {/* Panel Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'rules' ? (
              <RuleResultsList
                results={score.results}
                onSelectEvidenceBox={(box) => {
                  const match = inspection.declarations.find(d => 
                    Math.abs(d.bounding_box.ymin - box.ymin) < 0.05
                  );
                  if (match) setSelectedDeclId(match.id);
                }}
                onSubmitOverride={handleSubmitOverride}
              />
            ) : (
              <DeclarationsList
                declarations={inspection.declarations}
                selectedDeclId={selectedDeclId}
                onSelectDeclaration={setSelectedDeclId}
                onUpdateDeclaration={handleUpdateDeclaration}
              />
            )}
          </div>
        </div>
      </div>

      {/* Sticky Bottom Action Dock */}
      <InspectorActionDock
        inspectionId={inspection.id}
        inspectionNumber={inspection.inspection_number}
        overallCompliance={inspection.overall_compliance}
        onFinalizeReview={handleFinalizeReview}
      />
    </div>
  );
};
