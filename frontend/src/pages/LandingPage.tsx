import React, { useState, useEffect, useRef } from 'react';
import {
  Scale, ShieldCheck, Cpu, FileCheck, ArrowRight, Eye, Database, Lock,
  ChevronRight, Sparkles, Award, Zap, CheckCircle, BarChart3, Package,
  Scan, AlertTriangle, TrendingUp, Globe, Utensils, Wheat, Check,
  ExternalLink, ChevronDown, RefreshCw
} from 'lucide-react';

interface LandingPageProps {
  onStartInspection: () => void;
  onExploreDashboard: () => void;
  onOpenLogin: () => void;
  onSelectDemo: (demoId: string) => void;
}

function useCountUp(target: number, duration = 1800, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime: number | null = null;
    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(step);
      else setCount(target);
    };
    requestAnimationFrame(step);
  }, [target, duration, start]);
  return count;
}

const statItems = [
  { label: 'Statutory Rules Verified', value: 18, suffix: '+', color: 'text-orange-500', desc: 'From PCR 2011 & Gazette Orders' },
  { label: 'PCR Compliance Checks', value: 100, suffix: '%', color: 'text-emerald-500', desc: 'Pre-packaged food & commodities' },
  { label: 'Gazette Amendments Tracked', value: 14, suffix: '', color: 'text-blue-500', desc: 'Continuous Ministry sync' },
  { label: 'Inspection Speed (seconds)', value: 45, suffix: 's', color: 'text-amber-500', desc: 'Instant AI audit dossier' },
];

const workflowSteps = [
  {
    num: '01',
    icon: <Scan className="w-5 h-5" />,
    label: 'Capture Evidence',
    desc: 'Capture or upload high-resolution food packaging label imagery via camera or file upload.',
    color: 'from-blue-500 to-blue-700',
    light: 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700'
  },
  {
    num: '02',
    icon: <Cpu className="w-5 h-5" />,
    label: 'Extract Declarations',
    desc: 'Spatial OCR + Qwen Vision AI extract MRP, Net Qty, Dates, Veg Mark, FSSAI, and Manufacturer details.',
    color: 'from-orange-500 to-amber-600',
    light: 'bg-orange-50 dark:bg-orange-950/40 border-orange-300 dark:border-orange-700'
  },
  {
    num: '03',
    icon: <Database className="w-5 h-5" />,
    label: 'Verify Metrology Rules',
    desc: 'Deterministic rule engine evaluates evidence strictly against PCR 2011 statutory provisions.',
    color: 'from-emerald-500 to-teal-700',
    light: 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-700'
  },
  {
    num: '04',
    icon: <Eye className="w-5 h-5" />,
    label: 'Inspector Review',
    desc: 'Human officers attest low-confidence findings with digital signature and complete audit traceability.',
    color: 'from-amber-500 to-yellow-600',
    light: 'bg-amber-50 dark:bg-amber-950/40 border-amber-300 dark:border-amber-700'
  },
  {
    num: '05',
    icon: <FileCheck className="w-5 h-5" />,
    label: 'Enforcement Report',
    desc: 'Generate court-ready Legal Metrology Inspection Reports with statutory citation for field officers.',
    color: 'from-violet-500 to-purple-700',
    light: 'bg-violet-50 dark:bg-violet-950/40 border-violet-300 dark:border-violet-700'
  },
];

const pillars = [
  {
    icon: <Scale className="w-6 h-6" />,
    title: 'Official Legal Sources',
    desc: 'Every rule links directly to the Legal Metrology Act, 2009 & PCR 2011 published on consumeraffairs.gov.in. Versioned, auditable, and court-submissible.',
    accent: 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
    tag: 'Statutory Authority'
  },
  {
    icon: <Eye className="w-6 h-6" />,
    title: 'Absence ≠ Violation',
    desc: 'OCR unreadability, glare, or label folds are classified as UNABLE TO VERIFY — never falsely penalizing manufacturers without physical human verification.',
    accent: 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
    tag: 'Inspector-Safe'
  },
  {
    icon: <Lock className="w-6 h-6" />,
    title: 'Tamper-Evident Audit Dossier',
    desc: 'All perception outputs, OCR bounding coordinates, rule evaluations, and officer overrides are immutably logged for legal enforcement transparency.',
    accent: 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
    tag: 'Court-Ready'
  },
];

