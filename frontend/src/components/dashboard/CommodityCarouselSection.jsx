import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Layers,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  TrendingUp,
  ArrowUpRight,
  Droplets,
  Cookie,
  Heart,
  Flame,
  Milk,
  ShoppingBag,
  Waves,
  Sparkle,
  Building2,
} from 'lucide-react';

const COMMODITY_SECTORS = [
  {
    id: 'c1',
    title: 'Edible Oils & Vanaspati',
    value: '84.2%',
    audits: '1,420 Packages Audited',
    subtitle: 'Rule 6(1)(c) Volume vs Net Qty',
    color: 'from-amber-600 via-amber-700 to-amber-900',
    accent: '#F59E0B',
    badge: 'Standard Size Mandate',
    icon: Droplets,
    description:
      'Edible oils must declare net quantity in volume (litres) and weight (kg) at 30°C. Non-standard pack sizes strictly prohibited under Second Schedule.',
    violations: '89 Notices Issued (Net quantity temperature variance)',
  },
  {
    id: 'c2',
    title: 'Packaged Biscuits & Bakery',
    value: '91.8%',
    audits: '2,940 Packages Audited',
    subtitle: 'Rule 6(1)(e) MRP & Taxes',
    color: 'from-blue-600 via-indigo-700 to-slate-900',
    accent: '#3B82F6',
    badge: 'High Compliance',
    icon: Cookie,
    description:
      'High compliance across major FMCG brands. Primary minor infraction is omission of the mandatory statement "inclusive of all taxes" on promotional stickers.',
    violations: '24 Warnings (Promotional pricing font legibility)',
  },
  {
    id: 'c3',
    title: 'Cosmetics & Personal Care',
    value: '62.4%',
    audits: '840 Packages Audited',
    subtitle: 'Rule 6(3) Font Height Alerts',
    color: 'from-rose-600 via-pink-700 to-rose-950',
    accent: '#F43F5E',
    badge: 'High Scrutiny Alert',
    icon: Heart,
    description:
      'Widespread font height violations on small tubes and compact bottles. Mandates minimum 1.5mm to 2mm print height regardless of surface curve.',
    violations: '316 Notices Issued (Font height below Rule 6(3) minimums)',
  },
  {
    id: 'c4',
    title: 'Packaged Spices & Condiments',
    value: '78.5%',
    audits: '1,860 Packages Audited',
    subtitle: 'Rule 6(1)(i) Unit Sale Price (USP)',
    color: 'from-emerald-600 via-teal-700 to-emerald-950',
    accent: '#10B981',
    badge: 'USP Enforcement Zone',
    icon: Flame,
    description:
      'Mandatory Unit Sale Price per 100g or per 1g must be displayed adjacent to MRP. Common violation: omission of USP on spice pouch packaging.',
    violations: '142 Notices Issued (Missing Unit Sale Price declaration)',
  },
  {
    id: 'c5',
    title: 'Dairy & Infant Nutrition',
    value: '96.1%',
    audits: '1,120 Packages Audited',
    subtitle: 'Rule 6(1)(f) Expiry & Storage',
    color: 'from-purple-600 via-violet-700 to-purple-950',
    accent: '#8B5CF6',
    badge: 'Zero Tolerance Sector',
    icon: Milk,
    description:
      'Highest compliance sector nationwide. Stringent dual scrutiny under Legal Metrology and FSSAI for infant formula and pasteurized milk pouches.',
    violations: '11 Minor Notices (Customer care telephone formatting)',
  },
  {
    id: 'c6',
    title: 'E-Commerce Imports',
    value: '58.9%',
    audits: '650 Packages Audited',
    subtitle: 'Rule 6(1)(h) Origin Declaration',
    color: 'from-slate-700 via-slate-800 to-black',
    accent: '#64748B',
    badge: 'Customs & Port Scrutiny',
    icon: ShoppingBag,
    description:
      'Imported pre-packaged goods sold online must display the country of origin, importer name, and address on digital product listings and physical packs.',
    violations: '267 Violations Logged (Non-declaration of country of origin)',
  },
  {
    id: 'c7',
    title: 'Packaged Drinking Water',
    value: '88.3%',
    audits: '950 Packages Audited',
    subtitle: 'Rule 6(1)(c) Standard Capacities',
    color: 'from-cyan-600 via-sky-700 to-blue-950',
    accent: '#06B6D4',
    badge: 'ISI / BIS Linked',
    icon: Waves,
    description:
      'Water bottles must strictly comply with standard nominal capacities (250ml, 500ml, 1L, 2L, 5L, 20L). Non-standard volume packages are prohibited.',
    violations: '48 Seizures (Non-standard pack sizes and dual MRP stickers)',
  },
  {
    id: 'c8',
    title: 'Detergents & Cleaners',
    value: '81.4%',
    audits: '790 Packages Audited',
    subtitle: 'Rule 18 Net Weight Standards',
    color: 'from-indigo-600 via-blue-800 to-indigo-950',
    accent: '#6366F1',
    badge: 'Weight Verification',
    icon: Sparkle,
    description:
      'High-volume detergent powders checked for net content moisture loss tolerances. Net quantity must hold at standard distribution humidity.',
    violations: '62 Notices (Weight deficit exceeding maximum permissible error)',
  },
  {
    id: 'c9',
    title: 'Cement & Building Pre-packs',
    value: '93.5%',
    audits: '530 Packages Audited',
    subtitle: 'Rule 2(l) Bulk Pack Standards',
    color: 'from-stone-700 via-zinc-800 to-stone-950',
    accent: '#78716C',
    badge: 'Heavy Industry Audit',
    icon: Building2,
    description:
      'Standard 50kg bags audited at plant gates and retail hubs. Verified for tare weight deduction and tamper-evident stitched sealing.',
    violations: '18 Weight Discrepancies (Bags found with <49.5kg gross weight)',
  },
];

