import { useState, useCallback } from 'react';
import { Scan, BarChart3, Clock, Loader2, AlertCircle, Package, Sparkles, ChevronRight, ShieldCheck, ArrowRight } from 'lucide-react';
import SovereignHeader from './components/header/SovereignHeader';
import NavigationBar from './components/header/NavigationBar';
import LiveProductScanner from './components/hero/LiveProductScanner';
import AnimatedLoginPage from './components/auth/AnimatedLoginPage';
import PackageDropzone from './components/audit/PackageDropzone';
import ComplianceScorecard from './components/audit/ComplianceScorecard';
import KpiStatGrid from './components/dashboard/KpiStatGrid';
import IndiaHeatmap from './components/dashboard/IndiaHeatmap';
import AnalyticsCharts from './components/dashboard/AnalyticsCharts';
import AuditRegistry from './components/registry/AuditRegistry';
import LegalRulesHandbook from './components/handbook/LegalRulesHandbook';
import SovereignFooter from './components/footer/SovereignFooter';
import CuteFloatingMascot from './components/mascot/CuteFloatingMascot';
import { AppleStyleDock } from './components/navigation/AppleStyleDock';
import CommodityCarouselSection from './components/dashboard/CommodityCarouselSection';
import { InteractiveHoverButton } from './components/ui/interactive-hover-button';
import { useAuth } from './context/AuthContext';
import { useLang } from './context/LanguageContext';

import StatutoryDeclarationsOverlap from './components/declarations/StatutoryDeclarationsOverlap';

