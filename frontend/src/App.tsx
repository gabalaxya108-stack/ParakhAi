import React, { useState, useEffect } from "react";
import {
  Scale,
  LayoutDashboard,
  UploadCloud,
  FileCheck2,
  History,
  Building2,
  BookOpen,
  Layers,
  ShieldCheck,
  Search,
  User,
  Info,
  Menu,
  X,
  ChevronRight,
  Shield,
  Settings,
  Package,
  BarChart3,
  Database,
  FileText,
  Sun,
  Moon,
  FileWarning,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import { HealthStatusBadge } from "./components/HealthStatusBadge";
import { DashboardPage } from "./pages/DashboardPage";
import { ScanProductPage } from "./pages/ScanProductPage";
import { BatchInspectionPage } from "./pages/BatchInspectionPage";
import { InspectionResultPage } from "./pages/InspectionResultPage";
import { InspectionHistoryPage } from "./pages/InspectionHistoryPage";
import { ManufacturerAnalyticsPage } from "./pages/ManufacturerAnalyticsPage";
import { RuleCatalogPage } from "./pages/RuleCatalogPage";
import { AdminPortalPage } from "./pages/AdminPortalPage";
import { RegulatoryDataPage } from "./pages/RegulatoryDataPage";
import { RegulatorySourcesPage } from "./pages/RegulatorySourcesPage";
import { LandingPage } from "./pages/LandingPage";
import { ComplaintQueuePage } from "./pages/ComplaintQueuePage";
import { DatabaseMonitorPage } from "./pages/DatabaseMonitorPage";
import { LoginModal } from "./components/LoginModal";
import { NirikshaAssistant } from "./components/NirikshaAssistant";
import { useTheme } from "./context/ThemeContext";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("landing");
  const [previousTab, setPreviousTab] = useState<string>("dashboard");
  const [selectedInspectionId, setSelectedInspectionId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [loginModalOpen, setLoginModalOpen] = useState<boolean>(false);
  const { theme, setTheme, activeTheme } = useTheme();

  const [currentUser, setCurrentUser] = useState<{ id?: number; username: string; role: string; full_name: string }>({
    username: "inspector.demo",
    role: "INSPECTOR",
    full_name: "Rajesh Sharma (INS-DL-4029)"
  });

  useEffect(() => {
    const cached = localStorage.getItem("parakh_user");
    if (cached) {
      try {
        setCurrentUser(JSON.parse(cached));
      } catch (e) {}
    }
  }, []);

  const handleSelectInspection = (inspectionId: string) => {
    if (activeTab !== "result") {
      setPreviousTab(activeTab);
    }
    setSelectedInspectionId(inspectionId);
    setActiveTab("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleNavigateToHistory = (_manufacturerName?: string) => {
    setActiveTab("history");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    if (searchQuery.trim().toLowerCase().startsWith("insp_")) {
      handleSelectInspection(searchQuery.trim());
    } else {
      setActiveTab("history");
    }
  };

  const navSections = [
    {
      title: "OVERVIEW",
      items: [
        { id: "landing", label: "Platform Showcase", icon: Scale },
        { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      ],
    },
    {
      title: "INSPECTION",
      items: [
        { id: "scan", label: "Scan Product", icon: UploadCloud },
        { id: "history", label: "Inspection Stacks", icon: History },
        { id: "batch", label: "Batch Scan", icon: Layers },
      ],
    },
    {
      title: "ENFORCEMENT",
      items: [
        { id: "complaints", label: "Complaint Queue", icon: FileWarning },
      ],
    },
    {
      title: "INTELLIGENCE & DB",
      items: [
        { id: "db-monitor", label: "Database Monitor", icon: Database },
        { id: "analytics", label: "Surveillance & Analytics", icon: BarChart3 },
      ],
    },
    {
      title: "REGULATORY",
      items: [
        { id: "rules", label: "Rules Catalog", icon: BookOpen },
        { id: "regulatory-data", label: "Knowledge Base", icon: Database },
        { id: "regulatory-sources", label: "Gazette Sources", icon: FileText },
      ],
    },
    {
      title: "SYSTEM",
      items: [
        { id: "admin", label: "Admin & Audit", icon: ShieldCheck },
      ],
    },
  ];

  const getBreadcrumbTitle = () => {
    switch (activeTab) {
      case "landing": return "Platform Showcase";
      case "dashboard": return "Dashboard";
      case "scan": return "Scan Product";
      case "history": return "Inspection Stacks";
      case "complaints": return "Enforcement & Complaints";
      case "db-monitor": return "Database Monitor";
      case "batch": return "Batch Scan";
      case "analytics": return "Manufacturers & Surveillance";
      case "rules": return "Rules Catalog";
      case "regulatory-data": return "Regulatory Knowledge Base";
      case "regulatory-sources": return "Gazette Sources & Publications";
      case "admin": return "Admin & Audit Trail";
      case "result": return selectedInspectionId ? "Inspection / " + selectedInspectionId : "Inspection Result";
      default: return "PARAKH AI";
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans antialiased selection:bg-blue-100 selection:text-blue-900">
      {/* Top Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-40 h-13 flex items-center px-4 sm:px-6 lg:px-8 justify-between shadow-xs">
        {/* Left: Identity & Breadcrumb */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div
            onClick={() => setActiveTab("landing")}
            className="flex items-center gap-2.5 cursor-pointer select-none"
          >
            <div className="w-7 h-7 rounded bg-blue-900 text-white flex items-center justify-center shadow-xs">
              <Scale className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs tracking-tight text-slate-900 dark:text-white uppercase">
                PARAKH AI
              </span>
              <span className="text-slate-300 dark:text-slate-700">/</span>
              <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                {getBreadcrumbTitle()}
              </span>
            </div>
          </div>
        </div>



        {/* Right: Telemetry, Theme, and Role Switcher */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTheme(activeTheme === "dark" ? "light" : "dark")}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
            title="Toggle Theme"
          >
            {activeTheme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          <HealthStatusBadge />

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block" />

          {/* User Role Chip */}
          <button
            onClick={() => setLoginModalOpen(true)}
            className="flex items-center gap-2 p-1 pl-1.5 pr-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer text-left border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
            title="Click to Switch Role or Login"
          >
            <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-950 border border-blue-200 dark:border-blue-900 flex items-center justify-center text-blue-900 dark:text-blue-300">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="hidden sm:block">
              <span className="text-xs font-semibold text-slate-900 dark:text-slate-100 block leading-tight truncate max-w-[120px]">
                {currentUser.username}
              </span>
              <span className="text-[10px] text-blue-700 dark:text-blue-400 font-bold uppercase tracking-wider block leading-tight">
                {currentUser.role}
              </span>
            </div>
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="hidden lg:flex w-56 flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 select-none">
          <div className="flex-1 overflow-y-auto p-3 space-y-4">
            <button
              onClick={() => { setPreviousTab(activeTab !== "scan" ? activeTab : previousTab); setActiveTab("scan"); }}
              className="w-full py-2 px-3 rounded-lg bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-xs flex items-center justify-center gap-2 transition cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Scan a Product</span>
            </button>

            <div className="space-y-4">
              {navSections.map((sec, secIdx) => (
                <div key={sec.title + "_" + secIdx} className="space-y-0.5">
                  <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2.5 mb-1 block">
                    {sec.title}
                  </span>
                  {sec.items.map((item, itemIdx) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id + "_" + itemIdx}
                        onClick={() => setActiveTab(item.id)}
                        className={"w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer " + (isActive ? "bg-blue-50 dark:bg-blue-950/60 text-blue-900 dark:text-blue-300 font-semibold border-l-2 border-blue-900 dark:border-blue-400" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800")}
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className={"w-3.5 h-3.5 " + (isActive ? "text-blue-900 dark:text-blue-400" : "text-slate-400 dark:text-slate-500")} />
                          <span>{item.label}</span>
                        </div>
                        {isActive && <ChevronRight className="w-3 h-3 text-blue-900 dark:text-blue-400" />}
                      </button>
                    );
                  })}
                </div>
              ))}

              {selectedInspectionId && (
                <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2.5 mb-1 block">
                    ACTIVE INSPECTION
                  </span>
                  <button
                    onClick={() => setActiveTab("result")}
                    className={"w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer " + (activeTab === "result" ? "bg-blue-50 dark:bg-blue-950/60 text-blue-900 dark:text-blue-300 font-semibold border-l-2 border-blue-900 dark:border-blue-400" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800")}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileCheck2 className={"w-3.5 h-3.5 " + (activeTab === "result" ? "text-blue-900 dark:text-blue-400" : "text-slate-400")} />
                      <span className="truncate font-mono text-[11px]">{selectedInspectionId}</span>
                    </div>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-900 dark:bg-blue-400 shrink-0"></span>
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
              <Shield className="w-3.5 h-3.5 text-blue-900 dark:text-blue-400" />
              <span>Advisory DPI Screening</span>
            </div>
            <p className="leading-snug">
              Official statutory determination under Legal Metrology Rules, 2011. Final authority remains with the inspector.
            </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto focus:outline-hidden">
          {activeTab === "landing" && (
            <LandingPage
              onStartInspection={() => setActiveTab("scan")}
              onExploreDashboard={() => setActiveTab("dashboard")}
              onOpenLogin={() => setLoginModalOpen(true)}
              onSelectDemo={(id) => handleSelectInspection(id)}
            />
          )}

          {activeTab === "dashboard" && (
            <DashboardPage
              onNavigate={(tab) => {
                setActiveTab(tab);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
              onSelectInspection={handleSelectInspection}
            />
          )}

          {activeTab === "scan" && (
            <ScanProductPage
              onViewResult={(id) => handleSelectInspection(id)}
              onGoBack={() => { setActiveTab(previousTab || "dashboard"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
            />
          )}

          {activeTab === "batch" && (
            <BatchInspectionPage
              onSelectInspection={handleSelectInspection}
            />
          )}

          {activeTab === "result" && (
            <InspectionResultPage
              key={selectedInspectionId}
              inspectionId={selectedInspectionId}
              onBackToHistory={() => { setActiveTab("history"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
              onScanNew={() => { setPreviousTab("result"); setActiveTab("scan"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
              onGoBack={() => { setActiveTab(previousTab || "scan"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
              onSelectInspection={handleSelectInspection}
            />
          )}

          {activeTab === "history" && (
            <InspectionHistoryPage
              onSelectInspection={handleSelectInspection}
              onScanNew={() => setActiveTab("scan")}
            />
          )}

          {activeTab === "complaints" && (
            <ComplaintQueuePage
              onSelectInspection={handleSelectInspection}
            />
          )}

          {activeTab === "db-monitor" && (
            <DatabaseMonitorPage />
          )}

          {activeTab === "analytics" && (
            <ManufacturerAnalyticsPage
              onNavigateToHistoryWithFilter={handleNavigateToHistory}
            />
          )}

          {activeTab === "admin" && (
            <AdminPortalPage
              currentRole={currentUser.role as any}
            />
          )}

          {activeTab === "rules" && <RuleCatalogPage />}
          {activeTab === "regulatory-data" && <RegulatoryDataPage />}
          {activeTab === "regulatory-sources" && <RegulatorySourcesPage />}
        </main>
      </div>

      {/* NIRIKSHA Floating Regulatory Assistant */}
      <NirikshaAssistant currentInspectionId={selectedInspectionId || undefined} />

      {/* Login & Demo Role Switcher Modal */}
      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        onLoginSuccess={(u) => setCurrentUser(u)}
      />
    </div>
  );
}

export default App;
