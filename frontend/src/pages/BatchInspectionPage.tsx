const VALID_IMAGE_EXTENSIONS = [
  'jpg', 'jpeg', 'jfif', 'png', 'webp', 'heic', 'heif', 'hif', 'avif',
  'tif', 'tiff', 'bmp', 'dib', 'gif', 'ico', 'ppm', 'pgm', 'pbm', 'pnm',
  'jp2', 'j2k', 'jpf', 'jpx', 'tga', 'psd'
];

import React, { useState, useRef } from 'react';
import {
  Layers,
  UploadCloud,
  FileImage,
  AlertOctagon,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  ArrowRight,
  RefreshCw,
  X
} from 'lucide-react';
import { batchApi } from '../api/batch';
import { BatchInspectionItem, BatchInspectionResponse } from '../types/batch';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

interface BatchInspectionPageProps {
  onSelectInspection: (inspectionId: string) => void;
}

export const BatchInspectionPage: React.FC<BatchInspectionPageProps> = ({
  onSelectInspection,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [batchResponse, setBatchResponse] = useState<BatchInspectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [sortBy, setSortBy] = useState<'risk' | 'status'>('risk');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);

    const validFiles: File[] = [];
    const maxFiles = 20;

    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      if (validFiles.length >= maxFiles) break;

      const ext = f.name.split('.').pop()?.toLowerCase() || '';
      const isImage = f.type ? f.type.startsWith('image/') : VALID_IMAGE_EXTENSIONS.includes(ext);
      if (isImage || VALID_IMAGE_EXTENSIONS.includes(ext)) {
        validFiles.push(f);
      }
    }

    if (validFiles.length === 0) {
      setError('Please select valid package images (JPG, PNG, TIFF, WEBP).');
      return;
    }

    setSelectedFiles((prev) => {
      const combined = [...prev, ...validFiles];
      return combined.slice(0, 20);
    });
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    setBatchResponse(null);
    setError(null);
  };

  const handleRunBatch = async () => {
    if (selectedFiles.length === 0) return;

    try {
      setUploading(true);
      setError(null);

      const resp = await batchApi.uploadBatch(selectedFiles, 'packaged_commodity', '2026.1');
      setBatchResponse(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Batch processing encountered an error');
    } finally {
      setUploading(false);
    }
  };

  const sortedResults = [...(batchResponse?.results || [])].sort((a, b) => {
    if (sortBy === 'risk') {
      return sortAsc ? a.risk_score - b.risk_score : b.risk_score - a.risk_score;
    }
    if (sortBy === 'status') {
      return sortAsc ? a.status.localeCompare(b.status) : b.status.localeCompare(a.status);
    }
    return 0;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <PageHeader
        title="Batch Scan"
        subtitle="Upload multiple packaged commodities for concurrent compliance screening."
      />

      {error && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center gap-2.5">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Zone */}
      <Card padding="md" className="space-y-4">
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files) handleFiles(e.dataTransfer.files);
          }}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
            isDragging
              ? 'border-blue-700 bg-blue-50/40'
              : 'border-slate-300 bg-white hover:border-slate-400'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => handleFiles(e.target.files)}
            className="hidden"
          />

          <div className="w-10 h-10 rounded bg-slate-100 text-slate-700 flex items-center justify-center mx-auto mb-2">
            <Layers className="w-5 h-5 text-blue-900" />
          </div>

          <h3 className="text-xs font-semibold text-slate-900 dark:text-white">
            Select up to 20 package images for batch inspection
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5 mb-3">
            Drag and drop images, or choose files from your computer
          </p>

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-3.5 py-1.5 rounded bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            Select Files
          </button>
        </div>

        {/* Selected Files Queue */}
        {selectedFiles.length > 0 && (
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-900 dark:text-white">
                Files selected: <strong className="font-mono text-blue-900">{selectedFiles.length}</strong> / 20
              </span>
              <button
                onClick={clearAllFiles}
                className="text-slate-500 hover:text-rose-600 text-[11px] font-medium"
              >
                Clear all
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
              {selectedFiles.map((f, i) => (
                <div key={i} className="p-2 rounded border border-slate-200 bg-slate-50 relative group flex items-center gap-1.5 truncate">
                  <FileImage className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="text-[11px] text-slate-700 truncate">{f.name}</span>
                  <button
                    onClick={() => removeFile(i)}
                    className="absolute right-1 text-slate-400 hover:text-rose-600 p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleRunBatch}
                disabled={uploading}
                className="px-4 py-2 rounded bg-blue-900 hover:bg-blue-950 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition flex items-center gap-2 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${uploading ? 'animate-spin' : ''}`} />
                <span>{uploading ? 'Processing batch...' : `Analyze ${selectedFiles.length} Products`}</span>
              </button>
            </div>
          </div>
        )}
      </Card>

      {/* Batch Results Ledger */}
      {batchResponse && (
        <Card padding="none" className="overflow-hidden space-y-0">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Batch Results: {batchResponse.total} Products Analyzed
              </h3>
              <div className="flex items-center gap-3 text-xs text-slate-600 mt-0.5 font-medium">
                <span className="text-emerald-700 dark:text-emerald-400">✓ {batchResponse.compliant_count} Compliant</span>
                <span>•</span>
                <span className="text-rose-700 dark:text-rose-400">✕ {batchResponse.potential_violations_count} Potential Issues</span>
                <span>•</span>
                <span className="text-amber-700 dark:text-amber-400">⚠ {batchResponse.manual_review_count} Needs Review</span>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Sort by:</span>
              <button
                onClick={() => setSortBy('risk')}
                className={`px-2 py-1 rounded border text-[11px] font-medium ${
                  sortBy === 'risk' ? 'bg-blue-900 text-white border-blue-900' : 'bg-white text-slate-600 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500'
                }`}
              >
                Risk
              </button>
              <button
                onClick={() => setSortBy('status')}
                className={`px-2 py-1 rounded border text-[11px] font-medium ${
                  sortBy === 'status' ? 'bg-blue-900 text-white border-blue-900' : 'bg-white text-slate-600 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500'
                }`}
              >
                Status
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                  <th className="py-2.5 px-4">Product Asset</th>
                  <th className="py-2.5 px-3">Inspection ID</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Issues Detected</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {sortedResults.map((res) => (
                  <tr
                    key={res.inspection_id}
                    onClick={() => res.inspection_id && onSelectInspection(res.inspection_id)}
                    className="hover:bg-slate-50 cursor-pointer transition"
                  >
                    <td className="py-2.5 px-4 font-medium text-slate-900 truncate max-w-[200px]">
                      {res.filename}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">
                      {res.inspection_id}
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={res.status} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold">
                      {res.risk_score} <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
                      {res.violations_count > 0 ? (
                        <span className="text-rose-700 font-medium">
                          {res.violations_count} violation(s)
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">None</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <span className="text-xs font-semibold text-blue-900 hover:underline inline-flex items-center gap-1">
                        <span>Inspect</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
