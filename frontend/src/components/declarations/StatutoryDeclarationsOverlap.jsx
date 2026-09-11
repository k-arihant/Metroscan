import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck,
  Building2,
  Tag,
  Scale,
  Calendar,
  IndianRupee,
  ClockAlert,
  Headphones,
  Globe2,
  Coins,
  Type,
  CheckCircle2,
  AlertOctagon,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';

const STATUTORY_PAIRS = [
  {
    pairId: 'pair-1',
    stageNumber: '01',
    theme: 'Product Identity & Commercial Denomination',
    tag: 'Stage 01 / 05',
    tilt: 'rotate-0',
    rules: [
      {
        id: 'rule-6-1-a',
        number: '01',
        code: 'Rule 6(1)(a)',
        tag: 'Identification',
        title: 'Manufacturer, Packer or Importer Details',
        desc: 'Name and complete registered address of the manufacturer, contract packer, or importer with PIN code.',
        checks: [
          'Full registered postal address with PIN code',
          'Contract packer: "Mfg by X for Y"',
          'Importer name & IEC on imported consignments',
        ],
        example: 'Mfg: Apex Consumer Care Pvt Ltd, Plot 42, Okhla, New Delhi - 110020',
        penalty: 'Sec 36(1): Fine up to ₹25,000 (1st), ₹50,000 (2nd)',
        gradient: 'from-blue-600 via-indigo-700 to-slate-950',
        accent: '#3B82F6',
        border: 'border-blue-400/40',
        icon: Building2,
      },
      {
        id: 'rule-6-1-b',
        number: '02',
        code: 'Rule 6(1)(b)',
        tag: 'Identity & PDP',
        title: 'Generic & Common Commodity Name',
        desc: 'Unambiguous common or generic commercial name of the commodity on the Principal Display Panel (PDP).',
        checks: [
          'Prominent generic trade denomination',
          'No surrogate or misleading brand titles',
          'Standard Second Schedule statutory naming',
        ],
        example: 'Generic: Blended Edible Vegetable Oil (Rice Bran & Sunflower Seed)',
        penalty: 'Sec 36(1): Up to ₹1,00,000 for deceptive naming',
        gradient: 'from-indigo-600 via-purple-700 to-slate-950',
        accent: '#8B5CF6',
        border: 'border-indigo-400/40',
        icon: Tag,
      },
    ],
  },
  {
    pairId: 'pair-2',
    stageNumber: '02',
    theme: 'Metric Weights & Production Timeline',
    tag: 'Stage 02 / 05',
    tilt: '-rotate-1',
    rules: [
      {
        id: 'rule-6-1-c',
        number: '03',
        code: 'Rule 6(1)(c)',
        tag: 'Metric Standards',
        title: 'Net Quantity in SI Metric Units',
        desc: 'Declared in standard units of weight/volume (g, kg, ml, l) or count conforming strictly to metric standards.',
        checks: [
          'Mandatory SI metric units (g, kg, ml, l)',
          'Non-standard "gms", "kgs", "ltrs" strictly illegal',
          'Dual volume/weight at 30°C for liquids',
        ],
        example: 'Net Quantity: 1 kg (Net Volume at 30°C: 1.099 L)',
        penalty: 'Sec 36(2): Non-bailable offense for short-weight',
        gradient: 'from-emerald-600 via-teal-700 to-slate-950',
        accent: '#10B981',
        border: 'border-emerald-400/40',
        icon: Scale,
      },
      {
        id: 'rule-6-1-d',
        number: '04',
        code: 'Rule 6(1)(d)',
        tag: 'Freshness & Batch',
        title: 'Month & Year of Manufacture / Packing',
        desc: 'Indelible declaration of the month and year of manufacture, pre-packing, or import on the primary pack.',
        checks: [
          'Format: MM/YYYY or Month & Year in words',
          'Indelible print — cannot be wiped or overlaid',
          'Must specify mfg, packing, or import',
        ],
        example: 'Mfg Date: 08/2026 | Batch Code: LOT-IN-98442',
        penalty: 'Sec 36(1): Confiscation of unverified back-dated stock',
        gradient: 'from-amber-500 via-orange-600 to-slate-950',
        accent: '#F59E0B',
        border: 'border-amber-400/40',
        icon: Calendar,
      },
    ],
  },
  {
    pairId: 'pair-3',
    stageNumber: '03',
    theme: 'Pricing Transparency & Perishable Safety',
    tag: 'Stage 03 / 05',
    tilt: 'rotate-1',
    rules: [
      {
        id: 'rule-6-1-e',
        number: '05',
        code: 'Rule 6(1)(e)',
        tag: 'Consumer Price',
        title: 'MRP (Inclusive of All Taxes)',
        desc: 'Maximum Retail Price with mandatory statutory statement "inclusive of all taxes". Dual pricing is illegal.',
        checks: [
          'Exact words "inclusive of all taxes"',
          'Mandatory Rupee symbol (₹)',
          'Dual-pricing stickers strictly prohibited',
        ],
        example: 'MRP ₹ 245.00 (INCL. OF ALL TAXES)',
        penalty: 'Sec 36(1): ₹20,000 for 1st offense, criminal seizure for repeat',
        gradient: 'from-rose-600 via-red-700 to-slate-950',
        accent: '#F43F5E',
        border: 'border-rose-400/40',
        icon: IndianRupee,
      },
      {
        id: 'rule-6-1-f',
        number: '06',
        code: 'Rule 6(1)(f)',
        tag: 'Health & Perishables',
        title: 'Best Before / Expiry Date',
        desc: 'Mandatory declaration of expiry date or best before period for perishable and consumer consumable goods.',
        checks: [
          'Unambiguous "Best Before [X] Months from Packing"',
          'Or explicit "Expiry Date: DD/MM/YYYY"',
          'Harmonized with FSSAI regulations',
        ],
        example: 'Best Before: 12 Months from Packaging | Use By: 08/2027',
        penalty: 'Immediate confiscation and destruction of expired goods',
        gradient: 'from-orange-600 via-amber-700 to-slate-950',
        accent: '#EA580C',
        border: 'border-orange-400/40',
        icon: ClockAlert,
      },
    ],
  },
  {
    pairId: 'pair-4',
    stageNumber: '04',
    theme: 'Consumer Redressal & Trade Origins',
    tag: 'Stage 04 / 05',
    tilt: '-rotate-1',
    rules: [
      {
        id: 'rule-6-1-g',
        number: '07',
        code: 'Rule 6(1)(g)',
        tag: 'Consumer Redressal',
        title: 'Consumer Care Cell Details',
        desc: 'Name, address, working telephone number, and official email of the designated consumer grievance officer.',
        checks: [
          'Designated Grievance Officer title',
          'Working toll-free helpline number',
          'Official registered grievance email',
        ],
        example: 'Care: Exec-Grievances, Tel: 1800-11-4000, care@brand.in',
        penalty: 'Sec 36(1): Fine up to ₹25,000 for missing contact points',
        gradient: 'from-cyan-600 via-teal-700 to-slate-950',
        accent: '#06B6D4',
        border: 'border-cyan-400/40',
        icon: Headphones,
      },
      {
        id: 'rule-6-1-h',
        number: '08',
        code: 'Rule 6(1)(h)',
        tag: 'Customs & Origin',
        title: 'Country of Origin (For Imports)',
        desc: 'Packages containing imported goods must prominently declare the country of origin on physical and digital PDPs.',
        checks: [
          'Country of manufacture or origin',
          'Mandatory for all e-commerce product listings',
          'Customs IEC registration linkage',
        ],
        example: 'Country of Origin: India (Made in India) | IEC: 0511048821',
        penalty: 'Non-compliance triggers immediate import seizure at customs ports',
        gradient: 'from-purple-600 via-violet-700 to-slate-950',
        accent: '#A855F7',
        border: 'border-purple-400/40',
        icon: Globe2,
      },
    ],
  },
  {
    pairId: 'pair-5',
    stageNumber: '05',
    theme: 'Price Comparison & Legibility Heights',
    tag: 'Stage 05 / 05',
    tilt: 'rotate-0',
    rules: [
      {
        id: 'rule-6-1-i',
        number: '09',
        code: 'Rule 6(1)(i)',
        tag: 'Price Comparison',
        title: 'Unit Sale Price (USP)',
        desc: 'Mandatory price per gram, per kilogram, per millilitre, or per litre adjacent to MRP for comparison transparency.',
        checks: [
          'Per 1g / 100g / 1kg for solids',
          'Per 1ml / 100ml / 1L for liquids',
          'Font height at least 50% of MRP numerals',
        ],
        example: 'Unit Sale Price: ₹ 24.50 / 100g (Beside MRP)',
        penalty: 'Sec 36(1): Misleading packaging citation without USP',
        gradient: 'from-pink-600 via-rose-700 to-slate-950',
        accent: '#EC4899',
        border: 'border-pink-400/40',
        icon: Coins,
      },
      {
        id: 'rule-6-3',
        number: '10',
        code: 'Rule 6(3)',
        tag: 'Legibility Standard',
        title: 'Minimum Font & Numeral Height',
        desc: 'All declarations must meet strict minimum millimeter heights graduated according to package net content.',
        checks: [
          '≤ 50g/ml: Min 1.0 mm font height',
          '50g-200g: Min 2.0 mm font height',
          '> 200g-1kg: Min 4.0 mm font height',
          '> 1kg: Min 6.0 mm font height',
        ],
        example: 'Audit: Height = 4.2mm (Meets >200g statutory standard)',
        penalty: 'Sec 36(1): Illegible font treated as total absence of declaration',
        gradient: 'from-slate-800 via-blue-900 to-slate-950',
        accent: '#38BDF8',
        border: 'border-sky-400/40',
        icon: Type,
      },
    ],
  },
];

