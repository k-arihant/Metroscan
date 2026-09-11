import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Activity, AlertOctagon, FileCheck, Clock } from 'lucide-react';
import { useLang } from '../../context/LanguageContext';

export default function KpiStatGrid() {
  const { t } = useLang();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/dashboard/stats')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (data && typeof data === 'object' && !data.detail) {
          setStats(data);
        } else {
          throw new Error('Invalid stats format');
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch KPI stats:', err);
        setStats(null);
        setLoading(false);
      });
  }, []);

  const cards = [
    { key: 'total_scans', label: t('totalScans'), value: stats?.total_scans, icon: FileCheck, color: 'text-gov-blue', bg: 'bg-blue-50 dark:bg-blue-900/20', trend: '+12%', trendUp: true },
    { key: 'today_scans', label: "Today's Scans", value: stats?.today_scans, icon: Activity, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/20', trend: '+8%', trendUp: true },
    { key: 'violations_detected', label: t('violations'), value: stats?.violations_detected, icon: AlertOctagon, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20', trend: '-3%', trendUp: false },
    { key: 'compliance_rate', label: t('complianceRate'), value: stats?.compliance_rate != null ? `${stats.compliance_rate.toFixed(1)}%` : null, icon: TrendingUp, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20', trend: '+2.1%', trendUp: true },
    { key: 'pending_notices', label: t('pendingNotices'), value: stats?.pending_notices, icon: Clock, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20', trend: '-1', trendUp: false },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      {cards.map(card => {
        const Icon = card.icon;
        return (
          <div key={card.key} className="glass-card card-3d rounded-2xl p-5 border border-white/60 dark:border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-sm ${card.bg}`}>
                <Icon size={20} className={card.color} />
              </div>
              <span className={`text-xs font-bold flex items-center gap-0.5 px-2 py-0.5 rounded-full ${
                card.trendUp ? 'text-green-700 bg-green-50 dark:bg-green-950/40 dark:text-green-400' : 'text-red-700 bg-red-50 dark:bg-red-950/40 dark:text-red-400'
              }`}>
                {card.trendUp ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {card.trend}
              </span>
            </div>
            {loading ? (
              <div className="skeleton h-8 w-16 mb-1" />
            ) : (
              <div className={`text-2xl font-black ${card.color}`}>{card.value ?? '—'}</div>
            )}
            <div className="text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5 leading-tight">{card.label}</div>
          </div>
        );
      })}
    </div>
  );
}
