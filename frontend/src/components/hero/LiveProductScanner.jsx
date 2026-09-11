import { useState, useEffect, useRef } from 'react';
import { Scan, Package, CheckCircle, AlertTriangle, XCircle, Barcode } from 'lucide-react';
import { useLang } from '../../context/LanguageContext';
import { InteractiveHoverButton } from '@/components/ui/interactive-hover-button';

/* Live scanning tag floating over product */
function ScanTag({ label, status, style }) {
  const color = status === 'pass'
    ? 'border-green-400 bg-green-900/80 text-green-300'
    : status === 'fail'
    ? 'border-red-400 bg-red-900/80 text-red-300'
    : 'border-amber-400 bg-amber-900/80 text-amber-300';

  const Icon = status === 'pass' ? CheckCircle : status === 'fail' ? XCircle : AlertTriangle;

  return (
    <div
      className={`absolute flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono font-semibold backdrop-blur-sm ${color} animate-fade-in shadow-lg`}
      style={style}
    >
      <Icon size={11} />
      {label}
    </div>
  );
}

/* Bounding box wireframe on product */
function BoundingBox({ rect, color = '#F39C12', label, visible }) {
  if (!visible) return null;
  return (
    <>
      <div
        className="absolute border-2 rounded pointer-events-none"
        style={{
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
          borderColor: color,
          boxShadow: `0 0 8px ${color}60`,
          transition: 'all 0.5s ease',
        }}
      />
      {label && (
        <div
          className="absolute text-[9px] font-mono font-bold px-1.5 py-0.5 rounded"
          style={{
            left: rect.left,
            top: typeof rect.top === 'number' ? rect.top - 18 : `calc(${rect.top} - 18px)`,
            background: color,
            color: '#000',
          }}
        >
          {label}
        </div>
      )}
    </>
  );
}

/* Product 3D Package SVG */
function ProductPackage({ productIndex }) {
  const products = [
    { name: 'Wheat Flour', color1: '#D4A96A', color2: '#C49A5A', accent: '#8B6F47', label: 'ATTA 5kg' },
    { name: 'Biscuits', color1: '#E8D5A3', color2: '#D4B896', accent: '#A0845C', label: 'Parle-G' },
    { name: 'Face Cream', color1: '#A8D8EA', color2: '#85C1E9', accent: '#5DADE2', label: 'Cream 50g' },
    { name: 'Spice', color1: '#E74C3C', color2: '#C0392B', accent: '#922B21', label: 'Masala 100g' },
  ];
  const p = products[productIndex % products.length];

  return (
    <svg viewBox="0 0 120 160" className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
      {/* Main package face */}
      <rect x="15" y="20" width="90" height="120" rx="6" fill={p.color1} />
      {/* Package side shadow */}
      <polygon points="105,20 120,30 120,150 105,140" fill={p.color2} />
      {/* Top panel */}
      <polygon points="15,20 105,20 120,30 30,30" fill={p.accent} opacity="0.5" />

      {/* Brand name band */}
      <rect x="15" y="55" width="90" height="30" fill={p.accent} opacity="0.3" />
      <text x="60" y="75" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#1A1A1A" fontFamily="serif">
        {p.label}
      </text>

      {/* MRP text */}
      <text x="60" y="100" textAnchor="middle" fontSize="7" fill="#1A1A1A" fontFamily="monospace">
        MRP ₹240.00
      </text>
      <text x="60" y="110" textAnchor="middle" fontSize="6" fill="#666" fontFamily="monospace">
        Incl. of all taxes
      </text>

      {/* Barcode at bottom */}
      <g transform="translate(28, 120)">
        {Array.from({ length: 32 }, (_, i) => (
          <rect
            key={i}
            x={i * 2}
            y="0"
            width={i % 3 === 0 ? 1.5 : 1}
            height="18"
            fill="#1A1A1A"
          />
        ))}
        <text x="32" y="28" textAnchor="middle" fontSize="5" fill="#666" fontFamily="monospace">
          8901234567890
        </text>
      </g>

      {/* Manufacturer text */}
      <text x="60" y="42" textAnchor="middle" fontSize="5.5" fill="#444" fontFamily="sans-serif">
        Mfg: ITC Limited, Kolkata
      </text>
      <text x="60" y="50" textAnchor="middle" fontSize="5" fill="#666" fontFamily="sans-serif">
        Best Before: 12 months
      </text>
    </svg>
  );
}

