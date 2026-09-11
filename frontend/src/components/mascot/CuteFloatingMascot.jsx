import { useState, useEffect, useRef } from "react";
import { Sparkles, MessageCircle, X, MousePointer, BookOpen, ShieldCheck, Scale, CheckCircle2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export const LEGAL_ACTS = [
  {
    num: "01",
    rule: "Rule 6(1)(a)",
    title: "Manufacturer, Packer & Importer Details",
    desc: "Every package must declare the name and complete postal address of the manufacturer, packer, or importer. Incomplete addresses or abbreviations are unlawful.",
    example: "e.g. Manufactured & Packed by ITC Limited, 37 J.L. Nehru Road, Kolkata - 700071",
    icon: "🏭",
  },
  {
    num: "02",
    rule: "Rule 6(1)(b)",
    title: "Generic / Common Name of Commodity",
    desc: "The package must prominently state the common or generic name of the commodity inside so consumers immediately understand what is packed.",
    example: "e.g. Whole Wheat Flour (Atta), Refined Sunflower Oil, Iodized Table Salt",
    icon: "🏷️",
  },
  {
    num: "03",
    rule: "Rule 6(1)(c)",
    title: "Net Quantity in Standard SI Metric Units",
    desc: "Net quantity must be declared in standard legal units (g, kg, ml, l, m, or count). Words like 'when packed' or 'approximate' are strictly prohibited.",
    example: "e.g. Net Qty: 5 kg / Net Content: 500 ml (Standard SI symbols mandatory)",
    icon: "⚖️",
  },
  {
    num: "04",
    rule: "Rule 6(1)(d)",
    title: "Month & Year of Manufacture / Packing / Import",
    desc: "The label must clearly state the month and year of manufacture, packaging, or importation in standard date formats.",
    example: "e.g. Mfg. Date: 08/2026 or Mfd: AUG 2026",
    icon: "📅",
  },
  {
    num: "05",
    rule: "Rule 6(1)(e)",
    title: "Maximum Retail Price (MRP) (Incl. of all taxes)",
    desc: "MRP must be clearly printed in Indian Rupees and must explicitly include '(Inclusive of all taxes)'. Charging above MRP is a punishable legal offense.",
    example: "e.g. MRP ₹275.00 (Incl. of all taxes)",
    icon: "💰",
  },
  {
    num: "06",
    rule: "Rule 6(1)(f)",
    title: "Best Before / Expiry Date",
    desc: "Mandatory for perishable food items, pharmaceuticals, and cosmetics. Must provide exact expiry date or duration from packaging date.",
    example: "e.g. Best Before: 6 months from Mfg Date / Expiry: 12/2027",
    icon: "⏳",
  },
  {
    num: "07",
    rule: "Rule 6(1)(g)",
    title: "Consumer Care & Grievance Redressal Cell",
    desc: "Name, designation, postal address, active telephone helpline number, and email address of the consumer grievance redressal officer.",
    example: "e.g. Contact: Manager, Consumer Care | Tel: 1800-425-4444 | Email: help@itc.in",
    icon: "📞",
  },
  {
    num: "08",
    rule: "Rule 6(1)(h)",
    title: "Country of Origin",
    desc: "Mandatory declaration of the country where the commodity was produced or assembled. Critical for both imported and domestic goods.",
    example: "e.g. Country of Origin: India / Made in India",
    icon: "🌍",
  },
  {
    num: "09",
    rule: "Rule 6(1)(i)",
    title: "Unit Sale Price (USP)",
    desc: "Mandatory for all pre-packaged commodities exceeding 1 kg or 1 liter. Displays the rate per gram, kilogram, milliliter, or piece.",
    example: "e.g. USP: ₹55.00 / kg (for a 5kg pack costing ₹275)",
    icon: "📊",
  },
  {
    num: "10",
    rule: "Rule 6(3)",
    title: "Minimum Font & Numeral Height Standards",
    desc: "Numerals and letters declaring net quantity and MRP must meet statutory height: ≥ 2.0 mm for PDP 100-500 cm², ≥ 4.0 mm for PDP 500-2500 cm².",
    example: "e.g. Principal Display Panel font height measured: ≥ 2.0 mm",
    icon: "📏",
  },
];

const MASCOT_TIPS = [
  "⚖️ Click me to view all 10 Legal Metrology Acts & Rules!",
  "📋 Rule 6(1)(e) mandates 'Inclusive of all taxes' on all MRP declarations!",
  "📏 Rule 6(3) requires minimum 2.0mm numeral height for display areas > 100 cm²!",
  "📊 Rule 6(1)(i) mandates Unit Sale Price (USP) for all packages over 1kg/1L!",
  "🛡️ MetroScan AI automatically verifies all 10 statutory declarations on your scan!",
  "✨ Click anywhere on me to inspect the official 10 Metrology laws!",
];

export default function CuteFloatingMascot() {
  const { user, isConsumer } = useAuth();

  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [chaseCursor, setChaseCursor] = useState(false);
  const [pos, setPos] = useState({ x: window.innerWidth - 125, y: window.innerHeight - 170 });
  const [blinking, setBlinking] = useState(false);
  const [speech, setSpeech] = useState("Click me to see all 10 Legal Metrology Laws! ⚖️");
  const [speechIdx, setSpeechIdx] = useState(0);
  const [minimized, setMinimized] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [happySquint, setHappySquint] = useState(false);
  const [showActsModal, setShowActsModal] = useState(false);

  const mascotRef = useRef(null);
  const posRef = useRef(pos);
  const targetRef = useRef({ x: window.innerWidth - 125, y: window.innerHeight - 170 });

  // Stop chase on Escape
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        setChaseCursor(false);
        setShowActsModal(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Track cursor coordinates
  useEffect(() => {
    const onMove = (e) => setMousePos({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  // Natural blinking
  useEffect(() => {
    const id = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 180);
    }, 3200 + Math.random() * 1500);
    return () => clearInterval(id);
  }, []);

  // Chase cursor flight physics
  useEffect(() => {
    if (!chaseCursor) return;
    let raf;
    const loop = () => {
      const nx = posRef.current.x + (targetRef.current.x - posRef.current.x) * 0.07;
      const ny = posRef.current.y + (targetRef.current.y - posRef.current.y) * 0.07;
      posRef.current = { x: nx, y: ny };
      setPos({ x: nx, y: ny });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [chaseCursor]);

  useEffect(() => {
    if (!chaseCursor) return;
    targetRef.current = { x: mousePos.x - 45, y: mousePos.y - 55 };
  }, [mousePos, chaseCursor]);

  // Mascot eye physics
  const dx = mousePos.x - (pos.x + 45);
  const dy = mousePos.y - (pos.y + 45);
  const dist = Math.sqrt(dx * dx + dy * dy);
  const maxEye = 6.5;
  const pupilX = dist > 0 ? (dx / dist) * Math.min(maxEye, dist / 22) : 0;
  const pupilY = dist > 0 ? (dy / dist) * Math.min(maxEye, dist / 22) : 0;
  const tiltDeg = Math.max(-12, Math.min(12, dx / 40));

  const handleMascotClick = (e) => {
    e?.stopPropagation?.();
    if (chaseCursor) {
      setChaseCursor(false);
      return;
    }
    setHappySquint(true);
    setTimeout(() => setHappySquint(false), 900);
    setShowActsModal(true);
  };

  const roleTitle = isConsumer ? "Inspector Poki (Citizen Mode)" : "Inspector Poki (Enforcement)";

  if (minimized) {
    return (
      <button
        onClick={() => setMinimized(false)}
        className="fixed bottom-5 right-5 z-[9990] px-3 py-2 rounded-full bg-gov-blue hover:bg-blue-800 text-white shadow-2xl hover:scale-105 transition-all border-2 border-white/60 flex items-center gap-2"
        title="Open Inspector Poki"
      >
        <span className="text-xl">🤖</span>
        <span className="text-xs font-black tracking-wide">Inspector Poki (10 Laws)</span>
      </button>
    );
  }

  return (
    <>
      {/* ── 10 LEGAL METROLOGY ACTS MODAL (CLICK ON POKI) ── */}
      {showActsModal && (
        <div
          className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in"
          onClick={() => setShowActsModal(false)}
        >
          <div
            className="relative w-full max-w-3xl bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border-2 border-blue-400/50 dark:border-blue-700/60 flex flex-col max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-5 bg-gradient-to-r from-blue-900 via-gov-blue to-indigo-900 text-white flex items-center justify-between border-b border-blue-800">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-2xl shadow-inner">
                  ⚖️
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-gov-saffron text-white font-mono">
                      Statutory Handbook
                    </span>
                    <span className="text-xs text-blue-200 font-semibold">
                      Legal Metrology Act, 2009
                    </span>
                  </div>
                  <h2 className="text-lg sm:text-xl font-black text-white mt-0.5">
                    10 Mandatory Packaging Rules &amp; Declarations
                  </h2>
                  <p className="text-xs text-blue-100/80">
                    Legal Metrology (Packaged Commodities) Rules, 2011 — Explained by Inspector Poki
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowActsModal(false)}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-center text-white transition-all hover:rotate-90"
                title="Close dialog"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Content / All 10 Rules */}
            <div className="flex-1 overflow-y-auto p-6 space-y-3 bg-gray-50/60 dark:bg-gray-950/60">
              {LEGAL_ACTS.map((act) => (
                <div
                  key={act.rule}
                  className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm hover:shadow-md hover:border-blue-400 dark:hover:border-blue-600 transition-all group"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-xl shrink-0 group-hover:scale-110 transition-transform">
                      {act.icon}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="text-[10px] font-mono font-black px-2 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/50 text-gov-blue dark:text-blue-300">
                          {act.num} • {act.rule}
                        </span>
                        <span className="text-xs font-black text-gray-900 dark:text-white">
                          {act.title}
                        </span>
                      </div>

                      <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
                        {act.desc}
                      </p>

                      <div className="mt-2 text-[11px] font-mono text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800/50 flex items-center gap-1.5">
                        <CheckCircle2 size={12} className="shrink-0 text-emerald-600 dark:text-emerald-400" />
                        <span>{act.example}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 bg-gray-100 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-gov-green" />
                <span>Verified by Ministry of Consumer Affairs, Food &amp; Public Distribution, Govt. of India</span>
              </div>
              <button
                onClick={() => setShowActsModal(false)}
                className="px-5 py-2 rounded-xl bg-gov-blue hover:bg-blue-800 text-white font-bold text-xs shadow-md transition-all"
              >
                Got it, Inspector!
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── FLOATING MASCOT CONTAINER ── */}
      <div
        ref={mascotRef}
        className="fixed z-50 select-none"
        style={{
          left: `${pos.x}px`,
          top: `${pos.y}px`,
          width: "95px",
          height: "120px",
        }}
      >
        {/* Speech Bubble */}
        {speech && (
          <div
            onClick={handleMascotClick}
            className="absolute bottom-[115px] -left-32 w-64 p-3 rounded-2xl bg-white/95 dark:bg-gray-900/95 backdrop-blur-md shadow-2xl border-2 border-blue-300 dark:border-blue-700 text-xs font-semibold text-gray-800 dark:text-gray-100 cursor-pointer animate-bounce-short hover:scale-105 transition-transform"
          >
            <div className="flex items-start justify-between gap-1 mb-1">
              <span className="text-[10px] uppercase tracking-wider text-gov-blue dark:text-blue-400 font-bold flex items-center gap-1">
                <Sparkles size={11} className="text-gov-saffron" />
                Inspector Poki
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSpeech(null);
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-0.5"
              >
                <X size={12} />
              </button>
            </div>
            <p className="leading-snug text-[11px]">{speech}</p>
            <div className="mt-1 text-[9px] text-gov-blue dark:text-blue-300 font-bold underline">
              👉 Click to open 10 Metrology Rules
            </div>
            {/* Pointer arrow */}
            <div className="absolute -bottom-2 right-12 w-4 h-4 bg-white/95 dark:bg-gray-900/95 border-r-2 border-b-2 border-blue-300 dark:border-blue-700 transform rotate-45" />
          </div>
        )}

        {/* Mascot Avatar Body */}
        <div
          onClick={handleMascotClick}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="cursor-pointer relative flex flex-col items-center group"
          style={{
            transform: `rotate(${tiltDeg}deg) scale(${isHovered ? 1.1 : 1})`,
            transition: "transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
          title="Click to view all 10 Legal Metrology Acts!"
        >
          {/* Floating Orb Body */}
          <div
            className="relative w-[80px] h-[80px] rounded-full flex items-center justify-center cursor-pointer"
            style={{
              background: "radial-gradient(circle at 35% 30%, #ffffff 0%, #edf7ff 55%, #bae6fd 100%)",
              boxShadow: "0 0 28px rgba(56, 189, 248, 0.6), inset -2px -4px 8px rgba(186, 230, 253, 0.7), inset 2px 4px 6px rgba(255, 255, 255, 0.95)",
              border: "2.5px solid rgba(186, 230, 253, 0.9)",
              animation: "orb-float 3.6s ease-in-out infinite",
            }}
          >
            <svg viewBox="0 0 100 100" className="w-full h-full">
              {/* Rosy Cheeks */}
              <ellipse cx="22" cy="56" rx="8" ry="5" fill="#fda4af" opacity="0.8" />
              <ellipse cx="78" cy="56" rx="8" ry="5" fill="#fda4af" opacity="0.8" />

              {/* Nose */}
              <circle cx="50" cy="57" r="3.2" fill="#0284c7" />

              {/* Smile */}
              {happySquint ? (
                <path d="M 38 64 Q 50 75 62 64 Z" fill="#e11d48" stroke="#0f172a" strokeWidth="2.2" strokeLinecap="round" />
              ) : (
                <path d="M 40 65 Q 50 72 60 65" fill="none" stroke="#0f172a" strokeWidth="2.8" strokeLinecap="round" />
              )}

              {/* Eyes */}
              {blinking || happySquint ? (
                <g stroke="#0f172a" strokeWidth="3.2" strokeLinecap="round" fill="none">
                  <path d="M 27 43 Q 35 36 43 43" />
                  <path d="M 57 43 Q 65 36 73 43" />
                </g>
              ) : (
                <g>
                  {/* Left Eye */}
                  <ellipse cx="35" cy="43" rx="10.5" ry="12.5" fill="#ffffff" stroke="#94a3b8" strokeWidth="0.8" />
                  <g transform={`translate(${pupilX}, ${pupilY})`}>
                    <circle cx="35" cy="43" r="7.5" fill="#0f172a" />
                    <circle cx="35" cy="43" r="6" fill="#0284c7" />
                    <circle cx="33" cy="40" r="2.8" fill="#ffffff" />
                    <circle cx="37.5" cy="44.5" r="1.2" fill="#ffffff" />
                  </g>

                  {/* Right Eye */}
                  <ellipse cx="65" cy="43" rx="10.5" ry="12.5" fill="#ffffff" stroke="#94a3b8" strokeWidth="0.8" />
                  <g transform={`translate(${pupilX}, ${pupilY})`}>
                    <circle cx="65" cy="43" r="7.5" fill="#0f172a" />
                    <circle cx="65" cy="43" r="6" fill="#0284c7" />
                    <circle cx="63" cy="40" r="2.8" fill="#ffffff" />
                    <circle cx="67.5" cy="44.5" r="1.2" fill="#ffffff" />
                  </g>
                </g>
              )}
            </svg>
          </div>

          {/* Shadow */}
          <div
            className="w-11 h-2.5 rounded-full blur-[2px] mt-1.5"
            style={{
              background: "rgba(15, 23, 42, 0.45)",
              animation: "shadow-pulse 3.6s ease-in-out infinite",
            }}
          />

          {/* Action Pills */}
          <div className="flex items-center gap-1 mt-1">
            <button
              onClick={handleMascotClick}
              className="px-2.5 py-1 rounded-full text-[10px] font-black tracking-wider uppercase border border-blue-400 bg-gov-blue text-white shadow-md hover:bg-blue-800 transition-all flex items-center gap-1"
              title="View 10 Legal Metrology Acts"
            >
              <BookOpen size={10} /> 10 Acts
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setChaseCursor((c) => !c);
              }}
              className={`w-5 h-5 rounded-full flex items-center justify-center border transition-all ${
                chaseCursor
                  ? "bg-red-500 text-white border-red-400 animate-pulse"
                  : "bg-white/90 dark:bg-gray-800/90 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700"
              }`}
              title="Chase cursor"
            >
              <MousePointer size={9} />
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setSpeech(MASCOT_TIPS[speechIdx]);
                setSpeechIdx((p) => (p + 1) % MASCOT_TIPS.length);
              }}
              className="w-5 h-5 rounded-full bg-white/80 dark:bg-gray-800/80 border border-gray-300 dark:border-gray-700 flex items-center justify-center text-gov-blue dark:text-blue-300 hover:bg-white"
              title="Next tip"
            >
              <MessageCircle size={9} />
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setMinimized(true);
              }}
              className="w-5 h-5 rounded-full bg-white/80 dark:bg-gray-800/80 border border-gray-300 dark:border-gray-700 flex items-center justify-center text-gray-400 hover:text-gray-600"
              title="Minimize Poki"
            >
              <X size={9} />
            </button>
          </div>
        </div>
      </div>

      {/* Stop Chase Overlay Button */}
      {chaseCursor && (
        <div className="fixed bottom-6 right-8 z-[9999] pointer-events-auto">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setChaseCursor(false);
            }}
            className="px-4 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white font-black text-xs shadow-2xl flex items-center gap-2 border-2 border-white cursor-pointer hover:scale-105 transition-transform"
          >
            <X size={14} className="stroke-[3]" /> Stop Inspector Poki
          </button>
        </div>
      )}
    </>
  );
}