/* ─── How It Works section (Expanding Dock Accordion) ─── */
function HowItWorks() {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  const steps = [
    {
      icon: '📸',
      step: '01',
      title: 'Capture Package',
      tag: 'Multi-Angle Input',
      desc: 'Photograph front, back, and MRP panels with any mobile phone, scanner, or handheld terminal.',
      highlight: 'Zero hardware setup needed',
    },
    {
      icon: '⚡',
      step: '02',
      title: 'Edge AI OCR',
      tag: 'Dual-Engine Neural',
      desc: 'PaddleOCR + EasyOCR extract English, Hindi, and regional scripts down to 0.5mm font heights.',
      highlight: 'Instant on-device processing',
    },
    {
      icon: '🤖',
      step: '03',
      title: 'LLM Classification',
      tag: 'Generative Extraction',
      desc: 'Multimodal AI structures chaotic label typography directly into the 10 statutory declaration fields.',
      highlight: '99.4% field precision',
    },
    {
      icon: '⚖️',
      step: '04',
      title: 'Statutory Engine',
      tag: 'Deterministic Rules',
      desc: 'Validates PCR 2011 compliance, net quantity tolerances, MRP tax statements, and Rule 6(3) minimums.',
      highlight: 'Sec 36(1) penalty verification',
    },
    {
      icon: '📄',
      step: '05',
      title: 'Official Certificate',
      tag: 'Legal Export',
      desc: 'Generates tamper-evident digital audit certificate with GPS geo-stamp, QR verification, and PDF export.',
      highlight: 'Court-admissible inspection report',
    },
  ];

  return (
    <section
      id="how-it-works"
      className="py-20 bg-gradient-to-b from-white via-slate-50/60 to-white dark:from-gray-950 dark:via-[#090e1a] dark:to-gray-950 relative overflow-hidden"
    >
      {/* Subtle glowing ambient orbs in background */}
      <div className="absolute top-1/2 left-1/4 w-96 h-96 bg-blue-400/10 dark:bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-amber-400/10 dark:bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-screen-xl mx-auto px-6 relative z-10">
        <div className="text-center mb-14">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gov-blue/10 dark:bg-blue-900/30 text-gov-blue dark:text-blue-300 text-xs font-black uppercase tracking-widest border border-gov-blue/20">
            <Sparkles size={12} className="text-gov-saffron" />
            Statutory Workflow
          </span>
          <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white mt-3 tracking-tight">
            How MetroScan Works
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base mt-2 max-w-xl mx-auto">
            Hover over any stage below to inspect the forensic Legal Metrology verification pipeline
          </p>
        </div>

        {/* Expanding Accordion Dock Container */}
        <div
          onMouseLeave={() => setHoveredIdx(null)}
          className="flex flex-col lg:flex-row gap-3.5 items-stretch min-h-[320px]"
        >
          {steps.map((step, i) => {
            const isHovered = hoveredIdx === i;
            const isAnyHovered = hoveredIdx !== null;
            const isCompressed = isAnyHovered && !isHovered;

            return (
              <div
                key={i}
                onMouseEnter={() => setHoveredIdx(i)}
                className={`glass-card rounded-3xl p-5 sm:p-6 flex flex-col justify-between text-center relative cursor-pointer border transition-all duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] ${
                  isHovered
                    ? 'lg:flex-[2.6] bg-white dark:bg-slate-900/95 border-gov-saffron/80 shadow-2xl shadow-gov-saffron/15 scale-[1.02] z-20 ring-2 ring-gov-saffron/30'
                    : isCompressed
                    ? 'lg:flex-[0.68] opacity-75 hover:opacity-100 scale-[0.98] border-gray-200/50 dark:border-white/5'
                    : 'lg:flex-1 border-white/60 dark:border-white/10 hover:border-gov-saffron/50'
                }`}
              >
                {/* Top Indicator bar on active hover */}
                <div
                  className={`absolute top-0 left-6 right-6 h-1 rounded-full bg-gradient-to-r from-gov-saffron via-amber-400 to-gov-green transition-opacity duration-300 ${
                    isHovered ? 'opacity-100' : 'opacity-0'
                  }`}
                />

                {/* Top Row: Step badge and Tag */}
                <div className="flex items-center justify-between w-full mb-3">
                  <span
                    className={`font-mono text-xs font-black px-2 py-0.5 rounded-md border transition-all ${
                      isHovered
                        ? 'bg-gov-saffron text-white border-gov-saffron'
                        : 'bg-gov-saffron/10 text-gov-saffron border-gov-saffron/30'
                    }`}
                  >
                    {step.step}
                  </span>

                  {isHovered && (
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-gov-blue/10 dark:bg-blue-900/40 text-gov-blue dark:text-blue-300 animate-fade-in">
                      {step.tag}
                    </span>
                  )}
                </div>

                {/* Center: 3D Icon Orb */}
                <div className="my-auto flex flex-col items-center">
                  <div
                    className={`rounded-2xl bg-gradient-to-br from-white to-blue-50/80 dark:from-gray-800/80 dark:to-gray-900/80 border border-white/80 dark:border-white/15 flex items-center justify-center shadow-md transition-all duration-400 ${
                      isHovered
                        ? 'w-20 h-20 text-4xl scale-110 -translate-y-1 shadow-xl shadow-gov-saffron/20 rotate-3'
                        : isCompressed
                        ? 'w-14 h-14 text-2xl'
                        : 'w-16 h-16 text-3xl'
                    }`}
                  >
                    {step.icon}
                  </div>

                  <div
                    className={`font-black text-gray-900 dark:text-white mt-3 leading-snug transition-all ${
                      isHovered
                        ? 'text-lg sm:text-xl text-gov-blue dark:text-blue-300'
                        : isCompressed
                        ? 'text-xs line-clamp-1'
                        : 'text-sm sm:text-base'
                    }`}
                  >
                    {step.title}
                  </div>
                </div>

                {/* Bottom: Description & highlight */}
                <div className="mt-3">
                  <p
                    className={`text-xs text-gray-500 dark:text-gray-400 leading-relaxed transition-all ${
                      isCompressed ? 'hidden lg:hidden' : 'line-clamp-3'
                    }`}
                  >
                    {step.desc}
                  </p>

                  {isHovered && (
                    <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-800 text-[11px] font-bold text-gov-saffron flex items-center justify-center gap-1 animate-fade-in">
                      <span>✓ {step.highlight}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ─── Main audit studio ─── */
function AuditStudio({ onLoginRequired }) {
  const { t } = useLang();
  const { isAuthenticated, isInspector, getAuthHeaders, user } = useAuth();
  const [files, setFiles] = useState({
    front: null,
    back: null,
    mrp: null,
    side_1: null,
    side_2: null,
    reference: null,
  });
  const [storeName, setStoreName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const hasFiles = Object.values(files).some(f => f instanceof File);

  const handleAnalyse = useCallback(async () => {
    if (!isAuthenticated) { onLoginRequired(); return; }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      const panels = ['front', 'back', 'mrp', 'side_1', 'side_2', 'reference'];
      let imageCount = 0;
      for (const key of panels) {
        const f = files[key];
        if (f instanceof File) {
          formData.append('images', f);
          const backendPanel = (key === 'mrp') ? 'mrp_panel' : (key.startsWith('side')) ? 'side' : (key === 'reference') ? 'other' : key;
          formData.append('panel_types', backendPanel);
          imageCount++;
        }
      }

      if (imageCount === 0) {
        throw new Error('Please select at least one package photo to analyze.');
      }

      formData.append('user_role', isInspector ? 'inspector' : 'consumer');
      if (user?.id) {
        formData.append('user_id', user.id);
      }
      if (storeName && storeName.trim()) {
        formData.append('store_name', storeName.trim());
      }

      if (navigator.geolocation) {
        try {
          const pos = await new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(resolve, () => resolve(null), { timeout: 2000, maximumAge: 60000 });
          });
          if (pos && pos.coords) {
            formData.append('latitude', pos.coords.latitude.toString());
            formData.append('longitude', pos.coords.longitude.toString());
          }
        } catch {
          // ignore geolocation error
        }
      }

      const headers = getAuthHeaders ? getAuthHeaders() : {};
      const res = await fetch('/api/v1/scan/analyze', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Server error: ${res.status}`);
      }

      const scanData = await res.json();
      setResult(scanData);
    } catch (err) {
      console.error('Package audit analysis failed:', err);
      setError(err.message || 'Inspection analysis failed. Please check network connection and backend server.');
    }
    setLoading(false);
  }, [files, storeName, isAuthenticated, isInspector, getAuthHeaders, user, onLoginRequired]);

  const reset = () => {
    setFiles({
      front: null,
      back: null,
      mrp: null,
      side_1: null,
      side_2: null,
      reference: null,
    });
    setStoreName('');
    setResult(null);
    setError('');
  };

  return (
    <section id="audit-studio" className="py-12 bg-white dark:bg-gray-950">
      <div className="max-w-screen-xl mx-auto px-6">
        <div className="text-center mb-8">
          <span className="text-gov-blue dark:text-blue-400 text-xs font-bold uppercase tracking-widest">Compliance Studio</span>
          <h2 className="text-3xl font-black text-gray-900 dark:text-white mt-2">Package Audit Studio</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">
            Upload package photos and get instant compliance verification
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Upload panel */}
          <div className="lg:col-span-5">
            <div className="gov-card p-6 h-full">
              <div className="flex items-center gap-2 mb-5">
                <Package size={18} className="text-gov-blue" />
                <h3 className="font-bold text-gray-900 dark:text-white">{t('uploadTitle')}</h3>
              </div>
              <PackageDropzone files={files} onFilesChange={setFiles} />

              {isInspector && (
                <div className="mt-4">
                  <label className="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-1">
                    Inspection Site / Retail Establishment
                  </label>
                  <input
                    type="text"
                    value={storeName}
                    onChange={(e) => setStoreName(e.target.value)}
                    placeholder="e.g. Reliance Smart Supermarket, Sector 62"
                    className="gov-input py-2 text-sm w-full"
                  />
                </div>
              )}

              {error && (
                <div className="mt-4 flex items-start gap-2 text-red-600 dark:text-red-400 text-xs bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                  <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              <div className="flex items-center gap-3 mt-5">
                <InteractiveHoverButton
                  id="btn-analyse"
                  onClick={handleAnalyse}
                  disabled={!hasFiles || loading}
                  className="flex-1 py-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <><Loader2 size={16} className="animate-spin" /> {t('processingMsg')}</>
                  ) : (
                    <><Scan size={16} /> {t('analyzeBtn')}</>
                  )}
                </InteractiveHoverButton>
                {(hasFiles || result) && (
                  <button onClick={reset} className="btn-gov-outline py-2.5 px-4 text-xs rounded-full">
                    {t('clearBtn')}
                  </button>
                )}
              </div>

              {!isAuthenticated && (
                <p className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-2.5 mt-3 flex items-center gap-1.5">
                  <Sparkles size={12} />
                  Login as Inspector for official PDF certificates
                </p>
              )}
            </div>
          </div>

          {/* Results panel */}
          <div className="lg:col-span-7">
            <div className="gov-card p-6 min-h-[400px] flex flex-col">
              {!result && !loading && (
                <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
                  <div className="w-20 h-20 rounded-3xl bg-gov-blue/5 dark:bg-blue-900/20 flex items-center justify-center mb-4">
                    <Scan size={32} className="text-gov-blue/30 dark:text-blue-400/30" />
                  </div>
                  <p className="text-gray-400 dark:text-gray-600 text-sm font-medium">
                    Upload package images and click<br />
                    <span className="text-gov-blue dark:text-blue-400 font-bold">Analyse Package</span> to begin
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2 justify-center">
                    {['10 Rules Checked', 'Font Height Measured', 'PDF Certificate', 'Tamper-Proof Audit'].map(feat => (
                      <span key={feat} className="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-600 px-2 py-1 rounded-full border border-gray-100 dark:border-gray-800">
                        <ChevronRight size={10} /> {feat}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {loading && (
                <div className="flex-1 flex flex-col items-center justify-center py-12 text-center">
                  <div className="relative w-16 h-16 mb-4">
                    <div className="absolute inset-0 rounded-full border-4 border-gov-blue/20" />
                    <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-gov-blue animate-spin" />
                    <Scan size={20} className="absolute inset-0 m-auto text-gov-blue" />
                  </div>
                  <p className="text-gray-500 dark:text-gray-400 text-sm font-medium">{t('processingMsg')}</p>
                  <div className="flex gap-2 mt-4 text-xs text-gray-400 flex-wrap justify-center">
                    {['OCR Detection', 'AI Classification', 'Rule Validation', 'PDF Generation'].map((step, i) => (
                      <span key={step} className="px-2 py-1 rounded-full border border-gray-100 dark:border-gray-800 animate-pulse" style={{ animationDelay: `${i * 0.3}s` }}>
                        {step}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result && (
                <ComplianceScorecard result={result} onReset={reset} />
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Dashboard section ─── */
function DashboardSection() {
  const { t } = useLang();
  const { user } = useAuth();
  return (
    <section id="dashboard" className="py-8 sm:py-12 bg-gov-canvas dark:bg-gray-900 border-b border-gray-200/60 dark:border-white/5">
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 space-y-8">
        <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-200/80 dark:border-gray-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-gov-blue dark:text-blue-400 text-xs font-bold uppercase tracking-widest">
                Enforcement Command Center
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white mt-1">
              Legal Metrology Officer Dashboard
            </h2>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
              Live GIS surveillance · National inspection registry · Form 1 Statutory enforcement
            </p>
          </div>
          {user?.badge_id && (
            <div className="flex items-center gap-3 bg-white dark:bg-gray-800 border border-gov-blue/20 px-4 py-2 rounded-xl shadow-sm">
              <div className="text-right">
                <div className="text-[10px] text-gray-400 uppercase font-bold">Officer on Duty</div>
                <div className="text-sm font-bold text-gray-900 dark:text-white">{user.full_name}</div>
              </div>
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 font-bold border border-amber-300 dark:border-amber-700">
                {user.badge_id}
              </span>
            </div>
          )}
        </div>
        <KpiStatGrid />
      </div>
    </section>
  );
}

/* ─── Compliance Analytics section ─── */
function AnalyticsSection() {
  return (
    <section id="analytics-trends" className="py-12 bg-gov-canvas dark:bg-gray-900 border-b border-gray-200/60 dark:border-white/5">
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 space-y-8">
        <div>
          <span className="text-gov-blue dark:text-blue-400 text-xs font-bold uppercase tracking-widest">
            Enforcement Intelligence
          </span>
          <h2 className="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white mt-1">
            Sector-Wise Compliance Analytics &amp; Trends
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
            Real-time distribution across packaged commodity sectors and rule infraction rates
          </p>
        </div>
        <CommodityCarouselSection />
        <AnalyticsCharts />
      </div>
    </section>
  );
}

/* ─── GIS Map section ─── */
function GisMapSection() {
  return (
    <section id="gis-map" className="py-12 bg-white dark:bg-gray-950 border-b border-gray-200/60 dark:border-white/5">
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 space-y-6">
        <div>
          <span className="text-gov-blue dark:text-blue-400 text-xs font-bold uppercase tracking-widest">
            Geographic Surveillance
          </span>
          <h2 className="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white mt-1">
            National Enforcement GIS Heatmap
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
            Field inspections, geo-tagged violations, and jurisdictional retail audit tracking
          </p>
        </div>
        <IndiaHeatmap />
      </div>
    </section>
  );
}

/* ─── Registry section ─── */
function RegistrySection() {
  const { t } = useLang();
  return (
    <section id="audit-registry" className="py-12 bg-white dark:bg-gray-950">
      <div className="max-w-screen-xl mx-auto px-6">
        <div className="mb-6">
          <span className="text-gov-blue dark:text-blue-400 text-xs font-bold uppercase tracking-widest">History</span>
          <h2 className="text-2xl font-black text-gray-900 dark:text-white mt-1">{t('recentScans')}</h2>
        </div>
        <AuditRegistry />
      </div>
    </section>
  );
}

/* ─── Root App ─── */
export default function App() {
  const { user, isAuthenticated, loading, isInspector, isConsumer } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);

  const handleLoginRequired = useCallback(() => setLoginOpen(true), []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070c18] flex flex-col items-center justify-center text-white p-4">
        <div className="w-12 h-12 border-4 border-amber-500/20 border-t-amber-500 rounded-full animate-spin mb-4" />
        <p className="text-sm font-semibold text-gray-300">Initializing MetroScan Portal...</p>
      </div>
    );
  }

  // Force login first: unauthenticated users always land directly on AnimatedLoginPage
  if (!isAuthenticated || !user) {
    return <AnimatedLoginPage fullScreenMode={true} />;
  }

  return (
    <div className="min-h-screen flex flex-col dark-transition pb-20">
      <SovereignHeader onLoginClick={() => setLoginOpen(true)} />
      <NavigationBar />

      <main className="flex-1">
        {isConsumer ? (
          /* ── Citizen Experience: Pure compliance verification, NO MAP ── */
          <>
            <div id="home">
              <LiveProductScanner onScanClick={() => document.querySelector('#audit-studio')?.scrollIntoView({ behavior: 'smooth' })} />
            </div>
            <HowItWorks />
            <StatutoryDeclarationsOverlap />
            <AuditStudio onLoginRequired={handleLoginRequired} />
            <LegalRulesHandbook />
            <RegistrySection />
          </>
        ) : (
          /* ── Inspector & Regulator Experience: Full Enforcement Command Center with GIS Heatmap lower down ── */
          <>
            <DashboardSection />
            <AuditStudio onLoginRequired={handleLoginRequired} />
            <RegistrySection />
            <AnalyticsSection />
            <GisMapSection />
            <LegalRulesHandbook />
          </>
        )}
      </main>

      <SovereignFooter />

      {loginOpen && <AnimatedLoginPage onClose={() => setLoginOpen(false)} />}
      {/* Piku Mascot Companion — available for both Citizens and Inspectors */}
      <CuteFloatingMascot />
      <AppleStyleDock onLoginClick={() => setLoginOpen(true)} />
    </div>
  );
}