export default function CommodityCarouselSection() {
  const [activeId, setActiveId] = useState('c1');

  const activeSector =
    COMMODITY_SECTORS.find((s) => s.id === activeId) || COMMODITY_SECTORS[0];
  const otherSectors = COMMODITY_SECTORS.filter((s) => s.id !== activeId);

  const ActiveIcon = activeSector.icon;

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 lg:p-10 border border-white/60 dark:border-white/10 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-100 dark:border-gray-800 pb-5">
        <div>
          <span className="text-xs font-black uppercase tracking-widest text-gov-blue dark:text-blue-400 flex items-center gap-2">
            <Layers size={15} className="text-gov-saffron" />
            Statutory Sector Analytics (Full View)
          </span>
          <h3 className="text-2xl sm:text-3xl font-black text-gray-900 dark:text-white mt-1 tracking-tight">
            Sector-Wise Compliance Breakdown
          </h3>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-2xl">
            Click any sector card to feature its live compliance metrics, statutory audit count, and enforcement notice statistics.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800/80 px-3.5 py-1.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          9 Regulated Commodities Active
        </div>
      </div>

      {/* Main Wide Layout: Left Square Featured Card + Right Multi-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* ── LEFT FEATURED SQUARE HERO CARD (lg:col-span-5) ── */}
        <div className="lg:col-span-5 flex flex-col">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSector.id}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className={`relative flex-1 flex flex-col justify-between rounded-3xl p-6 sm:p-8 text-white shadow-2xl bg-gradient-to-br ${activeSector.color} border border-white/20 min-h-[380px] overflow-hidden`}
            >
              {/* Background ambient glow */}
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full blur-2xl pointer-events-none -mr-12 -mt-12" />

              {/* Top Row: Icon + Badge */}
              <div className="relative z-10 flex items-start justify-between gap-3">
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center shadow-lg">
                  <ActiveIcon size={34} className="text-white" />
                </div>
                <span className="flex items-center gap-1.5 text-xs font-black uppercase tracking-wider px-3 py-1.5 rounded-full bg-white/20 backdrop-blur-md border border-white/30">
                  <ShieldCheck size={14} className="text-emerald-300" />
                  {activeSector.badge}
                </span>
              </div>

              {/* Middle: Title, Subtitle, Description */}
              <div className="relative z-10 my-6">
                <span className="text-xs font-mono font-bold uppercase tracking-wider opacity-80">
                  {activeSector.subtitle}
                </span>
                <h4 className="text-2xl sm:text-3xl font-black leading-tight mt-1 tracking-tight">
                  {activeSector.title}
                </h4>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed mt-3">
                  {activeSector.description}
                </p>

                {/* Violations notice callout */}
                <div className="mt-4 p-3 rounded-xl bg-black/25 backdrop-blur-md border border-white/15 flex items-start gap-2.5 text-xs text-amber-200">
                  <AlertTriangle size={15} className="shrink-0 mt-0.5 text-amber-300" />
                  <span>{activeSector.violations}</span>
                </div>
              </div>

              {/* Bottom: Stat highlight */}
              <div className="relative z-10 pt-4 border-t border-white/20 flex items-end justify-between">
                <div>
                  <div className="text-3xl sm:text-4xl font-black font-mono tracking-tight">
                    {activeSector.value}
                  </div>
                  <div className="text-xs text-white/70 font-semibold mt-0.5">
                    {activeSector.audits}
                  </div>
                </div>

                <div className="text-xs font-black px-3 py-1.5 rounded-full bg-white text-gray-900 shadow flex items-center gap-1">
                  Active Focus <ArrowUpRight size={14} />
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* ── RIGHT MULTI-CARD GRID OF ALL OTHER SECTORS (lg:col-span-7) ── */}
        <div className="lg:col-span-7 flex flex-col justify-between">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 h-full">
            {otherSectors.map((sector) => {
              const Icon = sector.icon;
              return (
                <motion.div
                  key={sector.id}
                  whileHover={{ scale: 1.04, translateY: -3 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveId(sector.id)}
                  className={`group relative flex flex-col justify-between rounded-2xl p-4 text-white shadow-lg cursor-pointer bg-gradient-to-br ${sector.color} border border-white/20 hover:border-white/60 hover:shadow-2xl transition-all min-h-[165px]`}
                >
                  {/* Top Bar: Icon Orb + Compliance Score */}
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-md border border-white/25 flex items-center justify-center shadow">
                      <Icon size={20} className="text-white" />
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-black font-mono tracking-tight text-white drop-shadow">
                        {sector.value}
                      </div>
                      <div className="text-[9px] uppercase tracking-wider text-white/70 font-bold">
                        Compliance
                      </div>
                    </div>
                  </div>

                  {/* Middle Content: Title & Full Subtitle / Provision */}
                  <div className="my-2">
                    <h5 className="text-xs sm:text-sm font-black leading-snug line-clamp-2 drop-shadow-sm">
                      {sector.title}
                    </h5>
                    <div className="text-[10px] text-white/80 font-medium line-clamp-1 mt-1">
                      {sector.subtitle}
                    </div>
                  </div>

                  {/* Bottom Bar: Audited count & Focus hint */}
                  <div className="pt-2 border-t border-white/20 flex items-center justify-between text-[10px] text-white/80 font-mono">
                    <span className="truncate">{sector.audits.split(' ')[0]} Pkgs</span>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-white/70 group-hover:text-white group-hover:underline flex items-center gap-0.5">
                      Focus <ArrowUpRight size={10} />
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
