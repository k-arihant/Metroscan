import {
  Home,
  Scan,
  Scale,
  Calculator,
  MapPin,
  BarChart3,
  SunMoon,
  ShieldAlert,
} from 'lucide-react';
import { Dock, DockIcon, DockItem, DockLabel } from '@/components/ui/dock';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../context/AuthContext';

export function AppleStyleDock({ onScanClick, onLoginClick }) {
  const { isDark, toggle } = useTheme();
  const { user } = useAuth();
  const isConsumer = user?.role === 'consumer';

  const navTo = (hash) => {
    const el = document.querySelector(hash);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const dockItems = [
    {
      title: 'Home',
      icon: <Home className="h-full w-full text-blue-600 dark:text-blue-400" />,
      action: () => navTo(isConsumer ? '#home' : '#dashboard'),
    },
    {
      title: 'Scan Studio',
      icon: <Scan className="h-full w-full text-amber-500 dark:text-amber-400" />,
      action: () => navTo('#audit-studio'),
    },
    {
      title: '10 Rules',
      icon: <Scale className="h-full w-full text-emerald-600 dark:text-emerald-400" />,
      action: () => navTo('#legal-rules'),
    },
    {
      title: 'Audit Registry',
      icon: <Calculator className="h-full w-full text-purple-600 dark:text-purple-400" />,
      action: () => navTo('#audit-registry'),
    },
    {
      title: 'GIS Heatmap',
      icon: <MapPin className="h-full w-full text-rose-500 dark:text-rose-400" />,
      action: () => navTo('#gis-map'),
    },
    {
      title: 'Analytics',
      icon: <BarChart3 className="h-full w-full text-cyan-600 dark:text-cyan-400" />,
      action: () => navTo('#analytics-trends'),
    },
    {
      title: 'Theme',
      icon: <SunMoon className="h-full w-full text-amber-400 dark:text-amber-300" />,
      action: toggle,
    },
  ];

  const visibleDockItems = dockItems.filter(item => {
    if (isConsumer && (item.title === 'GIS Heatmap' || item.title === 'Analytics')) {
      return false;
    }
    return true;
  });

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 max-w-full pointer-events-auto">
      <Dock className="items-end pb-2 bg-white/75 dark:bg-gray-950/80 backdrop-blur-2xl border border-white/50 dark:border-white/10 shadow-2xl rounded-3xl px-3 py-1">
        {visibleDockItems.map((item, idx) => (
          <DockItem
            key={idx}
            onClick={item.action}
            className="aspect-square rounded-2xl bg-white/60 dark:bg-gray-800/60 hover:bg-white dark:hover:bg-gray-700 shadow-sm transition-colors border border-black/5 dark:border-white/5"
          >
            <DockLabel>{item.title}</DockLabel>
            <DockIcon>{item.icon}</DockIcon>
          </DockItem>
        ))}
      </Dock>
    </div>
  );
}