interface CommodityInfo {
  name: string;
  category: string;
  sampleItem: string;
  mandatoryRules: string[];
  unitRule: string;
}

const commodityCategories: Record<string, CommodityInfo> = {
  '🌾 Packaged Grains & Flour': {
    name: 'Packaged Grains & Flour',
    category: 'Staples',
    sampleItem: 'Atta / Rice / Pulses (1kg, 5kg, 10kg)',
    mandatoryRules: ['Net Quantity (kg/g standard symbol)', 'MRP incl. of all taxes', 'Best Before / Expiry', 'FSSAI License No.', 'Veg Logo Mark'],
    unitRule: 'Rule 11 & Schedule II: Mandatory metric symbols without pluralization (e.g., kg not kgs)'
  },
  '🥛 Dairy & Milk Products': {
    name: 'Dairy & Milk Products',
    category: 'Perishables',
    sampleItem: 'Packaged Milk / Butter / Ghee / Paneer',
    mandatoryRules: ['Date of Packing & Use By', 'Storage Temperature Advisory', 'Net Quantity (ml/L/g)', 'FSSAI License', 'Unit Sale Price'],
    unitRule: 'Rule 6(1)(d): Month & Year of packing + exact storage instructions'
  },
  '🫙 Edible Oils & Ghee': {
    name: 'Edible Oils & Ghee',
    category: 'Cooking Essentials',
    sampleItem: 'Mustard / Sunflower / Groundnut Oil Pouch',
    mandatoryRules: ['Net Qty in Volume AND Mass', 'Batch / Lot Number', 'Free from Argemone Oil declaration', 'MRP inclusive of all taxes'],
    unitRule: 'Rule 13: Packaging in standard metric volume (L/ml) with temperature declaration'
  },
  '🍪 Biscuits & Bakery': {
    name: 'Biscuits & Bakery',
    category: 'Packaged Snacks',
    sampleItem: 'Glucose / Marie Biscuits / Rusks',
    mandatoryRules: ['Unit Sale Price (USP per gram)', 'Nutritional Information table', 'List of Ingredients in descending order', 'Green Veg Dot'],
    unitRule: 'Rule 6(11): Unit Sale Price (USP) mandatory when net quantity exceeds 100g'
  },
  '🌶️ Spices & Condiments': {
    name: 'Spices & Condiments',
    category: 'Grocery',
    sampleItem: 'Turmeric / Red Chilli Powder / Garam Masala',
    mandatoryRules: ['AGMARK / FSSAI Quality Grade', 'Net Weight with font height compliance (Rule 7)', 'Customer Care Address & Email', 'Country of Origin'],
    unitRule: 'Rule 7: Minimum font height proportional to package area'
  },
  '🥤 Beverages & Juices': {
    name: 'Beverages & Juices',
    category: 'Ready to Drink',
    sampleItem: 'Packaged Drinking Water / Fruit Juices / Tea',
    mandatoryRules: ['Net Volume in ml / L', 'Crush bottle after use notice', 'Date of Manufacture & Best Before', 'Customer Helpline'],
    unitRule: 'Rule 6(1)(e): MRP strictly inclusive of all taxes across online and offline retail'
  }
};

