import { useState } from 'react';
import { Moon, Sun, Globe, ChevronDown, LogOut, User, Shield, Menu, X } from 'lucide-react';
import AshokaStambh from '../common/AshokaStambh';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useLang } from '../../context/LanguageContext';
import { InteractiveHoverButton } from '@/components/ui/interactive-hover-button';

/* Language Dropdown */
function LanguageDropdown() {
  const { lang, changeLang, languages } = useLang();
  const [open, setOpen] = useState(false);
  const current = languages.find(l => l.code === lang);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm font-semibold transition-all shadow-sm"
        aria-label="Change language"
      >
        <Globe size={14} className="text-gov-blue dark:text-blue-400" />
        <span className="inline">{current?.native || 'English'}</span>
        <ChevronDown size={12} className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl shadow-xl z-50 overflow-hidden min-w-[140px] animate-slide-in-up">
          {languages.map(l => (
            <button
              key={l.code}
              onClick={() => { changeLang(l.code); setOpen(false); }}
              className={`w-full text-left px-4 py-2.5 text-sm font-medium transition-colors ${
                lang === l.code
                  ? 'bg-gov-blue text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <span className="font-semibold">{l.native}</span>
              <span className="text-xs ml-2 opacity-60">{l.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SovereignHeader({ onLoginClick }) {
  const { user, logout, isAuthenticated, isInspector, isConsumer, setLoginMode } = useAuth();
  const { isDark, toggle } = useTheme();
  const { t } = useLang();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 dark:bg-[#070c18]/95 backdrop-blur-xl border-b border-gray-200/80 dark:border-white/10 shadow-sm transition-colors duration-300">
      {/* Top Sovereign Tricolor Accent Line */}
      <div className="h-1 w-full bg-gradient-to-r from-[#FF9933] via-white to-[#138808] opacity-90" />

      {/* Top Sovereign Band */}
      <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-2.5">
        <div className="flex items-center justify-between gap-4">

          {/* Left: Ashoka Stambha (logo.webp) + Dept Name */}
          <div className="flex items-center gap-3.5 min-w-0">
            <img
              src="/logo.webp"
              alt="State Emblem of India - Ashoka Stambha"
              className="w-11 h-14 sm:w-12 sm:h-16 object-contain flex-shrink-0 invert mix-blend-multiply dark:invert-0 dark:mix-blend-screen drop-shadow-sm transition-all"
            />
            <div className="min-w-0">
              <div className="font-extrabold text-gray-900 dark:text-white text-sm sm:text-base leading-tight tracking-tight">
                {t('deptName')}
              </div>
              <div className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 font-medium leading-tight mt-0.5 line-clamp-2">
                {t('ministry')}
              </div>
            </div>
          </div>

          {/* Center: App Title */}
          <div className="hidden md:block text-center flex-shrink-0">
            <div className="text-xl font-black text-gov-blue dark:text-amber-400 leading-tight tracking-tight">
              {t('appTitle')}
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">
              {t('appSubtitle')}
            </div>
          </div>

          {/* Right: Controls */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Language */}
            <LanguageDropdown />

            {/* Theme toggle */}
            <button
              onClick={toggle}
              className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all"
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {/* Auth */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(o => !o)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gov-blue/10 dark:bg-blue-900/20 border border-gov-blue/20 hover:border-gov-blue/40 text-gov-blue dark:text-blue-300 text-sm font-semibold transition-all"
                >
                  {isInspector ? <Shield size={15} /> : <User size={15} />}
                  <span className="hidden sm:inline max-w-[120px] truncate">{user?.full_name?.split(' ')[0]}</span>
                  <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full ${
                    isInspector
                      ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-400/40'
                      : 'bg-blue-500/20 text-blue-700 dark:text-blue-300 border border-blue-400/40'
                  }`}>
                    {isInspector ? 'Inspector' : 'Citizen'}
                  </span>
                  <ChevronDown size={12} />
                </button>
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-1 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl shadow-xl z-50 min-w-[220px] overflow-hidden animate-slide-in-up">
                    <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                      <div className="flex items-center justify-between gap-2">
                        <div className="font-bold text-sm text-gray-900 dark:text-white truncate">{user?.full_name}</div>
                        <span className={`text-[8px] font-black uppercase px-1.5 py-0.5 rounded ${
                          isInspector ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                        }`}>
                          {user?.role || 'Citizen'}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</div>
                      {user?.badge_id && (
                        <div className="text-xs text-gov-saffron font-mono mt-0.5">Badge: {user.badge_id}</div>
                      )}
                    </div>
                    {isConsumer ? (
                      <button
                        onClick={() => {
                          logout();
                          setLoginMode?.('inspector');
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2.5 text-xs text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 font-bold border-b border-gray-100 dark:border-gray-800 transition-colors"
                      >
                        <Shield size={14} /> Switch to Inspector Login
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          logout();
                          setLoginMode?.('consumer');
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2.5 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 font-bold border-b border-gray-100 dark:border-gray-800 transition-colors"
                      >
                        <User size={14} /> Switch to Citizen Mode
                      </button>
                    )}
                    <button
                      onClick={() => { logout(); setUserMenuOpen(false); }}
                      className="w-full flex items-center gap-2 px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors font-medium"
                    >
                      <LogOut size={14} /> {t('logout')}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  id="btn-header-login"
                  onClick={onLoginClick}
                  className="btn-gov-outline hidden sm:flex py-2 px-4 text-xs rounded-full"
                >
                  <User size={13} /> {t('login')}
                </button>
                <InteractiveHoverButton
                  id="btn-header-get-started"
                  onClick={onLoginClick}
                  className="py-2 px-4 text-xs min-w-[110px]"
                >
                  {t('getStarted')}
                </InteractiveHoverButton>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile: App Title */}
      <div className="md:hidden border-t border-gray-50 dark:border-gray-900 px-4 py-1.5 bg-gray-50 dark:bg-gray-950">
        <div className="flex items-center justify-between">
          <span className="text-sm font-black text-gov-blue dark:text-blue-300">{t('appTitle')}</span>
          <span className="text-[10px] text-gray-400">{t('appSubtitle')}</span>
        </div>
      </div>
    </header>
  );
}
