const VALID_IMAGE_EXTENSIONS = [
  'jpg', 'jpeg', 'jfif', 'png', 'webp', 'heic', 'heif', 'hif', 'avif',
  'tif', 'tiff', 'bmp', 'dib', 'gif', 'ico', 'ppm', 'pgm', 'pbm', 'pnm',
  'jp2', 'j2k', 'jpf', 'jpx', 'tga', 'psd'
];

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileImage,
  AlertCircle,
  CheckCircle2,
  RotateCcw,
  Trash2,
  Zap,
  Check,
  Info,
  Scale,
  ArrowLeft,
  ArrowRight
} from 'lucide-react';
import { inspectionApi } from '../api/inspection';
import { complianceApi } from '../api/compliance';
import { ApiClientError } from '../api/client';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

interface ScanProductPageProps {
  onViewResult?: (inspectionId: string) => void;
  onGoBack?: () => void;
}

export const ScanProductPage: React.FC<ScanProductPageProps> = ({ onViewResult, onGoBack }) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageDims, setImageDims] = useState<{ width: number; height: number } | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [allStepsDone, setAllStepsDone] = useState<boolean>(false);
  const [error, setError] = useState<{ title?: string; message: string; tip?: string } | null>(null);

  // E-Commerce Marketplace Listing Check
  const [enableEcom, setEnableEcom] = useState<boolean>(false);
  const [ecomMarketplace, setEcomMarketplace] = useState<string>('');
  const [ecomPrice, setEcomPrice] = useState<string>('');
  const [ecomQty, setEcomQty] = useState<string>('');
  const [ecomOrigin, setEcomOrigin] = useState<string>('India');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps: string[] = [
    'Image quality check',
    'Preparing image',
    'Extracting evidence',
    'Reconciling evidence',
    'Evaluating applicable rules',
    'Preparing evidence',
    'Inspection ready',
  ];

  const handleFileSelection = (selectedFile: File) => {
    setError(null);

    // Validate size (< 15MB)
    if (selectedFile.size > 15 * 1024 * 1024) {
      setError({
        title: 'File is too large',
        message: `Package image exceeds 15MB limit (${(selectedFile.size / (1024 * 1024)).toFixed(1)}MB).`,
        tip: 'Please select an image file under 15MB.',
      });
      return;
    }

    // Validate image format
    const ext = selectedFile.name.split('.').pop()?.toLowerCase() || '';
    const isImage = selectedFile.type ? selectedFile.type.startsWith('image/') : VALID_IMAGE_EXTENSIONS.includes(ext);
    if (!isImage && !VALID_IMAGE_EXTENSIONS.includes(ext)) {
      setError({
        title: 'Unsupported file format',
        message: `Format '.${ext}' is not supported.`,
        tip: 'Please upload a JPG, PNG, TIFF, or standard package image.',
      });
      return;
    }

    setFile(selectedFile);

    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    const img = new Image();
    img.onload = () => {
      setImageDims({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.src = url;
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    try {
      setAnalyzing(true);
      setError(null);
      setCurrentStepIndex(0); // Image quality check

      // Step 1: Upload image
      const uploadRes = await inspectionApi.uploadImage(file);
      setCurrentStepIndex(1); // Preparing image

      // Step 2: Trigger Spatial OCR
      await inspectionApi.extractOcr(uploadRes.inspection_id);
      setCurrentStepIndex(2); // Extracting evidence

      // Step 3: Trigger Vision AI Extraction & Reconciliation
      await inspectionApi.extractDeclarations(uploadRes.inspection_id);
      setCurrentStepIndex(3); // Reconciling evidence

      // Step 4: Evaluate Legal Compliance Rules
      setCurrentStepIndex(4); // Evaluating applicable rules
      await complianceApi.evaluateCompliance(
        uploadRes.inspection_id,
        'packaged_commodity',
        '2026.1'
      );

      // Step 4b: Optional Dual E-Commerce Listing Comparison
      if (enableEcom && (ecomPrice || ecomQty || ecomMarketplace)) {
        try {
          await inspectionApi.compareListing(uploadRes.inspection_id, {
            marketplace_name: ecomMarketplace || 'E-Commerce Marketplace',
            listed_price: ecomPrice ? `₹${ecomPrice.replace('₹', '').trim()}` : undefined,
            listed_net_quantity: ecomQty || undefined,
            listed_country_of_origin: ecomOrigin || undefined,
          });
        } catch (ecomErr) {
          console.warn('Listing comparison non-blocking warning:', ecomErr);
        }
      }

      setCurrentStepIndex(5);
      await new Promise(r => setTimeout(r, 400));
      setCurrentStepIndex(6);
      await new Promise(r => setTimeout(r, 450));
      // Mark all steps as complete with checkmark before transitioning
      setAllStepsDone(true);
      await new Promise(r => setTimeout(r, 1100));
      if (onViewResult) {
        onViewResult(uploadRes.inspection_id);
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError({
          title: 'Inspection failed',
          message: err.message,
          tip: 'Ensure the image is clear, well-lit, and shows text declarations visibly.',
        });
      } else {
        setError({
          title: 'Unable to analyze package',
          message: err instanceof Error ? err.message : 'An unexpected error occurred during processing.',
          tip: 'Try taking a clearer photo with the package facing the camera directly.',
        });
      }
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setImageDims(null);
    setError(null);
    setCurrentStepIndex(0);
    setAllStepsDone(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Page Header with Back Button */}
      <div className="space-y-1">
        {onGoBack && (
          <button
            onClick={onGoBack}
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors mb-1 cursor-pointer group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back</span>
          </button>
        )}
        <PageHeader
          title="Scan a Product"
          subtitle="Upload a package image to begin inspection under the Legal Metrology (Packaged Commodities) Rules, 2011."
        />
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-xs text-rose-900 space-y-1">
          <div className="flex items-center gap-2 font-semibold text-rose-800 dark:text-rose-300">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error.title || 'Validation error'}</span>
          </div>
          <p className="text-rose-700 pl-6">{error.message}</p>
          {error.tip && (
            <p className="text-rose-600/90 pl-6 text-[11px] italic">Tip: {error.tip}</p>
          )}
        </div>
      )}

      {/* Main Upload / Preview Area */}
      {!file ? (
        /* Clean Upload Dropzone */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-10 text-center transition ${
            isDragging
              ? 'border-blue-700 bg-blue-50/40'
              : 'border-slate-300 bg-white hover:border-slate-400'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelection(e.target.files[0]);
              }
            }}
            className="hidden"
          />

          <div className="w-12 h-12 rounded bg-slate-100 text-slate-700 flex items-center justify-center mx-auto mb-3">
            <UploadCloud className="w-6 h-6 text-blue-900" />
          </div>

          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
            Upload a package image to begin inspection
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
            Drag and drop an image here, or choose a file from your computer
          </p>

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 rounded bg-blue-900 dark:bg-blue-700 hover:bg-blue-950 dark:hover:bg-blue-600 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            Upload Image
          </button>

          <p className="text-[11px] text-slate-400 mt-4">
            Use a clear front/back/side image. Avoid glare and heavy blur.
          </p>
        </div>
      ) : (
        /* Selected File Card & Pipeline Progress */
        <Card padding="md" className="space-y-5">
          {/* File Header Details */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                <FileImage className="w-5 h-5 text-blue-900" />
              </div>
              <div className="truncate">
                <h3 className="text-xs font-bold text-slate-900 truncate max-w-md">
                  {file.name}
                </h3>
                <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono mt-0.5">
                  <span>{formatFileSize(file.size)}</span>
                  {imageDims && (
                    <>
                      <span>•</span>
                      <span>{imageDims.width} × {imageDims.height} px</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Actions: Replace / Remove */}
            {!analyzing && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleReset}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer shadow-xs group"
                  title="Go back to file upload screen"
                >
                  <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform text-slate-400" />
                  <span>Back to Upload</span>
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Replace</span>
                </button>
                <button
                  onClick={handleReset}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition cursor-pointer"
                  title="Remove image"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          {/* Image Preview */}
          <div className="bg-slate-100 rounded border border-slate-200 flex items-center justify-center p-2 max-h-[360px] overflow-hidden">
            {previewUrl && (
              <img
                src={previewUrl}
                alt="Package preview"
                className="max-h-[340px] max-w-full rounded object-contain"
              />
            )}
          </div>

          {/* Stepped Progress Pipeline */}
          {analyzing ? (
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/90 shadow-sm space-y-4">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-900 dark:text-white">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-ping"></span>
                  <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    {allStepsDone ? "Inspection Verified & Ready" : "Executing Statutory Analysis Pipeline..."}
                  </span>
                </span>
                <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400">
                  {allStepsDone ? "100%" : `${Math.round(((currentStepIndex) / steps.length) * 100)}%`}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange-500 via-amber-500 to-emerald-500 transition-all duration-300 rounded-full"
                  style={{ width: `${allStepsDone ? 100 : Math.max(10, Math.round(((currentStepIndex) / steps.length) * 100))}%` }}
                />
              </div>

              {/* Checklist items */}
              <div className="space-y-2.5 pt-1">
                {steps.map((label, idx) => {
                  const isDone = allStepsDone || idx < currentStepIndex;
                  const isCurrent = !allStepsDone && idx === currentStepIndex;
                  return (
                    <div
                      key={label}
                      className={`flex items-center justify-between p-2.5 rounded-lg border transition-all duration-300 ${
                        isDone
                          ? 'bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800/60'
                          : isCurrent
                          ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700 shadow-xs'
                          : 'bg-white/60 dark:bg-slate-800/40 border-slate-100 dark:border-slate-800 opacity-60'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {isDone ? (
                          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-600 text-white font-black text-xs shadow-xs animate-in zoom-in-50">
                            ✓
                          </span>
                        ) : isCurrent ? (
                          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white font-black text-xs animate-pulse">
                            ⏳
                          </span>
                        ) : (
                          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-400 text-xs">
                            {idx + 1}
                          </span>
                        )}
                        <span className={`text-xs font-semibold ${
                          isDone
                            ? 'text-emerald-800 dark:text-emerald-300'
                            : isCurrent
                            ? 'text-blue-900 dark:text-blue-300 font-bold'
                            : 'text-slate-500 dark:text-slate-400'
                        }`}>
                          {label}
                        </span>
                      </div>
                      <span className="text-[11px] font-mono font-medium text-slate-400">
                        {isDone ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-bold">Checked</span>
                        ) : isCurrent ? (
                          <span className="text-blue-600 dark:text-blue-400 font-bold animate-pulse">Running...</span>
                        ) : (
                          <span>Pending</span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>

              {allStepsDone && (
                <div className="p-3 bg-emerald-100 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-700 rounded-lg flex items-center gap-2.5 text-xs font-bold text-emerald-900 dark:text-emerald-200 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>All statutory verification checks completed! Loading inspection dossier...</span>
                </div>
              )}
            </div>
          ) : (
            <>
              {/* Optional Dual E-Commerce Listing Check */}
              <div className="p-3.5 rounded border border-slate-200 bg-slate-50/70 space-y-2.5">
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setEnableEcom(!enableEcom)}
                >
                  <div className="flex items-center gap-2">
                    <Scale className="w-3.5 h-3.5 text-blue-900" />
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-100">
                      Cross-reference with E-Commerce Marketplace Listing (Rule 6(10) / Rule 6(11))
                    </span>
                  </div>
                  <span className="text-[11px] text-blue-900 font-medium hover:underline">
                    {enableEcom ? 'Hide fields' : '+ Add listing claims'}
                  </span>
                </div>

                {enableEcom && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-2 border-t border-slate-200 text-xs">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-600 mb-1">Marketplace</label>
                      <input
                        type="text"
                        placeholder="e.g. Amazon, Blinkit"
                        value={ecomMarketplace}
                        onChange={(e) => setEcomMarketplace(e.target.value)}
                        className="w-full px-2 py-1 rounded border border-slate-300 text-xs bg-white focus:outline-none focus:border-blue-900"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-600 mb-1">Listed Price</label>
                      <input
                        type="text"
                        placeholder="e.g. ₹40.00"
                        value={ecomPrice}
                        onChange={(e) => setEcomPrice(e.target.value)}
                        className="w-full px-2 py-1 rounded border border-slate-300 text-xs bg-white focus:outline-none focus:border-blue-900"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-600 mb-1">Listed Net Qty</label>
                      <input
                        type="text"
                        placeholder="e.g. 140 g"
                        value={ecomQty}
                        onChange={(e) => setEcomQty(e.target.value)}
                        className="w-full px-2 py-1 rounded border border-slate-300 text-xs bg-white focus:outline-none focus:border-blue-900"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-600 mb-1">Country of Origin</label>
                      <input
                        type="text"
                        placeholder="e.g. India"
                        value={ecomOrigin}
                        onChange={(e) => setEcomOrigin(e.target.value)}
                        className="w-full px-2 py-1 rounded border border-slate-300 text-xs bg-white focus:outline-none focus:border-blue-900"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Obvious Primary Action Button */}
              <div className="flex justify-end pt-1">
                <button
                  onClick={handleAnalyze}
                  className="w-full sm:w-auto px-6 py-2.5 rounded bg-blue-900 dark:bg-blue-700 hover:bg-blue-950 dark:hover:bg-blue-600 text-white font-semibold text-xs shadow-xs transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
                  <span>Analyze Product</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  );
};
