import { useState } from 'react';
import { Home, Info, HelpCircle, FileText, BookOpen, Phone, Menu, X, MapPin, Scan, Scale, BarChart3 } from 'lucide-react';
import { useLang } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

export default function NavigationBar({ activeSection = 'home' }) {
  const { t } = useLang();
  const { isInspector } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = isInspector
    ? [
        { key: 'dashboard', label: 'Command Center', icon: BarChart3, href: '#dashboard' },
        { key: 'auditStudio', label: 'Scan Studio', icon: Scan, href: '#audit-studio' },
        { key: 'recentScans', label: 'Audit Registry', icon: FileText, href: '#audit-registry' },
        { key: 'analytics', label: 'Compliance Analytics', icon: BarChart3, href: '#analytics-trends' },
        { key: 'gisMap', label: 'Enforcement GIS', icon: MapPin, href: '#gis-map' },
        { key: 'legalRules', label: '10 Rules Handbook', icon: Scale, href: '#legal-rules' },
      ]
    : [
        { key: 'home', label: t('home') || 'Home', icon: Home, href: '#home' },
        { key: 'auditStudio', label: 'Verify Package', icon: Scan, href: '#audit-studio' },
        { key: 'howItWorks', label: t('howItWorks') || 'How It Works', icon: HelpCircle, href: '#how-it-works' },
        { key: 'legalRules', label: t('legalRules') || 'PCR Rules', icon: Scale, href: '#legal-rules' },
        { key: 'recentScans', label: 'My Scans', icon: FileText, href: '#audit-registry' },
        { key: 'contactUs', label: t('contactUs') || 'Contact Us', icon: Phone, href: '#contact' },
      ];

  const handleNav = (href) => {
    const el = document.querySelector(href);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setMobileOpen(false);
  };

  return (
    <nav className="bg-[#0B2545] dark:bg-[#040813]/95 backdrop-blur-xl border-b border-white/10 transition-colors duration-300 sticky top-[73px] z-30 shadow-md">
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6">
        {/* Desktop nav with spacious breathing room */}
        <div className="hidden md:flex items-center gap-3 sm:gap-5 lg:gap-7 overflow-x-auto py-2">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeSection === item.key;
            return (
              <button
                key={item.key}
                id={`nav-${item.key}`}
                onClick={() => handleNav(item.href)}
                className={`group flex items-center gap-2.5 px-4 py-2 rounded-xl text-sm font-semibold tracking-wide whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? 'bg-white/15 dark:bg-white/10 text-white shadow-sm border border-white/20 dark:border-white/15'
                    : 'text-gray-300 hover:text-white hover:bg-white/10 border border-transparent'
                }`}
              >
                <Icon
                  size={15}
                  className={`transition-colors ${
                    isActive ? 'text-gov-saffron' : 'text-gray-400 group-hover:text-gov-saffron'
                  }`}
                />
                <span>{item.label}</span>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-gov-saffron animate-pulse ml-0.5" />
                )}
              </button>
            );
          })}
        </div>

        {/* Mobile nav toggle */}
        <div className="md:hidden flex items-center justify-between py-2.5">
          <span className="text-white/80 text-xs font-bold uppercase tracking-widest flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gov-saffron" />
            {isInspector ? 'Inspector Enforcement' : 'Legal Metrology Navigation'}
          </span>
          <button
            onClick={() => setMobileOpen(o => !o)}
            className="text-white/90 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-all border border-white/10"
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden bg-gov-dark border-t border-white/10 animate-slide-in-up">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeSection === item.key;
            return (
              <button
                key={item.key}
                onClick={() => handleNav(item.href)}
                className={`w-full flex items-center gap-3 px-6 py-3 text-sm font-medium text-left transition-all
                  ${isActive
                    ? 'bg-white/10 text-white border-l-2 border-gov-saffron'
                    : 'text-gray-300 hover:bg-white/5 hover:text-white border-l-2 border-transparent'
                  }`}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
}
