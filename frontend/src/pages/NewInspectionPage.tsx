import React, { useState } from 'react';
import { Upload, Camera, Sparkles, CheckCircle2, AlertTriangle, Layers, Ruler, ArrowRight, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

interface NewInspectionPageProps {
  onInspectionCreated: (id: string) => void;
  onCancel: () => void;
}

export const NewInspectionPage: React.FC<NewInspectionPageProps> = ({ onInspectionCreated, onCancel }) => {
  // Real-time custom form inputs
  const [commodityName, setCommodityName] = useState<string>('');
  const [commodityCategory, setCommodityCategory] = useState<string>('Packaged Food');
  const [brandName, setBrandName] = useState<string>('');
  const [batchNumber, setBatchNumber] = useState<string>('');
  const [packageWidth, setPackageWidth] = useState<number>(15.0);
  const [packageHeight, setPackageHeight] = useState<number>(20.0);
  const [isCylindrical, setIsCylindrical] = useState<boolean>(false);
  const [file, setFile] = useState<File | null>(null);

  // Scanning animation state
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanStep, setScanStep] = useState<number>(1);

  // Live PDP Area calculation
  const pdpArea = isCylindrical
    ? Math.round(0.4 * (packageWidth * 3.14159) * packageHeight)
    : Math.round(packageWidth * packageHeight);

  // Schedule II requirement for this PDP
  let reqNumeral = 1.5;
  let reqLetter = 1.0;
  if (pdpArea > 500) {
    reqNumeral = 6.0; reqLetter = 4.0;
  } else if (pdpArea > 100) {
    reqNumeral = 4.0; reqLetter = 2.5;
  } else if (pdpArea > 50) {
    reqNumeral = 2.0; reqLetter = 1.5;
  }

  const handleStartInspection = async () => {
    if (!file) {
      alert('Please select or capture a packaging image for real-time inspection.');
      return;
    }

    try {
      setIsScanning(true);
      setScanStep(1);

      // Simulation steps for realistic scanning visual
      setTimeout(() => setScanStep(2), 700);
      setTimeout(() => setScanStep(3), 1400);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('commodity_name', commodityName || 'Packaged Commodity');
      formData.append('commodity_category', commodityCategory);
      if (brandName) formData.append('brand_name', brandName);
      if (batchNumber) formData.append('batch_number', batchNumber);
      formData.append('package_width_cm', String(packageWidth));
      formData.append('package_height_cm', String(packageHeight));
      formData.append('is_cylindrical', String(isCylindrical));
      formData.append('inspector_name', 'Inspector M. Sharma');

      const res = await api.createInspection(formData);

      setTimeout(() => {
        setIsScanning(false);
        onInspectionCreated(res.id);
      }, 2000);
    } catch (err: any) {
      setIsScanning(false);
      alert('Inspection screening error: ' + err.message);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-orange-500">Real-Time Inspection</span>
        <h1 className="text-2xl font-black text-slate-900 dark:text-white mt-1">Initiate Package Compliance Screening</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Upload or capture a photograph of a pre-packaged commodity for live spatial OCR and statutory rule verification.
        </p>
      </div>

      {/* Live Custom Package Inspection Panel */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 text-center hover:border-orange-500 transition cursor-pointer relative">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              if (e.target.files?.[0]) setFile(e.target.files[0]);
            }}
            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
          />
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-950/60 text-orange-600 flex items-center justify-center">
              <Upload className="w-6 h-6" />
            </div>
            {file ? (
              <div>
                <span className="text-sm font-bold text-slate-900 dark:text-white block">{file.name}</span>
                <span className="text-xs text-emerald-600 font-medium">Ready for real-time legal metrology screening</span>
              </div>
            ) : (
              <div>
                <span className="text-sm font-bold text-slate-900 dark:text-white block">Drop high-resolution packaging photo here</span>
                <span className="text-xs text-slate-400">Supports JPEG, PNG, WEBP, HEIC, TIFF from camera or scanner</span>
              </div>
            )}
          </div>
        </div>

        {/* Input Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Commodity / Generic Name</label>
            <input
              type="text"
              placeholder="e.g. Wheat Flour / Atta"
              value={commodityName}
              onChange={(e) => setCommodityName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
            />
          </div>
          <div>
            <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Commodity Category</label>
            <select
              value={commodityCategory}
              onChange={(e) => setCommodityCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
            >
              <option value="Packaged Food">Packaged Food & Staples</option>
              <option value="Dairy Products">Dairy Products & Ghee</option>
              <option value="Edible Oils">Edible Oils & Fats</option>
              <option value="Beverages">Beverages & Juices</option>
              <option value="Personal Care">Personal Care & Cosmetics</option>
              <option value="General Packaged Commodity">General Packaged Commodity</option>
            </select>
          </div>
          <div>
            <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Brand Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Aashirvaad, Amul, Parle"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
            />
          </div>
          <div>
            <label className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Batch / Lot Code (Optional)</label>
            <input
              type="text"
              placeholder="e.g. B.No. 4029"
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
            />
          </div>
        </div>

        {/* Dimension & Schedule II PDP Area Calculator */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
              <Ruler className="w-4 h-4 text-orange-600" />
              Principal Display Panel (PDP) Dimensions
            </span>
            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-600 dark:text-slate-400">
              <input
                type="checkbox"
                checked={isCylindrical}
                onChange={(e) => setIsCylindrical(e.target.checked)}
                className="rounded text-orange-600"
              />
              <span>Cylindrical Package</span>
            </label>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-500 block">Width (cm)</span>
              <input
                type="number"
                step="0.5"
                value={packageWidth}
                onChange={(e) => setPackageWidth(parseFloat(e.target.value) || 1)}
                className="w-full mt-1 px-2.5 py-1.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
              />
            </div>
            <div>
              <span className="text-slate-500 block">Height (cm)</span>
              <input
                type="number"
                step="0.5"
                value={packageHeight}
                onChange={(e) => setPackageHeight(parseFloat(e.target.value) || 1)}
                className="w-full mt-1 px-2.5 py-1.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
              />
            </div>
            <div>
              <span className="text-slate-500 block">Computed PDP</span>
              <div className="mt-1 font-mono font-bold text-slate-900 dark:text-white py-1.5">{pdpArea} cm²</div>
            </div>
            <div>
              <span className="text-slate-500 block">Schedule II Min Font</span>
              <div className="mt-1 font-mono font-bold text-orange-600 dark:text-orange-400 py-1.5">
                {reqNumeral} mm (numeral)
              </div>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleStartInspection}
            disabled={isScanning}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-xs shadow-md flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isScanning ? `Screening Package (Step ${scanStep}/3)...` : 'Run Real-Time Statutory Inspection'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