const SCAN_TAGS = [
  { label: 'MRP ✓ Incl. Tax', status: 'pass', style: { top: '38%', left: '-35%' } },
  { label: 'Net Qty: 5 kg', status: 'pass', style: { top: '28%', right: '-42%' } },
  { label: 'Mfg Date: 08/2026', status: 'pass', style: { top: '55%', right: '-48%' } },
  { label: 'Consumer Care ⚠', status: 'warn', style: { top: '65%', left: '-40%' } },
  { label: 'Font: 1.8mm ✓', status: 'pass', style: { top: '78%', right: '-38%' } },
];

const BOUNDING_BOXES = [
  { rect: { left: '18%', top: '22%', width: '64%', height: '14%' }, color: '#27AE60', label: 'BRAND' },
  { rect: { left: '10%', top: '38%', width: '80%', height: '20%' }, color: '#F39C12', label: 'PRODUCT' },
  { rect: { left: '15%', top: '60%', width: '70%', height: '12%' }, color: '#27AE60', label: 'MRP' },
  { rect: { left: '20%', top: '74%', width: '60%', height: '20%' }, color: '#27AE60', label: 'BARCODE' },
];

export default function LiveProductScanner({ onScanClick }) {
  const { t } = useLang();
  const [scanPhase, setScanPhase] = useState(0); // 0-idle, 1-scanning, 2-detected
  const [visibleTags, setVisibleTags] = useState([]);
  const [visibleBoxes, setVisibleBoxes] = useState([]);
  const [productIndex, setProductIndex] = useState(0);
  const phaseRef = useRef(0);

  useEffect(() => {
    // Auto-cycle through scan animation
    const cycle = () => {
      setVisibleTags([]);
      setVisibleBoxes([]);
      setScanPhase(1); // scanning

      // Reveal bounding boxes progressively
      BOUNDING_BOXES.forEach((_, i) => {
        setTimeout(() => {
          setVisibleBoxes(prev => [...prev, i]);
        }, 600 + i * 450);
      });

      // Reveal tags
      SCAN_TAGS.forEach((_, i) => {
        setTimeout(() => {
          setVisibleTags(prev => [...prev, i]);
        }, 900 + i * 500);
      });

      // Complete
      setTimeout(() => {
        setScanPhase(2);
        setTimeout(() => {
          setScanPhase(0);
          setProductIndex(p => (p + 1) % 4);
        }, 3000);
      }, 900 + SCAN_TAGS.length * 500 + 800);
    };

    const interval = setInterval(() => {
      cycle();
    }, 7500);

    // Start first cycle
    setTimeout(cycle, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="home" className="relative min-h-[92vh] flex flex-col items-center justify-center overflow-hidden bg-gov-mesh">
      {/* Ambient background dots */}
      <div className="absolute inset-0 pointer-events-none">
        {Array.from({ length: 30 }, (_, i) => (
          <div
            key={i}
            className="absolute rounded-full"
            style={{
              width: 2 + (i % 3),
              height: 2 + (i % 3),
              left: `${(i * 3.4) % 100}%`,
              top: `${(i * 7.1 + 15) % 85}%`,
              background: i % 3 === 0 ? '#F39C12' : '#1A5276',
              opacity: 0.15 + (i % 4) * 0.05,
            }}
          />
        ))}
      </div>

      {/* Main layout: 3-column editorial (text / product / text) */}
      <div className="relative z-10 w-full max-w-screen-xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-16 items-center">

          {/* Left column — headline */}
          <div className="text-left lg:col-span-1 order-2 lg:order-1">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-gov-saffron/40 bg-gov-saffron/10 text-gov-saffron text-xs font-bold uppercase tracking-widest mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-gov-saffron animate-pulse" />
              Legal Metrology PC Rules 2011
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-[0.95] tracking-tight mb-4">
              {t('heroHeadline')}
              <span className="block text-gov-saffron mt-2">{t('heroHeadline2')}</span>
            </h1>
            <p className="text-blue-200 text-sm sm:text-base leading-relaxed mb-8 max-w-sm">
              {t('heroSubtitle')}
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <InteractiveHoverButton
                id="btn-hero-scan"
                onClick={onScanClick}
                className="w-full sm:w-auto px-7 py-3 text-base bg-gov-saffron border-amber-400 text-white hover:bg-amber-500 shadow-lg"
              >
                {t('scanNowBtn')}
              </InteractiveHoverButton>
              <button
                id="btn-hero-dashboard"
                onClick={() => document.querySelector('#dashboard')?.scrollIntoView({ behavior: 'smooth' })}
                className="btn-gov-outline border-white/30 text-white hover:bg-white hover:text-gov-blue px-6 py-3 text-sm rounded-full"
              >
                {t('viewDashboard')}
              </button>
            </div>
          </div>

          {/* Center — Live product scan animation (DESIGN.md void-mode) */}
          <div className="relative lg:col-span-1 order-1 lg:order-2 flex items-center justify-center">
            <div className="relative w-56 h-72 sm:w-64 sm:h-80">

              {/* Laser scan line */}
              {scanPhase === 1 && (
                <div className="scan-laser" />
              )}

              {/* Corner bracket guides */}
              {[
                'top-0 left-0 border-t-2 border-l-2',
                'top-0 right-0 border-t-2 border-r-2',
                'bottom-0 left-0 border-b-2 border-l-2',
                'bottom-0 right-0 border-b-2 border-r-2',
              ].map((cls, i) => (
                <div
                  key={i}
                  className={`absolute w-8 h-8 border-gov-saffron ${cls}`}
                  style={{ boxShadow: '0 0 6px rgba(243,156,18,0.4)' }}
                />
              ))}

              {/* Product SVG */}
              <div className="absolute inset-4 animate-float">
                <ProductPackage productIndex={productIndex} />
              </div>

              {/* Bounding boxes on product */}
              {BOUNDING_BOXES.map((box, i) => (
                <BoundingBox
                  key={i}
                  rect={box.rect}
                  color={box.color}
                  label={box.label}
                  visible={visibleBoxes.includes(i)}
                />
              ))}

              {/* Floating scan tags */}
              {SCAN_TAGS.map((tag, i) =>
                visibleTags.includes(i) ? (
                  <ScanTag key={i} label={tag.label} status={tag.status} style={tag.style} />
                ) : null
              )}

              {/* Status overlay when complete */}
              {scanPhase === 2 && (
                <div className="absolute inset-x-0 bottom-0 flex justify-center">
                  <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/20 border border-green-400/50 text-green-300 text-xs font-bold animate-bounce-in">
                    <CheckCircle size={13} /> Compliance Verified
                  </div>
                </div>
              )}

              {/* Scan status indicator */}
              <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <div className={`flex items-center gap-2 text-xs font-mono ${
                  scanPhase === 1 ? 'text-gov-saffron' : scanPhase === 2 ? 'text-green-400' : 'text-blue-300/60'
                }`}>
                  {scanPhase === 1 && <><span className="w-1.5 h-1.5 rounded-full bg-gov-saffron animate-pulse" /> Scanning...</>}
                  {scanPhase === 2 && <><span className="w-1.5 h-1.5 rounded-full bg-green-400" /> Analysis Complete</>}
                  {scanPhase === 0 && <><Barcode size={12} /> Ready to Scan</>}
                </div>
              </div>
            </div>
          </div>

          {/* Right column — stats */}
          <div className="text-right lg:col-span-1 order-3 space-y-4">
            {[
              { num: '< 30s', label: 'Full compliance check', sub: 'From photo to PDF certificate' },
              { num: '10', label: 'Rules verified', sub: 'All Rule 6(1)(a)–(i) & Font height' },
              { num: '100%', label: 'Offline capable', sub: 'Works without internet' },
              { num: '3', label: 'Languages', sub: 'English · हिन्दी · मराठी' },
            ].map((stat, i) => (
              <div key={i} className="text-right">
                <div className="text-2xl font-black text-gov-saffron leading-none">{stat.num}</div>
                <div className="text-white font-semibold text-sm mt-0.5">{stat.label}</div>
                <div className="text-blue-300/60 text-xs">{stat.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scroll cue */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 text-blue-300/50 animate-bounce">
        <div className="w-px h-8 bg-gradient-to-b from-transparent to-blue-300/30" />
        <div className="text-[10px] uppercase tracking-widest font-medium">Scroll</div>
      </div>
    </section>
  );
}