const ruleCatalogItems = [
  {
    rule: 'Rule 6(1)(a)',
    title: 'Manufacturer / Packer / Importer Identity & Address',
    statute: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    description: 'Every package must clearly declare the registered name and complete postal address of the manufacturer or packer.',
    foodRelevance: 'Enables consumer traceability and swift food safety recall if required.'
  },
  {
    rule: 'Rule 6(1)(b)',
    title: 'Net Quantity in Standard Units of Mass or Measure',
    statute: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    description: 'Declaration of net weight, measure or number using standard metric units (g, kg, ml, L) without plurals.',
    foodRelevance: 'Protects consumers from short-weight deception in grains, pulses, dairy, and oils.'
  },
  {
    rule: 'Rule 6(1)(e)',
    title: 'Maximum Retail Price (MRP) Inclusive of All Taxes',
    statute: 'PCR 2011 Rule 6(1)(e) & Gazette Amendment 2022',
    description: 'Sale price declared as "Maximum Retail Price" or "MRP" with clear tax-inclusive notation.',
    foodRelevance: 'Prevents price gouging and unlawful overcharging on essential packaged food items.'
  },
  {
    rule: 'Rule 6(11)',
    title: 'Mandatory Unit Sale Price (USP) for Food Packages > 100g/ml',
    statute: 'PCR 2011 Amendment GSR 779(E)',
    description: 'Mandatory declaration of Unit Sale Price (e.g. ₹/g, ₹/kg, ₹/ml) to allow easy comparison.',
    foodRelevance: 'Allows consumers to compare relative costs across different package sizes transparently.'
  },
  {
    rule: 'Rule 6(1)(g)',
    title: 'Country of Origin Declaration',
    statute: 'PCR 2011 Rule 6(1)(g)',
    description: 'Mandatory country of origin declaration for all domestic and imported packaged commodities.',
    foodRelevance: 'Ensures origin authenticity for imported confectioneries, dry fruits, and specialty foods.'
  },
  {
    rule: 'FSSAI & Rule 6(1)(d)',
    title: 'Date of Packing, Best Before & Food Safety License',
    statute: 'FSSAI Packaging Regulations & Legal Metrology Harmonization',
    description: 'Month and year of manufacture/packing together with expiry/best before timeline and 14-digit FSSAI license.',
    foodRelevance: 'Guarantees shelf life safety and certified hygienic processing standards.'
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartInspection,
  onExploreDashboard,
  onOpenLogin,
}) => {
  const [statsVisible, setStatsVisible] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [hoveredPillar, setHoveredPillar] = useState<number | null>(null);
  const [selectedCommodity, setSelectedCommodity] = useState<string>('🌾 Packaged Grains & Flour');
  const [expandedRule, setExpandedRule] = useState<string | null>('Rule 6(1)(e)');
  const [mockScanStep, setMockScanStep] = useState<number>(2);

  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) setStatsVisible(true);
    }, { threshold: 0.3 });
    if (statsRef.current) obs.observe(statsRef.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    const t = setInterval(() => setActiveStep(s => (s + 1) % workflowSteps.length), 2800);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setMockScanStep(s => (s + 1) % 4), 3000);
    return () => clearInterval(t);
  }, []);

  const c0 = useCountUp(statItems[0].value, 1800, statsVisible);
  const c1 = useCountUp(statItems[1].value, 1800, statsVisible);
  const c2 = useCountUp(statItems[2].value, 1800, statsVisible);
  const c3 = useCountUp(statItems[3].value, 1800, statsVisible);
  const counts = [c0, c1, c2, c3];

  const currentCommodityInfo = commodityCategories[selectedCommodity];

  return (
    <div className="min-h-full bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-x-hidden selection:bg-orange-500 selection:text-white">

      {/* Top Advisory Bar */}
      <div className="bg-slate-900 text-slate-200 text-xs sm:text-sm py-2.5 px-4 sm:px-8 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shrink-0 shadow-xs shadow-emerald-400" />
          <span className="font-bold text-white tracking-wide truncate">
            Government of India &bull; Department of Consumer Affairs
          </span>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-amber-400 hidden md:inline font-medium">
            Legal Metrology (Packaged Commodities) Rules, 2011
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <a
            href="https://consumeraffairs.gov.in/pages/legal-metrology-act"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-semibold transition underline underline-offset-2"
          >
            <span>consumeraffairs.gov.in</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <span className="bg-orange-500/20 text-orange-300 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border border-orange-500/40">
            OFFICIAL PORTAL READY
          </span>
        </div>
      </div>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 px-4 sm:px-8">
        {/* Ambient Warm Gradients fitting food & regulatory packaging */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -top-32 -left-32 w-[550px] h-[550px] rounded-full bg-orange-500/15 dark:bg-orange-500/10 blur-3xl animate-pulse duration-1000" />
          <div className="absolute -top-20 -right-20 w-[450px] h-[450px] rounded-full bg-amber-500/15 dark:bg-amber-500/10 blur-3xl" />
          <div className="absolute top-[50%] left-[25%] w-[350px] h-[350px] rounded-full bg-emerald-500/10 dark:bg-emerald-500/5 blur-3xl" />
        </div>

        <div className="relative max-w-6xl mx-auto space-y-10">
          {/* Top Pill */}
          <div className="flex justify-center">
            <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-orange-50 dark:bg-orange-950/60 border border-orange-300 dark:border-orange-800/80 text-orange-900 dark:text-orange-200 text-sm font-bold shadow-xs hover:border-orange-400 transition cursor-default">
              <Scale className="w-4 h-4 text-orange-600 dark:text-orange-400 animate-bounce" />
              <span>AI-Assisted Legal Metrology Packaging Inspection System</span>
              <span className="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
              <span className="text-xs text-orange-700 dark:text-orange-300 font-mono">Rule 6 &amp; Schedule II</span>
            </div>
          </div>

          {/* Main Title & Subtitle */}
          <div className="text-center space-y-5 max-w-4xl mx-auto">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.1]">
              PARAKH{' '}
              <span className="relative inline-block">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-600 via-amber-500 to-emerald-600">
                  AI
                </span>
                <span className="absolute -bottom-1.5 left-0 w-full h-1.5 rounded-full bg-gradient-to-r from-orange-500 via-amber-400 to-emerald-500 shadow-sm" />
              </span>
            </h1>

            <p className="text-2xl sm:text-3xl font-extrabold text-slate-800 dark:text-slate-100 tracking-tight">
              Pre-Packaged Food &amp; Commodity Regulatory Verification
            </p>

            <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed font-normal">
              Empowering Legal Metrology Officers to verify packaged commodities instantly against{' '}
              <span className="font-bold text-orange-600 dark:text-orange-400 hover:underline cursor-pointer">
                PCR 2011 statutory declarations
              </span>{' '}
              — with explainable OCR bounding evidence, automated unit checks, and zero false violations.
            </p>
          </div>

          {/* Primary Interactive CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={onStartInspection}
              className="group px-8 py-4 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 hover:from-orange-600 hover:to-amber-600 text-white font-black text-lg shadow-xl shadow-orange-500/20 transition-all duration-200 flex items-center gap-2.5 cursor-pointer hover:scale-105 active:scale-100 border border-orange-400/30"
            >
              <Zap className="w-5 h-5 fill-current" />
              <span>Start Package Inspection</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={onExploreDashboard}
              className="group px-7 py-4 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 font-bold text-lg border-2 border-slate-200 dark:border-slate-700 shadow-sm transition-all duration-200 flex items-center gap-2.5 cursor-pointer hover:scale-105 active:scale-100"
            >
              <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span>Enforcement Cockpit</span>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={onOpenLogin}
              className="group px-6 py-4 rounded-xl bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-slate-100 font-bold text-lg border border-slate-700 shadow-sm transition-all duration-200 flex items-center gap-2 cursor-pointer hover:scale-105 active:scale-100"
            >
              <Lock className="w-5 h-5 text-amber-400" />
              <span>Inspector Access</span>
            </button>
          </div>

          {/* Interactive Live Scanner Preview Simulation */}
          <div className="pt-4 max-w-4xl mx-auto">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2.5">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping"></div>
                  <span className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                    Live Spatial Verification Pipeline Preview
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
                  <span>Sample Food Packaging:</span>
                  <span className="font-bold text-orange-600 dark:text-orange-400">Sharbati Whole Wheat Atta 5 kg</span>
                </div>
              </div>

              {/* Mock Scan Visual Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* MRP Check Card */}
                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:border-emerald-400 transition-all cursor-pointer group">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-slate-500">Rule 6(1)(e)</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                      <Check className="w-3 h-3" /> Compliant
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Maximum Retail Price</div>
                  <div className="text-xs font-mono text-emerald-700 dark:text-emerald-400 font-bold mt-1">
                    ₹ 245.00 (Incl. of all taxes)
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">Tax-inclusive wording verified</p>
                </div>

                {/* Net Quantity Card */}
                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:border-emerald-400 transition-all cursor-pointer group">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-slate-500">Rule 6(1)(b) &amp; Rule 11</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                      <Check className="w-3 h-3" /> Valid Unit
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Net Quantity Declaration</div>
                  <div className="text-xs font-mono text-emerald-700 dark:text-emerald-400 font-bold mt-1">
                    Net Qty: 5 kg
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">Standard metric symbol (kg) verified</p>
                </div>

                {/* USP & Food Safety Card */}
                <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 hover:border-emerald-400 transition-all cursor-pointer group">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-slate-500">Rule 6(11) &amp; FSSAI</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                      <Check className="w-3 h-3" /> Verified
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Unit Sale Price &amp; License</div>
                  <div className="text-xs font-mono text-blue-700 dark:text-blue-400 font-bold mt-1">
                    USP: ₹ 49.00 / kg &bull; Lic No: 1001...
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">Mandatory for packaged goods &gt; 100g</p>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Commodity Filter Pills */}
          <div className="space-y-4 pt-4">
            <div className="text-center">
              <span className="text-sm font-extrabold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Select Commodity Category to Inspect Statutory Requirements:
              </span>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2.5">
              {Object.keys(commodityCategories).map((tag) => {
                const isSelected = selectedCommodity === tag;
                return (
                  <button
                    key={tag}
                    onClick={() => setSelectedCommodity(tag)}
                    className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 cursor-pointer flex items-center gap-2 shadow-xs ${
                      isSelected
                        ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/20 scale-105'
                        : 'bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-orange-400 hover:text-orange-600 dark:hover:text-orange-400'
                    }`}
                  >
                    <span>{tag}</span>
                  </button>
                );
              })}
            </div>

            {/* Selected Commodity Requirements Banner */}
            {currentCommodityInfo && (
              <div className="p-5 rounded-2xl bg-amber-50/70 dark:bg-slate-900/90 border-2 border-amber-200 dark:border-amber-800/60 max-w-4xl mx-auto shadow-sm space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 font-black text-slate-900 dark:text-white text-base">
                    <Wheat className="w-5 h-5 text-orange-600" />
                    <span>{currentCommodityInfo.name} Compliance Profile</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 px-2.5 py-1 rounded-md">
                    Target Package: {currentCommodityInfo.sampleItem}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  {currentCommodityInfo.mandatoryRules.map((mr, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-lg bg-white dark:bg-slate-800 border border-amber-300 dark:border-amber-700 text-slate-800 dark:text-slate-200 text-xs font-bold flex items-center gap-1.5 shadow-2xs"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                      {mr}
                    </span>
                  ))}
                </div>
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 pt-1 border-t border-amber-200/60 dark:border-amber-900/60">
                  <span className="font-bold text-orange-700 dark:text-orange-300">Mandatory Rule Note: </span>
                  {currentCommodityInfo.unitRule}
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Counters & Statistics Bar */}
      <div ref={statsRef} className="bg-white dark:bg-slate-900 border-y border-slate-200 dark:border-slate-800 py-12 px-4 sm:px-8">
        <div className="max-w-6xl mx-auto grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          {statItems.map((s, i) => (
            <div
              key={s.label}
              className="p-4 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-all duration-200 cursor-default space-y-2 group"
            >
              <div className={`text-5xl sm:text-6xl font-black ${s.color} tabular-nums group-hover:scale-105 transition-transform`}>
                {counts[i]}{s.suffix}
              </div>
              <div className="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-200 tracking-tight">
                {s.label}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Workflow Section */}
      <section id="how-it-works" className="py-16 px-4 sm:px-8">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <span className="inline-flex items-center gap-1.5 text-sm font-bold uppercase tracking-widest text-orange-600 dark:text-orange-400">
              <Sparkles className="w-4 h-4" />
              Automated Verification Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 dark:text-white">
              Transparent,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500">
                Evidence-Grounded
              </span>{' '}
              Inspection
            </h2>
            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Every declaration check is mapped directly to spatial OCR coordinates and the official Gazette provision on consumeraffairs.gov.in.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
            {workflowSteps.map((step, idx) => (
              <button
                key={step.label}
                onClick={() => setActiveStep(idx)}
                className={`relative p-6 rounded-2xl border-2 text-left space-y-3 transition-all duration-300 cursor-pointer ${
                  activeStep === idx
                    ? `${step.light} shadow-xl scale-105 ring-2 ring-orange-400/40`
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:shadow-md hover:scale-[1.02]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-slate-400 font-mono tracking-widest">
                    STEP {step.num}
                  </span>
                  <span className={`p-2.5 rounded-xl bg-gradient-to-br ${step.color} text-white shadow-xs`}>
                    {step.icon}
                  </span>
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-white mb-1">
                    {step.label}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-normal">
                    {step.desc}
                  </p>
                </div>
                {activeStep === idx && (
                  <div className={`absolute bottom-0 left-0 w-full h-1.5 rounded-b-2xl bg-gradient-to-r ${step.color}`} />
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive Official Rules Catalog Section */}
      <section className="bg-white dark:bg-slate-900 border-y border-slate-200 dark:border-slate-800 py-16 px-4 sm:px-8">
        <div className="max-w-6xl mx-auto space-y-10">
          <div className="text-center space-y-3">
            <span className="inline-flex items-center gap-1.5 text-sm font-bold uppercase tracking-widest text-blue-600 dark:text-blue-400">
              <Globe className="w-4 h-4" />
              Official Regulatory Source
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
              Statutory Provisions from consumeraffairs.gov.in
            </h2>
            <p className="text-base text-slate-600 dark:text-slate-300 max-w-xl mx-auto">
              Click any rule below to explore statutory requirements, applicability, and legal safeguards.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ruleCatalogItems.map((item) => {
              const isExpanded = expandedRule === item.rule;
              return (
                <div
                  key={item.rule}
                  onClick={() => setExpandedRule(isExpanded ? null : item.rule)}
                  className={`p-5 rounded-2xl border-2 transition-all duration-200 cursor-pointer ${
                    isExpanded
                      ? 'bg-orange-50/50 dark:bg-orange-950/20 border-orange-400 dark:border-orange-700 shadow-md'
                      : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 hover:border-orange-300 dark:hover:border-orange-800 hover:shadow-xs'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded font-mono font-bold text-xs bg-orange-100 dark:bg-orange-900/60 text-orange-800 dark:text-orange-200">
                          {item.rule}
                        </span>
                        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                          {item.statute}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-900 dark:text-white">
                        {item.title}
                      </h4>
                    </div>
                    <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                  </div>

                  <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">
                    {item.description}
                  </p>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-orange-200 dark:border-orange-800/60 space-y-1 text-xs">
                      <div className="font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                        <Utensils className="w-3.5 h-3.5" />
                        <span>Food Packaging Application:</span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 leading-normal">
                        {item.foodRelevance}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="text-center pt-2">
            <button
              onClick={onExploreDashboard}
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-base shadow-md transition-all duration-200 cursor-pointer hover:scale-105 active:scale-100"
            >
              <TrendingUp className="w-4 h-4" />
              <span>Explore Rule Catalog &amp; Gazette Amendments</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* 3 Core Pillars */}
      <section className="py-16 px-4 sm:px-8">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <span className="inline-flex items-center gap-1.5 text-sm font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">
              <Award className="w-4 h-4" />
              Government Credibility &amp; Legal Soundness
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
              Engineered for Real-World Field Inspection
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {pillars.map((pillar, i) => (
              <div
                key={pillar.title}
                onMouseEnter={() => setHoveredPillar(i)}
                onMouseLeave={() => setHoveredPillar(null)}
                className={`p-7 rounded-2xl bg-white dark:bg-slate-900 border-2 ${pillar.border} shadow-sm transition-all duration-300 cursor-default space-y-4 ${
                  hoveredPillar === i ? 'scale-105 shadow-xl' : 'scale-100'
                }`}
              >
                <div className={`w-14 h-14 rounded-2xl ${pillar.accent} flex items-center justify-center transition-transform duration-300 ${
                  hoveredPillar === i ? 'rotate-6' : ''
                }`}>
                  {pillar.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <h3 className="text-lg font-black text-slate-900 dark:text-white">
                      {pillar.title}
                    </h3>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${pillar.accent}`}>
                      {pillar.tag}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                    {pillar.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final Call to Action Card */}
      <section className="py-12 px-4 sm:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-orange-600 via-amber-600 to-orange-700 p-10 sm:p-14 text-center text-white shadow-2xl">
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute -top-16 -left-16 w-72 h-72 rounded-full bg-white/10 blur-3xl" />
              <div className="absolute -bottom-16 -right-16 w-72 h-72 rounded-full bg-white/10 blur-3xl" />
            </div>
            <div className="relative space-y-6">
              <div className="flex items-center justify-center gap-3">
                <Package className="w-10 h-10 opacity-90" />
                <ShieldCheck className="w-10 h-10 opacity-90" />
              </div>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight">
                Ready to Verify Package Compliance?
              </h2>
              <p className="text-lg sm:text-xl text-orange-100 max-w-2xl mx-auto font-medium leading-relaxed">
                Upload any pre-packaged food or consumer commodity image and receive a complete statutory compliance dossier in seconds.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 pt-3">
                <button
                  onClick={onStartInspection}
                  className="group px-8 py-4 rounded-xl bg-white text-orange-700 font-extrabold text-lg shadow-xl hover:bg-orange-50 transition-all duration-200 flex items-center gap-2 cursor-pointer hover:scale-105 active:scale-100"
                >
                  <Zap className="w-5 h-5 fill-current" />
                  <span>Start Inspection Now</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
                <button
                  onClick={onOpenLogin}
                  className="px-7 py-4 rounded-xl bg-orange-800/60 hover:bg-orange-800/80 text-white border border-white/20 font-bold text-lg transition-all duration-200 flex items-center gap-2 cursor-pointer hover:scale-105 active:scale-100"
                >
                  <Lock className="w-5 h-5 text-amber-300" />
                  <span>Officer Portal Login</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Advisory Disclaimer */}
      <div className="px-4 sm:px-8 pb-10">
        <div className="max-w-5xl mx-auto p-5 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800/80 flex items-start gap-3.5 shadow-2xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-900 dark:text-amber-200 leading-relaxed font-medium">
            <span className="font-extrabold">Statutory Advisory: </span>
            PARAKH AI operates strictly as an assistive regulatory decision-support system. Final statutory enforcement, compound notices, and seizure orders remain under the exclusive statutory authority of gazetted Legal Metrology Officers under the Legal Metrology Act, 2009.
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-10 px-4 sm:px-8 text-center space-y-4">
        <div className="flex items-center justify-center gap-2 font-bold text-slate-800 dark:text-slate-200 text-lg">
          <Scale className="w-5 h-5 text-orange-500" />
          <span>PARAKH AI &bull; Legal Metrology Digital Infrastructure Demonstrator</span>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
          Developed for the Department of Consumer Affairs, Ministry of Consumer Affairs, Food and Public Distribution, Government of India.
        </p>
        <div className="flex items-center justify-center gap-4 text-xs font-semibold text-slate-400 pt-1 flex-wrap">
          <a
            href="https://consumeraffairs.gov.in/pages/legal-metrology-act"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-500 transition-colors underline underline-offset-2"
          >
            consumeraffairs.gov.in
          </a>
          <span>&bull;</span>
          <a
            href="https://consumeraffairs.gov.in/pages/legal-metrology-act"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-500 transition-colors underline underline-offset-2"
          >
            Legal Metrology Act, 2009
          </a>
          <span>&bull;</span>
          <span className="text-slate-500">PCR 2011 Rules v2026.1</span>
        </div>
      </footer>
    </div>
  );
};
