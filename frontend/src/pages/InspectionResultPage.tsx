import React, { useEffect, useState, useRef } from 'react';
import {
  Scale,
  FileWarning,
  Download,
  Printer,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  HelpCircle,
  Copy,
  Check,
  Send,
  Shield,
  FileCheck,
  ChevronRight,
  Info,
  Layers,
  FileText,
  Code2,
  Sparkles,
  Eye,
  Sliders,
  Terminal,
  Cpu,
  X,
  ExternalLink,
  Maximize2,
  ZoomIn,
  ZoomOut,
  RefreshCw,
  Search,
  BookOpen,
  ArrowRight,
  ArrowLeft,
  ShieldAlert,
  CheckCircle
} from 'lucide-react';
import { api } from '../services/api';
import { inspectionApi } from '../api/inspection';
import { complianceApi } from '../api/compliance';
import { reportApi } from '../api/report';
import { reviewApi, ReviewRecord } from '../api/review';
import { ComplianceEvaluationResult, RuleCheckResult, CanonicalRequirementDTO } from '../types/compliance';
import { InspectorDecisionModal, InspectorDecisionType } from '../components/InspectorDecisionModal';
import { fetchJson } from '../api/client';
import { OCRResult, OCRBlock } from '../types/ocr';
import { ExtractionResponse, InspectionDebugDossier } from '../types/extraction';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ConfidenceIndicator } from '../components/ui/ConfidenceIndicator';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

interface InspectionResultPageProps {
  inspectionId: string | null;
  onBackToHistory: () => void;
  onScanNew: () => void;
  onGoBack?: () => void;
  onSelectInspection?: (id: string) => void;
}


interface StatutoryRuleDetail {
  title: string;
  citation: string;
  sourceDocument: string;
  gazetteNotice: string;
  sourceUrl: string;
  verbatimStatute: string;
  checkpoints: string[];
  enforcementPenalty: string;
}

