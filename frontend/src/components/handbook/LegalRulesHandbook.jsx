import { useState } from 'react';
import { Calculator, Sparkles, Scale, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

export default function LegalRulesHandbook() {
  const [activeTab, setActiveTab] = useState('font'); // 'font' | 'usp' | 'mpe'

  // Font Height Calculator State
  const [pdpArea, setPdpArea] = useState(250);
  const [containerType, setContainerType] = useState('printed'); // 'printed' | 'blown'

  // USP Calculator State
  const [mrp, setMrp] = useState(150);
  const [netQty, setNetQty] = useState(750);
  const [unit, setUnit] = useState('g'); // 'g' | 'ml' | 'kg' | 'l'

  // MPE Calculator State
  const [declaredWeight, setDeclaredWeight] = useState(500); // in grams or ml
  const [actualWeight, setActualWeight] = useState(488);

  // Compute Font Height according to Table 1 of First Schedule
  const getMinFontHeight = (area, type) => {
    if (area <= 50) return type === 'blown' ? 2.0 : 1.0;
    if (area <= 100) return type === 'blown' ? 3.0 : 1.5;
    if (area <= 500) return type === 'blown' ? 4.0 : 2.0;
    if (area <= 2500) return type === 'blown' ? 6.0 : 4.0;
    return type === 'blown' ? 8.0 : 6.0;
  };

  const minFontHeight = getMinFontHeight(Number(pdpArea) || 0, containerType);

  // Compute USP
  const calculateUSP = () => {
    const numMrp = parseFloat(mrp) || 0;
    const numQty = parseFloat(netQty) || 1;

    if (unit === 'g' || unit === 'ml') {
      if (numQty >= 1000) {
        const qtyInBase = numQty / 1000;
        const usp = (numMrp / qtyInBase).toFixed(2);
        const baseUnit = unit === 'g' ? 'kg' : 'L';
        return { usp, unit: `₹${usp} per ${baseUnit}`, standard: `₹${(numMrp / numQty).toFixed(2)} per ${unit}` };
      } else {
        const uspPer100 = ((numMrp / numQty) * 100).toFixed(2);
        const uspPer1 = (numMrp / numQty).toFixed(2);
        return {
          usp: uspPer100,
          unit: `₹${uspPer100} per 100${unit}`,
          standard: `₹${uspPer1} per ${unit}`,
        };
      }
    } else {
      // kg or L
      const usp = (numMrp / numQty).toFixed(2);
      return { usp, unit: `₹${usp} per ${unit}`, standard: `₹${usp} per ${unit}` };
    }
  };

  const uspResult = calculateUSP();

  // Compute Second Schedule Maximum Permissible Error (MPE)
  const calculateMPE = () => {
    const decl = parseFloat(declaredWeight) || 0;
    const actual = parseFloat(actualWeight) || 0;

    let mpePercent = null;
    let mpeGrams = 0;
    let tierText = '';

    if (decl <= 50) {
      mpePercent = 9.0;
      mpeGrams = (decl * 0.09);
      tierText = '9.0% Ratio-based (Statutory standard for ≤ 50g/ml small sachets e.g., shampoo, sauces, spices)';
    } else if (decl <= 100) {
      mpeGrams = 4.5;
      tierText = 'Fixed 4.5g / ml (50g – 100g tier)';
    } else if (decl <= 200) {
      mpePercent = 4.5;
      mpeGrams = (decl * 0.045);
      tierText = '4.5% Ratio-based (100g – 200g tier)';
    } else if (decl <= 300) {
      mpeGrams = 9.0;
      tierText = 'Fixed 9.0g / ml (200g – 300g tier)';
    } else if (decl <= 500) {
      mpePercent = 3.0;
      mpeGrams = (decl * 0.03);
      tierText = '3.0% Ratio-based (300g – 500g tier)';
    } else if (decl <= 1000) {
      mpeGrams = 15.0;
      tierText = 'Fixed 15.0g / ml (500g – 1000g tier)';
    } else {
      mpePercent = 1.5;
      mpeGrams = (decl * 0.015);
      tierText = '1.5% Ratio-based (> 1000g bulk tier)';
    }

    const minPermissible = decl - mpeGrams;
    const diff = actual - decl;
    const isCompliant = actual >= minPermissible;

    return {
      mpeGrams: mpeGrams < 1 ? mpeGrams.toFixed(2) : mpeGrams.toFixed(1),
      minPermissible: minPermissible < 1 ? minPermissible.toFixed(2) : minPermissible.toFixed(1),
      diff: diff.toFixed(1),
      mpePercent,
      tierText,
      isCompliant,
    };
  };

  const mpeResult = calculateMPE();

  return (
    <section id="legal-rules" className="py-20 bg-gov-canvas dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
      <div className="max-w-screen-xl mx-auto px-6">
        {/* Section Header */}
        <div className="text-center mb-12">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gov-blue/10 dark:bg-blue-900/30 text-gov-blue dark:text-blue-300 text-xs font-black uppercase tracking-widest border border-gov-blue/20">
            <Calculator size={13} className="text-gov-saffron" />
            Statutory Calculators & Enforcement Tools
          </span>
          <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white mt-3 tracking-tight">
            Legal Metrology Enforcement Workbench
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base mt-2 max-w-2xl mx-auto">
            Interactive statutory calculators engineered according to the Legal Metrology (Packaged Commodities) Rules, 2011 for enforcement officers, brand packagers, and legal auditors.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex justify-center mb-10">
          <div className="inline-flex rounded-2xl bg-gray-200/70 dark:bg-gray-800/80 p-1.5 gap-1.5 shadow-inner border border-gray-300/40 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('font')}
              className={`px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all flex items-center gap-2 ${
                activeTab === 'font'
                  ? 'bg-white dark:bg-gray-700 text-gov-blue dark:text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Calculator size={15} className="text-blue-500" />
              Rule 6(3) Font Auditor
            </button>
            <button
              onClick={() => setActiveTab('usp')}
              className={`px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all flex items-center gap-2 ${
                activeTab === 'usp'
                  ? 'bg-white dark:bg-gray-700 text-gov-blue dark:text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Sparkles size={15} className="text-gov-saffron" />
              Rule 6(1)(i) USP Generator
            </button>
            <button
              onClick={() => setActiveTab('mpe')}
              className={`px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all flex items-center gap-2 ${
                activeTab === 'mpe'
                  ? 'bg-white dark:bg-gray-700 text-gov-blue dark:text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Scale size={15} className="text-emerald-500" />
              Second Schedule MPE Checker
            </button>
          </div>
        </div>

        {/* Tab 1: Font Height Calculator */}
        {activeTab === 'font' && (
          <div className="max-w-4xl mx-auto glass-card rounded-3xl p-6 sm:p-8 border border-white/60 dark:border-white/10 shadow-2xl">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100 dark:border-gray-800">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <Calculator size={24} />
              </div>
              <div>
                <h3 className="text-xl font-black text-gray-900 dark:text-white">
                  Rule 6(3) Minimum Font Height Calculator
                </h3>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  Calculate statutory letter and numeral height according to the Principal Display Panel (PDP) area.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Principal Display Panel Area ({pdpArea} cm²):
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="10"
                    max="3000"
                    step="10"
                    value={pdpArea}
                    onChange={(e) => setPdpArea(e.target.value)}
                    className="w-full accent-gov-blue cursor-pointer h-2 bg-gray-200 rounded-lg dark:bg-gray-700"
                  />
                  <input
                    type="number"
                    min="1"
                    max="5000"
                    value={pdpArea}
                    onChange={(e) => setPdpArea(e.target.value)}
                    className="w-24 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-mono text-center font-bold dark:bg-gray-800 dark:text-white"
                  />
                </div>
                <p className="text-[11px] text-gray-400 mt-2">
                  PDP = Height × Width of the main face of rectangular package (cm²).
                </p>
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Container Packaging Medium:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setContainerType('printed')}
                    className={`p-3 rounded-xl border text-xs font-bold transition-all text-center ${
                      containerType === 'printed'
                        ? 'border-gov-blue bg-blue-50 dark:bg-blue-900/30 text-gov-blue dark:text-blue-300 shadow-sm'
                        : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    📄 Printed / Labeled
                  </button>
                  <button
                    onClick={() => setContainerType('blown')}
                    className={`p-3 rounded-xl border text-xs font-bold transition-all text-center ${
                      containerType === 'blown'
                        ? 'border-gov-blue bg-blue-50 dark:bg-blue-900/30 text-gov-blue dark:text-blue-300 shadow-sm'
                        : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    🧴 Blown / Moulded
                  </button>
                </div>
                <p className="text-[11px] text-gray-400 mt-2">
                  Moulded containers enforce higher relief minimums under First Schedule.
                </p>
              </div>
            </div>

            {/* Result Box */}
            <div className="bg-gradient-to-br from-blue-900 via-indigo-950 to-slate-950 text-white rounded-3xl p-6 sm:p-8 text-center relative overflow-hidden border border-blue-400/30 shadow-xl">
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-blue-300">
                Statutory Minimum Height Requirement (First Schedule)
              </span>
              <div className="text-5xl font-black my-3 font-mono tracking-tight text-white drop-shadow">
                {minFontHeight} mm
              </div>
              <p className="text-xs sm:text-sm text-blue-100/90 max-w-lg mx-auto leading-relaxed">
                Any mandatory declaration (MRP, Net Quantity, Mfg Date) on a package with{' '}
                <strong className="text-white">{pdpArea} cm²</strong> PDP area must have a numeral and letter height of at least{' '}
                <strong className="text-white">{minFontHeight} mm</strong>.
              </p>

              <div className="mt-5 pt-4 border-t border-white/15 flex flex-wrap justify-center gap-6 text-xs text-blue-200">
                <div>
                  Area Bracket:{' '}
                  <span className="font-bold text-white">
                    {pdpArea <= 50
                      ? '≤ 50 cm²'
                      : pdpArea <= 100
                      ? '51 – 100 cm²'
                      : pdpArea <= 500
                      ? '101 – 500 cm²'
                      : pdpArea <= 2500
                      ? '501 – 2500 cm²'
                      : '> 2500 cm²'}
                  </span>
                </div>
                <div>
                  Enforcement: <span className="font-bold text-emerald-400">Zero Tolerance (Strict)</span>
                </div>
                <div>
                  Offense: <span className="font-bold text-amber-300">Section 36(1)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: USP Calculator */}
        {activeTab === 'usp' && (
          <div className="max-w-4xl mx-auto glass-card rounded-3xl p-6 sm:p-8 border border-white/60 dark:border-white/10 shadow-2xl">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100 dark:border-gray-800">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-gov-saffron">
                <Sparkles size={24} />
              </div>
              <div>
                <h3 className="text-xl font-black text-gray-900 dark:text-white">
                  Rule 6(1)(i) Unit Sale Price (USP) Generator
                </h3>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  Calculates official statutory Unit Sale Price format required under the Legal Metrology amendment.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Maximum Retail Price (₹):
                </label>
                <input
                  type="number"
                  min="1"
                  step="0.5"
                  value={mrp}
                  onChange={(e) => setMrp(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-mono font-bold dark:bg-gray-800 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Net Quantity Value:
                </label>
                <input
                  type="number"
                  min="1"
                  value={netQty}
                  onChange={(e) => setNetQty(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-mono font-bold dark:bg-gray-800 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Metric Unit:
                </label>
                <select
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-bold dark:bg-gray-800 dark:text-white"
                >
                  <option value="g">Grams (g)</option>
                  <option value="kg">Kilograms (kg)</option>
                  <option value="ml">Millilitres (ml)</option>
                  <option value="l">Litres (L)</option>
                </select>
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-600 via-orange-700 to-slate-950 text-white rounded-3xl p-6 sm:p-8 text-center relative overflow-hidden border border-amber-400/30 shadow-xl">
              <span className="text-xs font-mono font-bold uppercase tracking-widest text-amber-200">
                Official Declaration Format to Print Beside MRP
              </span>
              <div className="text-4xl sm:text-5xl font-black my-3 font-mono tracking-tight text-white drop-shadow">
                {uspResult.unit}
              </div>
              <p className="text-xs sm:text-sm text-amber-100/90 max-w-lg mx-auto">
                Under Rule 6(1)(i), this Unit Sale Price must be published directly adjacent to the MRP in numerals at least 50% the size of the retail price.
              </p>
            </div>
          </div>
        )}

        {/* Tab 3: Second Schedule MPE Tolerance Checker */}
        {activeTab === 'mpe' && (
          <div className="max-w-4xl mx-auto glass-card rounded-3xl p-6 sm:p-8 border border-white/60 dark:border-white/10 shadow-2xl">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100 dark:border-gray-800">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <Scale size={24} />
              </div>
              <div>
                <h3 className="text-xl font-black text-gray-900 dark:text-white">
                  Second Schedule Maximum Permissible Error (MPE) Auditor
                </h3>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  Verifies whether package net content deficiency falls within statutory tolerances or constitutes a prosecution violation.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Declared Net Quantity on Pack (g / ml):
                </label>
                <input
                  type="number"
                  min="5"
                  max="50000"
                  value={declaredWeight}
                  onChange={(e) => setDeclaredWeight(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-mono font-bold dark:bg-gray-800 dark:text-white"
                />
                <p className="text-[11px] text-gray-400 mt-2">
                  The nominal weight or volume declared on the principal display panel.
                </p>
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-gray-700 dark:text-gray-300 mb-2">
                  Actual Net Content Audited on Scale (g / ml):
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={actualWeight}
                  onChange={(e) => setActualWeight(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-xl text-sm font-mono font-bold dark:bg-gray-800 dark:text-white"
                />
                <p className="text-[11px] text-gray-400 mt-2">
                  Gross weight minus calibrated tare weight of the packaging material.
                </p>
              </div>
            </div>

            {/* Quick Sachet & Pack Test Presets */}
            <div className="flex flex-wrap items-center gap-2 mb-6">
              <span className="text-[11px] font-black uppercase tracking-wider text-gray-500 dark:text-gray-400 mr-1">
                Quick Presets:
              </span>
              <button
                type="button"
                onClick={() => { setDeclaredWeight('6'); setActualWeight('5.5'); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/40 text-gov-blue dark:text-blue-300 hover:bg-blue-100"
              >
                🧴 Shampoo Sachet (6 ml)
              </button>
              <button
                type="button"
                onClick={() => { setDeclaredWeight('10'); setActualWeight('9.2'); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 hover:bg-amber-100"
              >
                🥫 Sauce Sachet (10 g)
              </button>
              <button
                type="button"
                onClick={() => { setDeclaredWeight('25'); setActualWeight('23.5'); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 hover:bg-purple-100"
              >
                ☕ Coffee Sachet (25 g)
              </button>
              <button
                type="button"
                onClick={() => { setDeclaredWeight('500'); setActualWeight('488'); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100"
              >
                🌾 Atta Pack (500 g)
              </button>
              <button
                type="button"
                onClick={() => { setDeclaredWeight('1000'); setActualWeight('985'); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100"
              >
                📦 Standard 1kg Pack
              </button>
            </div>

            <div className={`rounded-3xl p-6 sm:p-8 text-center text-white relative overflow-hidden border shadow-xl bg-gradient-to-br ${
              mpeResult.isCompliant
                ? 'from-emerald-600 via-teal-700 to-slate-950 border-emerald-400/40'
                : 'from-rose-600 via-red-700 to-slate-950 border-rose-400/40'
            }`}>
              <div className="flex items-center justify-center gap-2 mb-2">
                {mpeResult.isCompliant ? (
                  <CheckCircle2 size={24} className="text-emerald-300" />
                ) : (
                  <AlertTriangle size={24} className="text-amber-300" />
                )}
                <span className="text-xs font-mono font-bold uppercase tracking-widest text-white/90">
                  {mpeResult.isCompliant ? 'Complies with Second Schedule Tolerances' : 'Short-Weight Violation Detected'}
                </span>
              </div>

              {/* Statutory Tier Badge */}
              <div className="inline-block my-1 px-3 py-1 rounded-full bg-black/30 border border-white/20 text-[11px] font-mono text-white/95">
                ⚖️ {mpeResult.tierText}
              </div>

              <div className="text-4xl sm:text-5xl font-black my-2 font-mono tracking-tight text-white drop-shadow">
                {mpeResult.isCompliant ? 'PASSED AUDIT' : 'NON-COMPLIANT'}
              </div>

              <p className="text-xs sm:text-sm text-white/90 max-w-xl mx-auto leading-relaxed">
                Maximum Permissible Error (MPE) for {declaredWeight}g/ml is <strong>±{mpeResult.mpeGrams}g/ml {mpeResult.mpePercent ? `(${mpeResult.mpePercent}% ratio-based)` : '(fixed schedule)'}</strong>. The minimum legal acceptable net quantity is <strong>{mpeResult.minPermissible}g/ml</strong>. Actual difference: <strong>{mpeResult.diff}g/ml</strong>.
              </p>

              {!mpeResult.isCompliant && (
                <div className="mt-4 inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-black/40 text-amber-200 text-xs font-bold">
                  <span>Actionable under Section 36(2) of the Legal Metrology Act, 2009</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