export default function StatutoryDeclarationsOverlap() {
  const [activeStageId, setActiveStageId] = useState('pair-1');

  const scrollToStage = (id) => {
    setActiveStageId(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <section
      id="about"
      className="py-24 bg-gradient-to-b from-slate-100 via-slate-50 to-slate-100 dark:from-[#050811] dark:via-[#080d1a] dark:to-[#050811] relative border-t border-b border-gray-200/70 dark:border-white/5"
    >
      {/* Background ambient lighting isolated with overflow-hidden */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-10 w-96 h-96 bg-blue-500/10 dark:bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-10 w-96 h-96 bg-amber-500/10 dark:bg-amber-600/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-screen-xl mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          
          {/* ── LEFT PINNED STICKY HEADER (lg:col-span-4) ── */}
          <div className="lg:col-span-4 lg:sticky lg:top-24 space-y-6">
            <div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-black uppercase tracking-widest border border-emerald-500/20">
                <ShieldCheck size={14} className="text-emerald-500" />
                Legal Metrology Act, 2009
              </span>
              <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white mt-4 tracking-tight leading-tight">
                10 Mandatory Declarations
              </h2>
              <p className="text-gray-600 dark:text-gray-300 text-xs sm:text-sm mt-3 leading-relaxed">
                Organized into 5 paired statutory themes. As you scroll, each pair stacks smoothly onto the deck for fast, high-density compliance verification.
              </p>
            </div>

            {/* Quick 5-Stage Thematic Navigator */}
            <div className="glass-card rounded-2xl p-4 border border-white/60 dark:border-white/10 space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-gray-700 dark:text-gray-300">
                <span className="flex items-center gap-1.5">
                  <Sparkles size={13} className="text-gov-saffron" />
                  Statutory Theme Navigator
                </span>
                <span className="text-[11px] font-mono text-gray-400">5 Stages</span>
              </div>

              <div className="space-y-1.5">
                {STATUTORY_PAIRS.map((pair) => (
                  <button
                    key={pair.pairId}
                    onClick={() => scrollToStage(pair.pairId)}
                    className={`w-full text-left text-xs font-semibold px-3 py-2 rounded-xl transition-all duration-200 flex items-center justify-between ${
                      activeStageId === pair.pairId
                        ? 'bg-gov-blue text-white shadow-md font-bold'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="font-mono text-[11px] opacity-80">{pair.stageNumber}</span>
                      <span className="truncate">{pair.theme}</span>
                    </div>
                    <ArrowRight size={12} className="shrink-0 opacity-70" />
                  </button>
                ))}
              </div>
            </div>

            {/* Zero Tolerance Callout */}
            <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-2.5 text-xs text-amber-800 dark:text-amber-200">
              <AlertOctagon size={16} className="text-amber-500 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Zero-Tolerance Mandate:</span> Under Section 36(1), omission of any statutory declaration attracts immediate compoundable or non-bailable fines.
              </div>
            </div>
          </div>

          {/* ── RIGHT STACKING 2-CARD DECK CONTAINER (lg:col-span-8) ── */}
          <div className="lg:col-span-8 relative pb-20">
            {STATUTORY_PAIRS.map((pair, pairIndex) => (
              <div
                key={pair.pairId}
                id={pair.pairId}
                className={`sticky mb-24 sm:mb-28 last:mb-0 transition-all duration-300 ${pair.tilt}`}
                style={{
                  top: `calc(5.5rem + ${pairIndex * 18}px)`,
                  zIndex: pairIndex + 1,
                }}
                onMouseEnter={() => setActiveStageId(pair.pairId)}
              >
                {/* Stage Header Banner */}
                <div className="flex items-center justify-between px-4 py-2 mb-2 rounded-xl bg-slate-900/90 dark:bg-black/90 backdrop-blur-md text-white border border-white/10 shadow-lg">
                  <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider">
                    <Layers size={13} className="text-gov-saffron" />
                    <span>{pair.tag}</span>
                    <span className="text-white/40">·</span>
                    <span className="text-white/90 normal-case font-bold">{pair.theme}</span>
                  </div>
                  <span className="text-[10px] font-mono text-white/60">2 Declarations</span>
                </div>

                {/* 2-Card Horizontal Pair Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {pair.rules.map((rule) => {
                    const Icon = rule.icon;
                    return (
                      <motion.div
                        key={rule.id}
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, margin: '-30px' }}
                        transition={{ duration: 0.3 }}
                        className={`rounded-3xl p-5 sm:p-6 text-white shadow-[0_-8px_25px_rgba(0,0,0,0.35)] bg-gradient-to-br ${rule.gradient} border ${rule.border} backdrop-blur-xl relative overflow-hidden group flex flex-col justify-between hover:scale-[1.02] transition-transform`}
                      >
                        {/* Ambient glow in corner */}
                        <div
                          className="absolute -top-12 -right-12 w-36 h-36 rounded-full blur-2xl pointer-events-none opacity-40 group-hover:opacity-70 transition-opacity"
                          style={{ backgroundColor: rule.accent }}
                        />

                        {/* Top: Code & Tag */}
                        <div>
                          <div className="flex items-center justify-between gap-2 relative z-10">
                            <span className="font-mono text-xs font-black px-2.5 py-1 rounded-md bg-white/20 backdrop-blur-md border border-white/20 text-white shadow-sm">
                              {rule.code}
                            </span>
                            <span className="text-[10px] font-bold uppercase tracking-wider text-white/80 px-2 py-0.5 rounded bg-black/30">
                              {rule.tag}
                            </span>
                          </div>

                          {/* Icon & Title */}
                          <div className="mt-4 flex items-start gap-3 relative z-10">
                            <div
                              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-md border border-white/20 backdrop-blur-md"
                              style={{ backgroundColor: `${rule.accent}33` }}
                            >
                              <Icon size={20} className="text-white" />
                            </div>
                            <div>
                              <h3 className="text-base sm:text-lg font-black tracking-tight leading-snug">
                                {rule.title}
                              </h3>
                              <p className="text-xs text-white/85 mt-1 leading-relaxed line-clamp-2">
                                {rule.desc}
                              </p>
                            </div>
                          </div>

                          {/* Checklist */}
                          <div className="mt-4 pt-3 border-t border-white/15 relative z-10 space-y-1.5">
                            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-white/70 block">
                              Key Standards
                            </span>
                            {rule.checks.map((check, i) => (
                              <div key={i} className="flex items-start gap-1.5 text-[11px] text-white/90 leading-snug">
                                <CheckCircle2 size={12} className="text-emerald-400 shrink-0 mt-0.5" />
                                <span>{check}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Bottom: Example & Penalty */}
                        <div className="mt-4 space-y-2 relative z-10">
                          <div className="p-2.5 rounded-xl bg-black/35 backdrop-blur-md border border-white/10 text-[11px] text-white/90 font-mono">
                            <span className="text-gov-saffron font-bold mr-1">EX:</span>
                            <span className="text-white/80">{rule.example}</span>
                          </div>

                          <div className="pt-2 border-t border-white/10 text-[10px] text-amber-300 font-semibold flex items-center gap-1.5">
                            <AlertOctagon size={12} className="shrink-0" />
                            <span className="truncate">{rule.penalty}</span>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
