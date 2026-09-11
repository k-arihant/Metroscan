import { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  Tooltip, Legend, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { useTheme } from '../../context/ThemeContext';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl shadow-xl px-4 py-3 text-sm">
      {label && <div className="font-bold text-gray-700 dark:text-gray-300 mb-1">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-600 dark:text-gray-400">{p.name}:</span>
          <span className="font-bold text-gray-900 dark:text-white">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function AnalyticsCharts() {
  const { isDark } = useTheme();
  const axisColor = isDark ? '#6B7280' : '#9CA3AF';
  const gridColor = isDark ? '#1F2937' : '#F3F4F6';

  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/dashboard/analytics')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        setAnalytics(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load real analytics:', err);
        setAnalytics(null);
        setLoading(false);
      });
  }, []);

  const ruleViolations = analytics?.rule_violations || [];
  const complianceDist = analytics?.overall_compliance || [];
  const monthlyTrend = analytics?.monthly_trend || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      {/* Violation by rule — bar chart */}
      <div className="lg:col-span-2 gov-card p-5">
        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4">
          Violations by Statutory Rule
        </h3>
        {loading ? (
          <div className="h-60 flex items-center justify-center">
            <div className="skeleton h-52 w-full rounded-xl" />
          </div>
        ) : ruleViolations.length === 0 ? (
          <div className="h-60 flex items-center justify-center text-gray-400 text-sm">
            No statutory rule violations recorded in active audits.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={ruleViolations} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="rule" tick={{ fontSize: 11, fill: axisColor }} />
              <YAxis tick={{ fontSize: 11, fill: axisColor }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="violations" name="Violations" fill="#C0392B" radius={[4, 4, 0, 0]} />
              <Bar dataKey="compliant" name="Compliant" fill="#27AE60" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Compliance distribution — pie */}
      <div className="gov-card p-5">
        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4">
          Overall Compliance
        </h3>
        {loading ? (
          <div className="h-40 flex items-center justify-center">
            <div className="skeleton h-32 w-32 rounded-full" />
          </div>
        ) : complianceDist.length === 0 ? (
          <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
            No compliance distribution data available.
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  data={complianceDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {complianceDist.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-col gap-2 mt-2">
              {complianceDist.map(d => (
                <div key={d.name} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                    <span className="text-gray-600 dark:text-gray-400">{d.name}</span>
                  </span>
                  <span className="font-bold text-gray-900 dark:text-white">{d.value}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Monthly trend */}
      <div className="lg:col-span-3 gov-card p-5">
        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-4">
          Monthly Inspection Trend (2026)
        </h3>
        {loading ? (
          <div className="h-44 flex items-center justify-center">
            <div className="skeleton h-36 w-full rounded-xl" />
          </div>
        ) : monthlyTrend.length === 0 ? (
          <div className="h-44 flex items-center justify-center text-gray-400 text-sm">
            No monthly inspection trends recorded.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={monthlyTrend} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: axisColor }} />
              <YAxis tick={{ fontSize: 11, fill: axisColor }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="scans" name="Total Scans" fill="#1A5276" radius={[4, 4, 0, 0]} />
              <Bar dataKey="violations" name="Violations" fill="#F39C12" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