const RULE_STATUTORY_REGISTRY: Record<string, StatutoryRuleDetail> = {
  'REQ-MRP': {
    title: 'Maximum Retail Price (MRP) & Unit Sale Price Declaration',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e) & Rule 6(11)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011 & Amendments GSR 779(E) / GSR 226(E)',
    gazetteNotice: 'G.S.R. 779(E) dated 02.11.2021 & G.S.R. 226(E) dated 28.03.2022',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'The retail sale price of the package shall clearly be declared as "Maximum Retail Price" or "MRP" inclusive of all taxes. For all pre-packaged commodities exceeding 100g or 100ml, declaration of Unit Sale Price (USP) in terms of rupees per gram, kilogram, millilitre, or litre is mandatory. Selling or offering for sale above declared physical MRP constitutes a cognizable statutory offence.',
    checkpoints: [
      'Mandatory prefix "Maximum Retail Price" or "MRP" (Rule 6(1)(e))',
      'Mandatory tax-inclusive clause: "incl. of all taxes" or "inclusive of all taxes"',
      'Mandatory Unit Sale Price (USP) declared in ₹/g, ₹/kg, ₹/ml, or ₹/L for packages > 100g or 100ml',
      'Marketplace digital listing price must never exceed the declared physical package MRP (Rule 6(10))'
    ],
    enforcementPenalty: 'Violation attracts compounding or fine up to ₹25,000 for first offence, ₹50,000 for second offence, and up to ₹1,00,000 or imprisonment up to 1 year for subsequent offences under Section 36(1) of the Legal Metrology Act, 2009.'
  },
  'REQ-NET-QTY': {
    title: 'Net Quantity in Standard Units of Mass or Measure',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(b), Rule 11, Rule 13 & Schedule II',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    gazetteNotice: 'G.S.R. 202(E) Base Notification & Schedule II Standards',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'Every package shall bear a prominent declaration of the net quantity in terms of standard unit of mass or measure. All metric units must employ official SI symbols (e.g., g, kg, ml, L, m) strictly without pluralization. Using non-standard abbreviations such as "gms", "kgs", or "mls" is strictly illegal. Minimum numeral character height on the Principal Display Panel must comply with Schedule II based on package surface area.',
    checkpoints: [
      'Strict use of standard metric symbols ("g", "kg", "ml", "L") without plural letters (Rule 11)',
      'Declared in mass (g, kg) for solid goods and volume (ml, L) for liquids (Rule 12 & 13)',
      'Numeral and letter height conforms to Schedule II Table 1 proportional to package area (Rule 7)',
      'Net weight excludes tare packaging, wrapper, and desiccant materials'
    ],
    enforcementPenalty: 'Short-weight packages or non-standard metric declarations attract penalties under Section 36(2) and Section 39 of the Legal Metrology Act, 2009.'
  },
  'REQ-MFD-PACKER': {
    title: 'Identity & Complete Postal Address of Manufacturer / Packer / Importer',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(a) & Rule 6(1)(ab)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    gazetteNotice: 'G.S.R. 202(E) dated 07.03.2011',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'The name and complete postal address of the manufacturer, or where the manufacturer is not the packer, the name and complete address of the manufacturer and packer, or in case of imported packages, the name and complete address of the importer must be declared prominently on every package.',
    checkpoints: [
      'Name of manufacturing enterprise or legal corporate entity',
      'Complete postal address including street/plot, city, state, and PIN code',
      'Clear declaration of role: "Manufactured by", "Packed by", or "Imported by"',
      'Direct traceability to registered factory or packaging premises'
    ],
    enforcementPenalty: 'Omission of manufacturer/packer identity and address is punishable under Section 36 of the Legal Metrology Act, 2009.'
  },
  'REQ-DATE': {
    title: 'Month and Year of Manufacture, Packaging or Import',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(d)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    gazetteNotice: 'G.S.R. 202(E) read with Consumer Affairs Advisory',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'The month and year in which the commodity is manufactured or pre-packed or imported shall be declared on the package. The date may be expressed in words or numerals (e.g., "05/2026", "May 2026", "05/26"). Pre-dating or post-dating packaging is strictly unlawful.',
    checkpoints: [
      'Declaration of both month and year (e.g. MM/YYYY or Month YYYY)',
      'Clear prefix: "Mfg Date", "Date of Packing", "PKD", or "Imported on"',
      'Clearly legible alongside batch identifier without obscuring print'
    ],
    enforcementPenalty: 'Misdeclaration or absence of manufacturing/packing date is an offence under Section 36 of the Legal Metrology Act, 2009.'
  },
  'REQ-CONSUMER-CARE': {
    title: 'Consumer Helpline & Grievance Redressal Cell Details',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(da)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Amendment Rules',
    gazetteNotice: 'G.S.R. 629(E) dated 23.06.2017',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'Every package shall declare the name, address, telephone number, and email address of the person or officer who may be contacted in case of consumer complaints or grievance redressal.',
    checkpoints: [
      'Dedicated consumer grievance telephone number or toll-free helpline',
      'Active customer support email address',
      'Name or designation of grievance redressal executive',
      'Complete postal address of consumer response cell'
    ],
    enforcementPenalty: 'Non-provision of statutory consumer grievance contact points is punishable under Section 36 of the Legal Metrology Act, 2009.'
  },
  'REQ-ORIGIN': {
    title: 'Country of Origin Declaration for Domestic and Imported Goods',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(g)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011 & Ministry Advisory',
    gazetteNotice: 'Advisory WM-10(5)/2020 dated 07.07.2020 & G.S.R. 629(E)',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'Every package must declare the country of origin or manufacture. In case of imported commodities, the country of origin must be declared conspicuously on the physical package and on all digital e-commerce marketplace listings.',
    checkpoints: [
      'Explicit declaration: "Country of Origin: India", "Made in India", or foreign nation',
      'Digital marketplace listing must display exact matching country of origin',
      'Declaration must not be obscured by subsequent packaging or barcodes'
    ],
    enforcementPenalty: 'Failure to declare country of origin on physical goods or e-commerce portals constitutes an offence under Rule 6(1)(g) and Section 36.'
  },
  'REQ-BATCH': {
    title: 'Batch, Lot or Code Identification Number',
    citation: 'Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(q)',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011',
    gazetteNotice: 'G.S.R. 202(E) dated 07.03.2011',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'A lot, batch, or code identification number identifying the manufacturing run or packaging run shall be declared on packages containing commodities to enable statutory inspection traceability and food safety recall.',
    checkpoints: [
      'Distinct batch/lot identifier prefixed with "Batch No.", "Lot No.", or "B.No."',
      'Clear, indelible printing that withstands normal handling and distribution',
      'Direct linkage to factory production and quality records'
    ],
    enforcementPenalty: 'Absence of batch or lot identification code impairs regulatory traceability under Rule 6(1)(q).'
  },
  'REQ-EXPIRY': {
    title: 'Best Before / Use By / Expiry Date Declaration',
    citation: 'PCR 2011 Rule 6(1)(g) read with FSSAI (Packaging & Labelling) Regulations, 2011',
    sourceDocument: 'Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI Regulations',
    gazetteNotice: 'G.S.R. 202(E) & FSSAI Packaging & Labelling Notification',
    sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
    verbatimStatute: 'Every package of food commodity must bear the "Best Before" or "Use By" date, stating the period in months or days from packaging or the specific calendar date beyond which the product must not be offered for sale or human consumption.',
    checkpoints: [
      'Declaration formatted as "Best Before [X] Months from Manufacture" or DD/MM/YYYY',
      'Specific temperature and storage conditions stated where applicable',
      'Must be legible on the principal label panel without rubbing off'
    ],
    enforcementPenalty: 'Selling expired or date-obscured food commodities is punishable under the Legal Metrology Act, 2009 and Food Safety & Standards Act, 2006.'
  },
  'REQ-FSSAI': {
    title: '14-Digit FSSAI License & Food Safety Registration',
    citation: 'Food Safety and Standards Act, 2006 & PCR 2011 Cross-Regulatory Harmonization',
    sourceDocument: 'FSSAI Food Safety and Standards (Packaging and Labelling) Regulations, 2011',
    gazetteNotice: 'FSSAI Packaging & Labelling Regulations, Section 31',
    sourceUrl: 'https://fssai.gov.in',
    verbatimStatute: 'All pre-packaged food products sold in India must display a valid 14-digit FSSAI License Number accompanied by the official FSSAI logo on the label of the pre-packaged commodity.',
    checkpoints: [
      'Valid 14-digit numeric license identifier',
      'Preceded by official FSSAI logo or "Lic. No."',
      'License must be active and registered for the manufacturer/packer premises'
    ],
    enforcementPenalty: 'Operating without or misrepresenting an FSSAI license attracts penalties under Section 63 of the Food Safety & Standards Act, 2006.'
  },
  'REQ-VEGMARK': {
    title: 'Vegetarian / Non-Vegetarian Logo Marking',
    citation: 'FSSAI Food Safety and Standards (Packaging and Labelling) Regulations, 2011 - Reg. 2.2.2',
    sourceDocument: 'FSSAI Packaging and Labelling Regulations',
    gazetteNotice: 'FSSAI Reg. 2.2.2 / Legal Metrology Cross-Verification',
    sourceUrl: 'https://fssai.gov.in',
    verbatimStatute: 'Every package of "Vegetarian" food shall bear a green colour filled circle inside a green square outline. Every package of "Non-Vegetarian" food shall bear a brown colour filled triangle inside a brown square outline on the Principal Display Panel.',
    checkpoints: [
      'Green filled circle inside a green square for vegetarian food commodities',
      'Brown filled triangle inside a brown square for non-vegetarian commodities',
      'Positioned prominently near the brand name or product title'
    ],
    enforcementPenalty: 'Absence or deceptive marking of veg/non-veg logo violates FSSAI Regulation 2.2.2 and Consumer Protection regulations.'
  },
  'REQ-INGREDIENTS': {
    title: 'Complete List of Ingredients in Descending Order of Composition',
    citation: 'FSSAI Packaging & Labelling Regulations, 2011 - Reg. 2.2.1 & PCR Rule 6',
    sourceDocument: 'FSSAI Packaging & Labelling Regulations & Legal Metrology Act',
    gazetteNotice: 'FSSAI Reg. 2.2.1 Statutory Directive',
    sourceUrl: 'https://fssai.gov.in',
    verbatimStatute: 'Except for single-ingredient commodities, a comprehensive list of ingredients shall be declared on the label in descending order of their composition by weight or volume at the time of manufacture of the food.',
    checkpoints: [
      'Ingredients listed in strictly descending order of proportion',
      'Specific names of ingredients, food additives, flavouring agents, and allergens',
      'Clear heading: "Ingredients:" or "List of Ingredients:"'
    ],
    enforcementPenalty: 'Misleading ingredient declarations constitute misbranding under Food Safety & Legal Metrology statutory provisions.'
  },
  'REQ-NUTRITION': {
    title: 'Nutritional Information Declaration per 100g / Serving',
    citation: 'FSSAI (Labelling & Display) Regulations, 2020 & Legal Metrology Harmonization',
    sourceDocument: 'FSSAI Labelling and Display Regulations, 2020',
    gazetteNotice: 'FSSAI Notification F. No. 1-94/FSSAI/SP(Labelling)/2017',
    sourceUrl: 'https://fssai.gov.in',
    verbatimStatute: 'Nutritional Information or nutritional facts per 100g or 100ml or per single consumption pack shall be declared: Energy (kcal), Protein (g), Carbohydrate (g), Total Sugars (g), Added Sugars (g), Total Fat (g), Saturated Fat (g), Trans Fat (g), and Sodium (mg).',
    checkpoints: [
      'Standard tabular panel indicating metric values per 100g/ml or per serving',
      'Mandatory reporting of energy, protein, carbohydrates, fats, sugars, and sodium',
      'Declaration of Trans Fat (g) and Saturated Fat (g) content'
    ],
    enforcementPenalty: 'Omission or false reporting of nutritional information constitutes statutory misbranding.'
  }
};

export const InspectionResultPage: React.FC<InspectionResultPageProps> = ({
  inspectionId,
  onBackToHistory,
  onScanNew,
  onGoBack,
  onSelectInspection,
}) => {
  const [inspection, setInspection] = useState<any | null>(null);
  const [compliance, setCompliance] = useState<ComplianceEvaluationResult | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [extractionResult, setExtractionResult] = useState<ExtractionResponse | null>(null);
  const [debugDossier, setDebugDossier] = useState<InspectionDebugDossier | null>(null);
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [reviewModalTarget, setReviewModalTarget] = useState<CanonicalRequirementDTO | null>(null);
  const [ruleModalTarget, setRuleModalTarget] = useState<CanonicalRequirementDTO | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Active check selection for interactive evidence grounding
  const [selectedCanonical, setSelectedCanonical] = useState<CanonicalRequirementDTO | null>(null);
  const [selectedCheck, setSelectedCheck] = useState<RuleCheckResult | null>(null);
  const [focusedOcrBlock, setFocusedOcrBlock] = useState<OCRBlock | null>(null);
  const [showAllOcrBoxes, setShowAllOcrBoxes] = useState<boolean>(false);
  const [imageZoom, setImageZoom] = useState<number>(1);

  const [copiedId, setCopiedId] = useState<boolean>(false);
  const [downloadingReport, setDownloadingReport] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);

  // Developer / Debug Dossier Modal
  const [showDevModal, setShowDevModal] = useState<boolean>(false);
  const [currentImgUrl, setCurrentImgUrl] = useState<string>('');
  const [fallbackAttempt, setFallbackAttempt] = useState<number>(0);
  const [devActiveTab, setDevActiveTab] = useState<'json' | 'perception' | 'reconciliation' | 'rules' | 'telemetry'>('json');
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  // Human Review Form State
  const [selectedDecision, setSelectedDecision] = useState<'CONFIRM_FINDING' | 'REJECT_FINDING' | 'REQUEST_MANUAL_VERIFICATION' | 'MARK_NOT_APPLICABLE'>('CONFIRM_FINDING');
  const [reviewComment, setReviewComment] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);

  // Action Modals
  const [clearModalOpen, setClearModalOpen] = useState<boolean>(false);
  const [clearComment, setClearComment] = useState<string>('All statutory declarations verified and cleared for commercial distribution.');
  const [manualReviewModalOpen, setManualReviewModalOpen] = useState<boolean>(false);
  const [manualReviewReason, setManualReviewReason] = useState<string>('Physical package verification required for ambiguous text or spatial placement.');
  const [complaintModalOpen, setComplaintModalOpen] = useState<boolean>(false);
  const [complaintProvisions, setComplaintProvisions] = useState<string>('Rule 6(1) of Legal Metrology (Packaged Commodities) Rules, 2011');
  const [complaintNotes, setComplaintNotes] = useState<string>('');
  const [submittingComplaint, setSubmittingComplaint] = useState<boolean>(false);
  const [complaintSuccessMsg, setComplaintSuccessMsg] = useState<string | null>(null);

  const imageContainerRef = useRef<HTMLDivElement>(null);

  const fetchInspectionDossier = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      setInspection(null);
      setCompliance(null);
      setOcrResult(null);
      setExtractionResult(null);
      setDebugDossier(null);
      setSelectedCheck(null);
      setSelectedCanonical(null);
      setFocusedOcrBlock(null);

      const [inspData, compData, ocrData, reviewData, extData, debugData] = await Promise.all([
        inspectionApi.getInspection(id),
        complianceApi.getCachedCompliance(id).catch(async () => {
          // If cached compliance returned 404, trigger evaluate on the fly
          return await fetchJson<ComplianceEvaluationResult>(`/inspections/${id}/evaluate`, { method: 'POST' }).catch(() => null);
        }),
        inspectionApi.getOcrResult(id).catch(() => null),
        reviewApi.getReviews(id).catch(() => []),
        inspectionApi.getExtractionResult(id).catch(() => null),
        inspectionApi.getDebugDossier(id).catch(() => null),
      ]);

      setInspection(inspData);
      setCompliance(compData);
      const initialImg = inspData?.image_url || inspData?.image?.file_url || (id ? `/uploads/${id}/original.png` : '');
      setCurrentImgUrl(api.getImageUrl(initialImg));
      setFallbackAttempt(0);
      setOcrResult(ocrData);
      setReviews(reviewData || []);
      setExtractionResult(extData);
      setDebugDossier(debugData);

      if (compData && compData.canonical_requirements && compData.canonical_requirements.length > 0) {
        // Set first non-compliant or first requirement as default selected
        const firstIssue = compData.canonical_requirements.find((r: CanonicalRequirementDTO) => r.status === 'NEEDS_REVIEW' || r.status === 'NON_COMPLIANT');
        setSelectedCanonical(firstIssue || compData.canonical_requirements[0]);
      }

      if (compData && compData.checks && compData.checks.length > 0) {
        const firstCheckIssue = compData.checks.find((c: RuleCheckResult) => c.status === 'POTENTIAL_VIOLATION' || c.status === 'MANUAL_REVIEW');
        setSelectedCheck(firstCheckIssue || compData.checks[0] || null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve inspection record');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (inspectionId) {
      fetchInspectionDossier(inspectionId);
    }
  }, [inspectionId]);

  const handleImageError = () => {
    if (!inspectionId) return;
    const candidates = [
      api.getImageUrl(`/uploads/${inspectionId}/original.png`),
      api.getImageUrl(`/uploads/${inspectionId}/original.jpg`),
      api.getImageUrl(`/uploads/${inspectionId}/processed.jpg`),
      api.getImageUrl(`/uploads/${inspectionId}/display.jpg`),
      api.getImageUrl('/uploads/sample.jpg')
    ];
    if (fallbackAttempt < candidates.length) {
      const nextCandidate = candidates[fallbackAttempt];
      setFallbackAttempt(prev => prev + 1);
      if (nextCandidate !== currentImgUrl) {
        setCurrentImgUrl(nextCandidate);
      }
    }
  };

  const copyInspectionId = () => {
    if (inspection?.inspection_id) {
      navigator.clipboard.writeText(inspection.inspection_id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  const handleDownloadReport = async () => {
    if (!inspectionId) return;
    try {
      setDownloadingReport(true);
      await reportApi.downloadReport(inspectionId);
      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to generate PDF report');
    } finally {
      setDownloadingReport(false);
    }
  };

  const getActiveBoundingBox = () => {
    // 1. Direct bounding box on canonical requirement
    if (selectedCanonical && (selectedCanonical as any).bounding_box) {
      return (selectedCanonical as any).bounding_box;
    }
    // 2. Direct bounding box on selected rule check
    if (selectedCheck?.evidence_reference?.bounding_box) {
      return selectedCheck.evidence_reference.bounding_box;
    }
    // 3. From inspection extracted declarations map or list
    if (selectedCanonical) {
      const fieldKey = selectedCanonical.field;
      const declMap = (inspection as any)?.extracted_declarations;
      if (declMap && declMap[fieldKey]?.bounding_box) {
        return declMap[fieldKey].bounding_box;
      }
      const extFields = (extractionResult as any)?.fields || (extractionResult as any);
      if (extFields && extFields[fieldKey]?.bounding_box) {
        return extFields[fieldKey].bounding_box;
      }
      if (inspection?.declarations) {
        const decl = inspection.declarations.find((d: any) => (d.field === fieldKey || d.field_name === fieldKey));
        if (decl?.bounding_box) return decl.bounding_box;
        if (decl?.bounding_box_json) {
          try {
            return typeof decl.bounding_box_json === 'string' ? JSON.parse(decl.bounding_box_json) : decl.bounding_box_json;
          } catch (e) {}
        }
      }
    }
    // 4. Focused OCR block
    if (focusedOcrBlock?.bounding_box) {
      return focusedOcrBlock.bounding_box;
    }
    // 5. High-precision token overlap against OCR blocks
    if (selectedCanonical?.extracted_value && ocrResult?.blocks) {
      const valLower = selectedCanonical.extracted_value.toLowerCase();
      const tokens = valLower.split(/[\s,:\.\-\/]+/).filter((t: string) => t.length >= 2);
      let bestBlock: any = null;
      let maxMatches = 0;
      for (const b of ocrResult.blocks) {
        if (!b.bounding_box || !b.text) continue;
        const bText = b.text.toLowerCase();
        let matches = 0;
        for (const tok of tokens) {
          if (bText.includes(tok)) matches++;
        }
        if (matches > maxMatches) {
          maxMatches = matches;
          bestBlock = b;
        }
      }
      if (bestBlock?.bounding_box) {
        return bestBlock.bounding_box;
      }
    }
    return null;
  };

  const handleViewEvidence = (req: CanonicalRequirementDTO) => {
    setSelectedCanonical(req);
    // Find matching sub-check if available
    if (compliance?.checks) {
      const match = compliance.checks.find(c => {
        if (c.field === req.field) return true;
        if (req.sub_checks) {
          return req.sub_checks.some((s: any) => typeof s === 'string' ? s === c.rule_id : s.rule_id === c.rule_id);
        }
        return false;
      });
      if (match) setSelectedCheck(match);
    }
    // Find best matching OCR block
    if (ocrResult?.blocks && req.extracted_value) {
      const valLower = req.extracted_value.toLowerCase();
      const tokens = valLower.split(/[\s,:\.\-\/]+/).filter((t: string) => t.length >= 2);
      let bestBlock: any = null;
      let maxMatches = 0;
      for (const b of ocrResult.blocks) {
        if (!b.bounding_box || !b.text) continue;
        const bText = b.text.toLowerCase();
        let matches = 0;
        for (const tok of tokens) {
          if (bText.includes(tok)) matches++;
        }
        if (matches > maxMatches) {
          maxMatches = matches;
          bestBlock = b;
        }
      }
      if (bestBlock) setFocusedOcrBlock(bestBlock);
    }
    // Smooth scroll to image viewer container
    if (imageContainerRef.current) {
      imageContainerRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  const handleClearInspectionAction = async () => {
    if (!inspectionId) return;
    try {
      const record = await reviewApi.submitReview(inspectionId, {
        decision: 'CONFIRM_FINDING',
        comment: clearComment || 'All statutory declarations verified and cleared for commercial distribution.',
        reviewer: 'INS-DL-4029'
      });
      setReviews((prev) => [record, ...prev]);
      setReviewSuccessMsg('Inspection officially CLEARED and recorded in database.');
      setClearModalOpen(false);
      setTimeout(() => setReviewSuccessMsg(null), 5000);
      fetchInspectionDossier(inspectionId);
    } catch (err: any) {
      alert(err.message || 'Failed to clear inspection');
    }
  };

  const handleNeedsReviewAction = async () => {
    if (!inspectionId || !manualReviewReason.trim()) return;
    try {
      const record = await reviewApi.submitReview(inspectionId, {
        decision: 'REQUEST_MANUAL_VERIFICATION',
        comment: manualReviewReason,
        reviewer: 'INS-DL-4029'
      });
      setReviews((prev) => [record, ...prev]);
      setReviewSuccessMsg('Inspection marked for manual verification queue.');
      setManualReviewModalOpen(false);
      setTimeout(() => setReviewSuccessMsg(null), 5000);
      fetchInspectionDossier(inspectionId);
    } catch (err: any) {
      alert(err.message || 'Failed to update review status');
    }
  };

  const handleSubmitComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspectionId) return;
    try {
      setSubmittingComplaint(true);
      const pName = inspection?.product?.name || inspection?.product?.product_name || 'Packaged Commodity';
      const mfgName = inspection?.product?.manufacturer || null;
      const cat = inspection?.product?.category || 'packaged_commodity';
      const violations = compliance?.violations || [];

      const res = await fetchJson<any>('/complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inspection_id: inspectionId,
          product_name: pName,
          manufacturer_name: mfgName,
          commodity_category: cat,
          statutory_provisions: complaintProvisions,
          violations: violations,
          enforcement_notes: complaintNotes,
          inspector_name: 'inspector.demo'
        })
      });

      setComplaintModalOpen(false);
      setComplaintSuccessMsg("Official Complaint " + (res.complaint_id || "") + " successfully registered in Enforcement Queue.");
      setTimeout(() => setComplaintSuccessMsg(null), 6000);
      fetchInspectionDossier(inspectionId);
    } catch (err: any) {
      alert(err.message || 'Failed to submit complaint');
    } finally {
      setSubmittingComplaint(false);
    }
  };

  const handleConfirmReview = async (decision: any, reason: string, remarks?: string) => {
    if (!inspectionId || !reviewModalTarget) return;
    const res = await fetchJson<any>(`/inspections/${inspectionId}/review-check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        canonical_id: reviewModalTarget.canonical_id,
        decision,
        reason,
        remarks,
        reviewer: "INS-DL-4029"
      })
    });
    if (res && res.compliance) {
      setCompliance(res.compliance);
    }
  };

  const formatAdvisorySentences = (text: string) => {
    if (!text) return [];
    return text.split(';').map(s => s.trim()).filter(s => s.length > 0);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] space-y-4">
        <div className="w-10 h-10 border-3 border-blue-900 border-t-transparent dark:border-blue-400 rounded-full animate-spin"></div>
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">Loading Legal Metrology Inspection Dossier...</p>
        <p className="text-xs text-slate-400 font-mono">Running deterministic rule engine screening...</p>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="p-8 max-w-2xl mx-auto space-y-4">
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 flex items-start gap-3">
          <AlertOctagon className="w-5 h-5 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
          <div className="space-y-1">
            <h3 className="font-bold text-sm">Unable to Load Inspection</h3>
            <p className="text-xs">{error || 'Inspection record not found.'}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={onBackToHistory} className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-xs font-semibold rounded-lg transition cursor-pointer">
            Return to Stacks
          </button>
          <button onClick={onScanNew} className="px-4 py-2 bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold rounded-lg transition cursor-pointer">
            Scan New Product
          </button>
        </div>
      </div>
    );
  }

  const overallStatus = compliance?.overall_status || inspection?.overall_status || 'NEEDS_REVIEW';
  const screeningScore = compliance?.screening_priority_score ?? inspection?.screening_priority_score ?? 0;
  const canonicalReqs = compliance?.canonical_requirements || [];
  const violationsCount = compliance?.confirmed_violations_count ?? compliance?.violations?.length ?? 0;
  const reviewCount = compliance?.items_needing_review_count ?? canonicalReqs.filter(r => r.status === 'NEEDS_REVIEW').length ?? 0;
  const passedCount = canonicalReqs.filter(r => r.status === 'COMPLIANT').length;
  const coveragePercent = compliance?.evidence_coverage_percent ?? (canonicalReqs.length > 0 ? Math.round((passedCount / canonicalReqs.length) * 100) : 100);

  const imgWidth = ocrResult?.image_width || inspection?.image?.width || 1000;
  const imgHeight = ocrResult?.image_height || inspection?.image?.height || 1000;
  const rawImg = inspection?.image_url || inspection?.image?.file_url || (inspectionId ? `/uploads/${inspectionId}/original.png` : '');
  const imageUrl = currentImgUrl || (rawImg ? api.getImageUrl(rawImg) : '');

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Context Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="space-y-2">
          {onGoBack && (
            <button
              onClick={onGoBack}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-all cursor-pointer shadow-xs group"
              title="Go back to previous step without refreshing"
            >
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform text-slate-500" />
              <span>Back to Previous Step</span>
            </button>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span>Inspections</span>
            <ChevronRight className="w-3 h-3" />
            <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{inspection.inspection_id}</span>
            <button
              onClick={copyInspectionId}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition cursor-pointer text-slate-400 hover:text-slate-600"
              title="Copy Inspection ID"
            >
              {copiedId ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-slate-100">
              Inspection Result
            </h1>
            <span className="text-xs text-slate-500 font-mono">
              Asset: <span className="text-slate-700 dark:text-slate-300 font-semibold">{inspection.filename || 'package_label.png'}</span>
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 font-mono">
              Rule Catalog: <span className="text-blue-900 dark:text-blue-400 font-bold">{compliance?.rule_version || '2026.1'}</span>
            </span>
          </div>
        </div>

        {/* Quick Test Scenario Chips & Top Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">


          <button
            onClick={() => setShowDevModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold transition cursor-pointer"
            title="Open Developer & Audit Dossier"
          >
            <Code2 className="w-3.5 h-3.5 text-blue-900 dark:text-blue-400" />
            <span>Developer View</span>
          </button>

          <button
            onClick={handleDownloadReport}
            disabled={downloadingReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloadSuccess ? 'Downloaded!' : downloadingReport ? 'Generating...' : 'Download PDF'}</span>
          </button>

          <button
            onClick={() => window.print()}
            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition cursor-pointer hidden sm:block"
            title="Print Inspection"
          >
            <Printer className="w-4 h-4" />
          </button>

          <button
            onClick={onScanNew}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Scan Another</span>
          </button>
        </div>
      </div>

      {/* Top Assessment Banner */}
      <div className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs transition-all ${
        overallStatus === 'COMPLIANT'
          ? 'bg-emerald-50/90 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800 text-emerald-950 dark:text-emerald-200'
          : overallStatus === 'NON_COMPLIANT' || overallStatus === 'POTENTIAL_VIOLATION'
          ? 'bg-rose-50/90 dark:bg-rose-950/30 border-rose-300 dark:border-rose-800 text-rose-950 dark:text-rose-200'
          : 'bg-amber-50/90 dark:bg-amber-950/30 border-amber-300 dark:border-amber-800 text-amber-950 dark:text-amber-200'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
            overallStatus === 'COMPLIANT'
              ? 'bg-emerald-600 text-white shadow-emerald-200 shadow-sm'
              : overallStatus === 'NON_COMPLIANT' || overallStatus === 'POTENTIAL_VIOLATION'
              ? 'bg-rose-600 text-white shadow-rose-200 shadow-sm'
              : 'bg-amber-500 text-white shadow-amber-200 shadow-sm'
          }`}>
            {overallStatus === 'COMPLIANT' ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : overallStatus === 'NON_COMPLIANT' || overallStatus === 'POTENTIAL_VIOLATION' ? (
              <AlertOctagon className="w-5 h-5" />
            ) : (
              <AlertTriangle className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-black tracking-tight uppercase">
                {overallStatus === 'COMPLIANT'
                  ? '✓ COMPLIANT'
                  : overallStatus === 'NON_COMPLIANT' || overallStatus === 'POTENTIAL_VIOLATION'
                  ? '✕ CONFIRMED VIOLATION'
                  : '⚠ NEEDS REVIEW'}
              </span>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-white/70 dark:bg-slate-900/70 border border-current">
                {overallStatus === 'COMPLIANT' ? 'Passed All Checks' : overallStatus === 'NON_COMPLIANT' ? 'Statutory Defect' : 'Perception Triage'}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              {overallStatus === 'COMPLIANT'
                ? 'All mandatory Legal Metrology packaging declarations verified and conform to statutory standards.'
                : overallStatus === 'NON_COMPLIANT' || overallStatus === 'POTENTIAL_VIOLATION'
                ? 'Statutory non-compliances detected on principal display panel. Action required under Legal Metrology Rules.'
                : 'Perception uncertainty or low confidence detected. Mandatory declarations require manual inspector verification before enforcement.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 pl-4 md:border-l border-slate-200/80 dark:border-slate-800 shrink-0">
          <div className="text-right">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
              Internal Screening Priority
            </span>
            <span className="text-lg font-black font-mono text-slate-900 dark:text-slate-100">
              {screeningScore} <span className="text-xs text-slate-400 font-normal">/ 100</span>
            </span>
            <span className="text-[9px] text-slate-400 block leading-tight">Advisory triage score</span>
          </div>
        </div>
      </div>

      {/* 4-Metric Counters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Confirmed Violations</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-black font-mono ${violationsCount > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-700 dark:text-slate-300'}`}>
              {violationsCount}
            </span>
            <span className="text-[11px] text-slate-400">Statutory defects</span>
          </div>
        </Card>

        <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Items Needing Review</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-black font-mono ${reviewCount > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-700 dark:text-slate-300'}`}>
              {reviewCount}
            </span>
            <span className="text-[11px] text-slate-400">Inspector queue</span>
          </div>
        </Card>

        <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Passed Requirements</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">
              {passedCount}
            </span>
            <span className="text-[11px] text-slate-400">of {canonicalReqs.length} canonical</span>
          </div>
        </Card>

        <Card className="p-3 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Evidence Coverage</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-black font-mono text-blue-900 dark:text-blue-400">
              {coveragePercent}%
            </span>
            <span className="text-[11px] text-slate-400">Mandatory labels</span>
          </div>
        </Card>
      </div>

      {/* Main Balanced 2-Column Workstation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Visual Grounding & Inspector Review Workstation (lg:col-span-5) */}
        <div className="lg:col-span-5 lg:sticky lg:top-16 space-y-4 max-h-[calc(100vh-5rem)] overflow-y-auto pr-1">
          {/* Package Evidence Viewer */}
          <div ref={imageContainerRef}>
          <Card className="overflow-hidden border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <div className="p-3 bg-slate-50 dark:bg-slate-900/70 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-blue-900 dark:text-blue-400" />
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Package Evidence Viewer</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 text-[11px] text-slate-600 dark:text-slate-400 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={showAllOcrBoxes}
                    onChange={(e) => setShowAllOcrBoxes(e.target.checked)}
                    className="rounded text-blue-900 focus:ring-blue-900 w-3.5 h-3.5 cursor-pointer"
                  />
                  <span>OCR Blocks ({ocrResult?.total_blocks || ocrResult?.blocks?.length || 0})</span>
                </label>
              </div>
            </div>

            {/* Interactive Image Canvas */}
            <div className="relative bg-slate-950 flex items-center justify-center min-h-[380px] p-2 overflow-hidden select-none">
              {imageUrl ? (
                <div className="relative inline-block max-w-full">
                  <img
                    src={imageUrl}
                    alt="Inspection target"
                    onError={handleImageError}
                    className="max-h-[460px] w-auto object-contain rounded shadow-md block transition-transform duration-200"
                    style={{ transform: `scale(${imageZoom})` }}
                  />

                  {/* SVG Overlay for High-Precision Bounding Boxes */}
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 ${imgWidth} ${imgHeight}`}
                    preserveAspectRatio="none"
                  >
                    {/* All OCR Blocks if toggled */}
                    {showAllOcrBoxes && ocrResult?.blocks?.map((b: OCRBlock, bIdx: number) => {
                      if (!b.bounding_box) return null;
                      const isFocused = focusedOcrBlock && focusedOcrBlock.text === b.text;
                      return (
                        <rect
                          key={`ocr_box_${bIdx}`}
                          x={b.bounding_box.x}
                          y={b.bounding_box.y}
                          width={b.bounding_box.width}
                          height={b.bounding_box.height}
                          fill={isFocused ? "rgba(59, 130, 246, 0.3)" : "rgba(255, 255, 255, 0.05)"}
                          stroke={isFocused ? "#3B82F6" : "rgba(148, 163, 184, 0.4)"}
                          strokeWidth={isFocused ? "3" : "1"}
                          strokeDasharray={isFocused ? "none" : "2,2"}
                        />
                      );
                    })}

                    {/* Spotlight Active Finding Bounding Box */}
                    {(() => {
                      const activeBox = getActiveBoundingBox();
                      if (!activeBox) return null;
                      return (
                        <g className="animate-pulse">
                          <rect
                            x={activeBox.x}
                            y={activeBox.y}
                            width={activeBox.width}
                            height={activeBox.height}
                            fill={
                              selectedCanonical?.status === 'COMPLIANT'
                                ? "rgba(16, 185, 129, 0.25)"
                                : selectedCanonical?.status === 'NON_COMPLIANT'
                                ? "rgba(244, 63, 94, 0.3)"
                                : "rgba(245, 158, 11, 0.3)"
                            }
                            stroke={
                              selectedCanonical?.status === 'COMPLIANT'
                                ? "#10B981"
                                : selectedCanonical?.status === 'NON_COMPLIANT'
                                ? "#F43F5E"
                                : "#F59E0B"
                            }
                            strokeWidth="4"
                            rx="4"
                          />
                        </g>
                      );
                    })()}
                  </svg>
                </div>
              ) : (
                <div className="text-slate-500 text-xs">No image available</div>
              )}
            </div>

            <div className="p-2.5 bg-slate-50 dark:bg-slate-900/60 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
              <span>Click any declaration on the right to spotlight grounded evidence.</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setImageZoom(prev => Math.max(0.8, prev - 0.2))}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="font-mono text-[10px]">{Math.round(imageZoom * 100)}%</span>
                <button
                  onClick={() => setImageZoom(prev => Math.min(2.0, prev + 0.2))}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </Card>
          </div>

          {/* Evidence Grounding Detail Panel */}
          {selectedCanonical && (
            <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Grounding Panel</span>
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100">{selectedCanonical.title}</span>
                </div>
                <StatusBadge status={selectedCanonical.status as any} />
              </div>

              <div className="space-y-2">
                <div>
                  <span className="text-[10px] font-semibold text-slate-500 uppercase block">Declared Package Value</span>
                  <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                    {selectedCanonical.extracted_value || 'Null / Not Detected on Scanned Panel'}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                    <span className="text-[10px] text-slate-400 block uppercase font-semibold">Perception Source</span>
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Tesseract + Qwen Vision</span>
                  </div>
                  <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                    <span className="text-[10px] text-slate-400 block uppercase font-semibold">Confidence Level</span>
                    <ConfidenceIndicator confidence={selectedCanonical.confidence || 0.95} />
                  </div>
                </div>

                {(() => {
                  const bBox = getActiveBoundingBox();
                  if (!bBox) return null;
                  return (
                    <div className="p-2 rounded bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-[11px] font-mono text-slate-600 dark:text-slate-400">
                      <span className="text-[10px] text-slate-400 block uppercase font-semibold font-sans">Bounding Box Coordinates</span>
                      x: {bBox.x}, y: {bBox.y}, w: {bBox.width}, h: {bBox.height}
                    </div>
                  );
                })()}
              </div>
            </Card>
          )}

          {/* Official Inspector Review & Determination Dock */}
          <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-900 dark:text-blue-400" />
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100">Inspector Determination Dock</span>
              </div>
              <Badge variant="neutral" className="text-[10px]">Statutory Authority</Badge>
            </div>

            {reviewSuccessMsg && (
              <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{reviewSuccessMsg}</span>
              </div>
            )}

            {complaintSuccessMsg && (
              <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs font-semibold flex items-center gap-2">
                <FileWarning className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{complaintSuccessMsg}</span>
              </div>
            )}

            <div className="space-y-3">
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Record official enforcement action under the Legal Metrology (Packaged Commodities) Rules, 2011.
              </p>

              {/* Action Buttons Triage Stack */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  onClick={() => setClearModalOpen(true)}
                  className="py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
                >
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>Move to Cleared</span>
                </button>

                <button
                  onClick={() => setComplaintModalOpen(true)}
                  className="py-2 px-3 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold transition cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
                >
                  <FileWarning className="w-3.5 h-3.5" />
                  <span>Create Complaint</span>
                </button>

                <button
                  onClick={() => setManualReviewModalOpen(true)}
                  className="py-2 px-3 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold transition cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Review Queue</span>
                </button>
              </div>

              {/* Recorded Reviews History */}
              {reviews.length > 0 && (
                <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Audit Log</span>
                  {reviews.map((r, rIdx) => (
                    <div key={`rev_${rIdx}`} className="p-2 rounded bg-slate-50 dark:bg-slate-800 text-[11px] space-y-0.5">
                      <div className="flex items-center justify-between text-slate-700 dark:text-slate-300 font-semibold">
                        <span>{r.reviewer || 'INS-DL-4029'}</span>
                        <span className="text-[10px] text-slate-400">{r.decision}</span>
                      </div>
                      <p className="text-slate-500 dark:text-slate-400">{r.comment}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: Canonical Statutory Requirements (lg:col-span-7) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-blue-900 dark:text-blue-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Mandatory Statutory Declarations
              </h2>
            </div>
            <span className="text-xs text-slate-500 font-mono">
              {passedCount} / {canonicalReqs.length} Passed
            </span>
          </div>

          {/* 7 Canonical Requirement Cards */}
          <div className="space-y-3">
            {canonicalReqs.map((req: CanonicalRequirementDTO) => {
              const isSelected = selectedCanonical?.canonical_id === req.canonical_id;
              const hasReviewNotes = req.status === 'NEEDS_REVIEW' || req.status === 'NON_COMPLIANT';
              const advisorySentences = formatAdvisorySentences(req.overall_reason || '');

              return (
                <Card
                  key={req.canonical_id}
                  className={`p-4 transition-all duration-200 ${
                    isSelected
                      ? 'ring-2 ring-blue-900 dark:ring-blue-400 shadow-md bg-white dark:bg-slate-900'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                          {req.title}
                        </span>
                        <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {req.canonical_id}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500 font-medium block">
                        {req.statutory_rule || 'Legal Metrology (Packaged Commodities) Rules, 2011'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <StatusBadge status={req.status as any} />
                      <button
                        onClick={() => setRuleModalTarget(req)}
                        className="px-2.5 py-1 rounded-md text-[11px] font-semibold border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition cursor-pointer"
                        title="View Full Statutory Rule"
                      >
                        View Rule
                      </button>
                      <button
                        onClick={() => setReviewModalTarget(req)}
                        className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 text-blue-900 dark:text-blue-300 transition cursor-pointer border border-blue-200 dark:border-blue-900"
                        title="Record Inspector Decision"
                      >
                        Inspector Decision
                      </button>
                    </div>
                  </div>

                  {/* Formatted Advisory / Review Notice Box if Issue Exists */}
                  {hasReviewNotes && advisorySentences.length > 0 && (
                    <div className="my-3 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 border-2 border-amber-300 dark:border-amber-700/80 shadow-xs">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-900 dark:text-amber-200 mb-2">
                        <div className="w-5 h-5 rounded-full bg-amber-200 dark:bg-amber-900/80 flex items-center justify-center shrink-0">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-800 dark:text-amber-300" />
                        </div>
                        <span>Statutory Inspector Advisory Notice</span>
                      </div>
                      <div className="space-y-2 pl-1">
                        {advisorySentences.map((sentence, sIdx) => {
                          const cleanSentence = sentence.replace(/^Manual inspector review required:\s*/i, '').trim();
                          return (
                            <div key={`adv_${sIdx}`} className="flex items-start gap-2.5 text-xs text-amber-950 dark:text-amber-100 font-medium leading-relaxed bg-amber-100/70 dark:bg-amber-900/40 p-2.5 rounded-lg border border-amber-200 dark:border-amber-800/70">
                              <span className="w-2 h-2 rounded-full bg-amber-600 dark:bg-amber-400 mt-1 shrink-0" />
                              <span className="flex-1">{cleanSentence}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Declared Value Pill */}
                  <div className="mt-3 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase block">Declared Package Value</span>
                      <span className="font-mono text-xs font-black text-slate-900 dark:text-slate-100">
                        {req.extracted_value ? (
                          <span>{req.extracted_value}</span>
                        ) : (
                          <span className="text-amber-700 dark:text-amber-400 font-sans font-semibold text-[11px] flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 animate-pulse"></span>
                            Not Detected on Scanned Panel &bull; Physical Verification Required
                          </span>
                        )}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {req.extracted_value ? (
                        <ConfidenceIndicator confidence={req.confidence ?? 0.85} />
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono">
                          0% / Unverified
                        </span>
                      )}
                      <button
                        onClick={() => handleViewEvidence(req)}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-blue-900 dark:text-blue-400 text-xs font-bold transition cursor-pointer shadow-2xs"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Evidence</span>
                      </button>
                    </div>
                  </div>

                  {/* Sub-checks pill list */}
                  {req.sub_checks && req.sub_checks.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
                      <span className="text-[10px] font-semibold text-slate-400 uppercase mr-1">Evaluated Sub-rules:</span>
                      {req.sub_checks.map((sub: any, idx: number) => {
                        const rId = typeof sub === "string" ? sub : sub?.rule_id || ("rule_" + idx);
                        const isChkCompliant = typeof sub === "object" && sub?.status ? sub.status === "COMPLIANT" : compliance?.checks?.find(c => c.rule_id === rId)?.status === "COMPLIANT";
                        return (
                          <span
                            key={rId}
                            className={"px-1.5 py-0.5 rounded text-[10px] font-mono font-medium border " + (
                              isChkCompliant
                                ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                                : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800"
                            )}
                          >
                            {rId}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      </div>

      {/* Non-Governmental Prototype Advisory */}
      <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 text-xs flex items-start gap-2.5">
        <Info className="w-4 h-4 text-blue-900 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold text-slate-700 dark:text-slate-300">Non-Governmental Prototype Advisory:</span>
          <p className="leading-snug">
            PARAKH AI is an independent automated decision-support system designed to screen packaging declarations under the Legal Metrology (Packaged Commodities) Rules, 2011. This analysis provides algorithmic triage and does not replace official government statutory certification or physical laboratory metrological verification.
          </p>
        </div>
      </div>

      {/* Developer View Modal */}
      {showDevModal && (
        <div onClick={(e) => { if (e.target === e.currentTarget) setShowDevModal(false); }} className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/80">
              <div className="flex items-center gap-2">
                <Code2 className="w-5 h-5 text-blue-900 dark:text-blue-400" />
                <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">Developer & Pipeline Audit Dossier</h3>
              </div>
              <button
                onClick={() => setShowDevModal(false)}
                className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-600 transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Tabs */}
            <div className="flex items-center gap-2 px-4 border-b border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/60 text-xs font-semibold overflow-x-auto">
              <button
                onClick={() => setDevActiveTab('json')}
                className={`py-2.5 px-3 border-b-2 transition cursor-pointer ${
                  devActiveTab === 'json'
                    ? 'border-blue-900 dark:border-blue-400 text-blue-900 dark:text-blue-400 font-bold'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Raw JSON Payload
              </button>
              <button
                onClick={() => setDevActiveTab('perception')}
                className={`py-2.5 px-3 border-b-2 transition cursor-pointer ${
                  devActiveTab === 'perception'
                    ? 'border-blue-900 dark:border-blue-400 text-blue-900 dark:text-blue-400 font-bold'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Perception Engine
              </button>
              <button
                onClick={() => setDevActiveTab('reconciliation')}
                className={`py-2.5 px-3 border-b-2 transition cursor-pointer ${
                  devActiveTab === 'reconciliation'
                    ? 'border-blue-900 dark:border-blue-400 text-blue-900 dark:text-blue-400 font-bold'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Reconciliation Trace
              </button>
              <button
                onClick={() => setDevActiveTab('rules')}
                className={`py-2.5 px-3 border-b-2 transition cursor-pointer ${
                  devActiveTab === 'rules'
                    ? 'border-blue-900 dark:border-blue-400 text-blue-900 dark:text-blue-400 font-bold'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Rule Engine Trace
              </button>
              <button
                onClick={() => setDevActiveTab('telemetry')}
                className={`py-2.5 px-3 border-b-2 transition cursor-pointer ${
                  devActiveTab === 'telemetry'
                    ? 'border-blue-900 dark:border-blue-400 text-blue-900 dark:text-blue-400 font-bold'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                API Telemetry
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-4">
              {devActiveTab === 'json' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase">Complete Inspection JSON</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify({ inspection, compliance, ocrResult, extractionResult }, null, 2));
                        setCopiedJson(true);
                        setTimeout(() => setCopiedJson(false), 2000);
                      }}
                      className="px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition cursor-pointer"
                    >
                      {copiedJson ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedJson ? 'Copied!' : 'Copy JSON'}</span>
                    </button>
                  </div>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-400 text-xs font-mono overflow-x-auto max-h-[400px]">
                    {JSON.stringify({ inspection, compliance, ocrResult, extractionResult }, null, 2)}
                  </pre>
                </div>
              )}

              {devActiveTab === 'perception' && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">OCR Token Blocks ({ocrResult?.total_blocks || 0})</h4>
                  <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-x-auto max-h-[350px]">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 sticky top-0">
                        <tr>
                          <th className="p-2 border-b">Token / Text</th>
                          <th className="p-2 border-b">Confidence</th>
                          <th className="p-2 border-b">Box (x, y, w, h)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                        {ocrResult?.blocks?.map((b, i) => (
                          <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                            <td className="p-2 font-bold">{b.text}</td>
                            <td className="p-2">{Math.round((b.confidence || 0) * 100)}%</td>
                            <td className="p-2 text-slate-400">
                              {b.bounding_box ? `${b.bounding_box.x}, ${b.bounding_box.y}, ${b.bounding_box.width}, ${b.bounding_box.height}` : 'null'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {devActiveTab === 'reconciliation' && (
                <div className="space-y-3 text-xs">
                  <h4 className="font-bold text-slate-700 dark:text-slate-300 uppercase">Perception Conflict Reconciliation (Cases A-E)</h4>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">Conflict Architecture Rules:</p>
                    <ul className="list-disc pl-4 space-y-1 text-slate-600 dark:text-slate-400">
                      <li><strong>Case A (Corroboration):</strong> Tesseract OCR + Vision agree $\rightarrow$ high-confidence extraction.</li>
                      <li><strong>Case B (Single Clear Match):</strong> One source captures valid statutory declaration $\rightarrow$ accepted.</li>
                      <li><strong>Case C (Disagreement):</strong> Sources disagree on numeric price/quantity $\rightarrow$ flags NEEDS REVIEW (never false violation).</li>
                      <li><strong>Case D (Omission):</strong> Declaration not visible on scanned panel $\rightarrow$ flags NEEDS REVIEW.</li>
                    </ul>
                  </div>
                </div>
              )}

              {devActiveTab === 'rules' && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase">Evaluated Rules Ledger ({compliance?.checks?.length || 0})</h4>
                  <div className="space-y-2 max-h-[350px] overflow-y-auto">
                    {compliance?.checks?.map((chk) => (
                      <div key={chk.rule_id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-center justify-between text-xs">
                        <div className="space-y-0.5">
                          <span className="font-bold text-slate-900 dark:text-slate-100">{chk.rule_id}</span>
                          <p className="text-[11px] text-slate-500">{chk.requirement}</p>
                          <p className="text-[10px] text-slate-400 font-mono">{chk.reason}</p>
                        </div>
                        <StatusBadge status={chk.status as any} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {devActiveTab === 'telemetry' && (
                <div className="space-y-3 text-xs">
                  <h4 className="font-bold text-slate-700 dark:text-slate-300 uppercase">System Endpoints & Latencies</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                      <span className="text-slate-400 block font-semibold">OCR Latency</span>
                      <span className="text-sm font-black text-slate-900 dark:text-slate-100">{ocrResult?.processing_time_ms ? `${ocrResult.processing_time_ms} ms` : 'Cached'}</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                      <span className="text-slate-400 block font-semibold">Deterministic Rule Screening</span>
                      <span className="text-sm font-black text-slate-900 dark:text-slate-100">&lt; 15 ms</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 flex justify-end">
              <button
                onClick={() => setShowDevModal(false)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-950 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-lg transition cursor-pointer"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Details Modal with Official Government Source Integration */}
      {ruleModalTarget && (() => {
        const ruleDetail = RULE_STATUTORY_REGISTRY[ruleModalTarget.canonical_id] || {
          title: ruleModalTarget.title,
          citation: ruleModalTarget.statutory_rule || 'Legal Metrology (Packaged Commodities) Rules, 2011',
          sourceDocument: 'Ministry of Consumer Affairs, Food & Public Distribution',
          gazetteNotice: 'Gazette of India Extraordinary / Official Notification',
          sourceUrl: 'https://consumeraffairs.gov.in/pages/legal-metrology-act',
          verbatimStatute: 'Under the Legal Metrology (Packaged Commodities) Rules, 2011, every package must bear a clear, legible, and prominent statutory declaration satisfying prescribed requirements.',
          checkpoints: ['Statutory declaration must be clearly visible on the Principal Display Panel'],
          enforcementPenalty: 'Violation attracts compounding or fine under Section 36 of the Legal Metrology Act, 2009.'
        };

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                  <div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                      Official Statutory Rule Dossier
                    </h3>
                    <span className="text-[11px] font-mono text-slate-400">
                      Department of Consumer Affairs &bull; Gazette Codification
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setRuleModalTarget(null)}
                  className="p-1 rounded text-slate-400 hover:text-slate-600 transition cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 text-xs">
                {/* Title & Citation */}
                <div className="p-3.5 bg-orange-50/70 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-900/60 rounded-xl space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-orange-200 dark:bg-orange-900 text-orange-900 dark:text-orange-200">
                      {ruleModalTarget.canonical_id}
                    </span>
                    <span className="font-bold text-xs text-orange-900 dark:text-orange-200">
                      {ruleDetail.citation}
                    </span>
                  </div>
                  <h4 className="font-black text-sm text-slate-900 dark:text-slate-100 pt-0.5">
                    {ruleDetail.title}
                  </h4>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                    Gazette Reference: {ruleDetail.gazetteNotice}
                  </p>
                </div>

                {/* Verbatim Statutory Requirement */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Verbatim Statutory Requirement
                  </span>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
                    <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-normal text-xs">
                      {ruleDetail.verbatimStatute}
                    </p>
                  </div>
                </div>

                {/* Mandatory Checkpoints */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Statutory Verification Checkpoints
                  </span>
                  <div className="space-y-1">
                    {ruleDetail.checkpoints.map((cp, cIdx) => (
                      <div key={cIdx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                        <Check className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                        <span>{cp}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Statutory Penalty */}
                <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 space-y-1">
                  <span className="text-[10px] font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider block">
                    Statutory Enforcement &amp; Penalties
                  </span>
                  <p className="text-amber-900 dark:text-amber-200 text-xs leading-relaxed">
                    {ruleDetail.enforcementPenalty}
                  </p>
                </div>

                {/* Official Source Link Button */}
                <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <a
                    href={ruleDetail.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-300 text-xs font-bold hover:bg-blue-100 transition cursor-pointer shadow-2xs group"
                  >
                    <span>View Gazette Rule on consumeraffairs.gov.in</span>
                    <ExternalLink className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </a>
                  <button
                    onClick={() => setRuleModalTarget(null)}
                    className="px-4 py-2 bg-slate-900 dark:bg-slate-700 text-white text-xs font-bold rounded-lg hover:bg-slate-800 transition cursor-pointer"
                  >
                    Close Rule Viewer
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Action Dialogs */}
      {clearModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">Move to Cleared Stack</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Confirm that this package satisfies all statutory declarations and is cleared for distribution.
            </p>
            <textarea
              value={clearComment}
              onChange={(e) => setClearComment(e.target.value)}
              className="w-full p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
              rows={3}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setClearModalOpen(false)} className="px-3 py-1.5 rounded-lg border text-xs font-semibold">Cancel</button>
              <button onClick={handleClearInspectionAction} className="px-4 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold">Confirm Cleared</button>
            </div>
          </div>
        </div>
      )}

      {complaintModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">Register Official Complaint</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Create an official enforcement complaint record against the manufacturer.
            </p>
            <textarea
              value={complaintNotes}
              onChange={(e) => setComplaintNotes(e.target.value)}
              placeholder="Enforcement notes and inspection observations..."
              className="w-full p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
              rows={3}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setComplaintModalOpen(false)} className="px-3 py-1.5 rounded-lg border text-xs font-semibold">Cancel</button>
              <button onClick={handleSubmitComplaint} disabled={submittingComplaint} className="px-4 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold">Register Complaint</button>
            </div>
          </div>
        </div>
      )}

      {manualReviewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">Send to Review Queue</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Flag this package for manual physical inspection by an authorized officer.
            </p>
            <textarea
              value={manualReviewReason}
              onChange={(e) => setManualReviewReason(e.target.value)}
              className="w-full p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs"
              rows={3}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setManualReviewModalOpen(false)} className="px-3 py-1.5 rounded-lg border text-xs font-semibold">Cancel</button>
              <button onClick={handleNeedsReviewAction} className="px-4 py-1.5 rounded-lg bg-amber-600 text-white text-xs font-semibold">Submit Review Request</button>
            </div>
          </div>
        </div>
      )}

      {/* Inspector Decision Modal for Individual Checks */}
      {reviewModalTarget && (
        <InspectorDecisionModal
          isOpen={!!reviewModalTarget}
          onClose={() => setReviewModalTarget(null)}
          onConfirm={(decision, reason, remarks) => handleConfirmReview(decision, reason, remarks)}
          canonicalTitle={reviewModalTarget.title}
          statutoryRule={reviewModalTarget.statutory_rule || 'Rule 6, LMR 2011'}
          currentStatus={reviewModalTarget.status}
          detectedValue={reviewModalTarget.extracted_value}
        />
      )}
    </div>
  );
};
