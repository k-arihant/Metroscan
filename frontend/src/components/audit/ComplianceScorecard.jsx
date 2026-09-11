import { useState } from 'react';
import {
  CheckCircle, XCircle, AlertTriangle, ChevronDown, ChevronUp,
  Download, Edit3, RotateCcw
} from 'lucide-react';
import { useLang } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

const STATUS_CONFIG = {
  PASS: { icon: CheckCircle, cls: 'badge-pass', bg: 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-900/30', label: 'PASS' },
  FAIL: { icon: XCircle, cls: 'badge-fail', bg: 'bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30', label: 'FAIL' },
  WARN: { icon: AlertTriangle, cls: 'badge-warn', bg: 'bg-amber-50 dark:bg-amber-900/10 border-amber-100 dark:border-amber-900/30', label: 'WARNING' },
};

function RuleRow({ decl, index }) {
  const [open, setOpen] = useState(false);
  const cfg = STATUS_CONFIG[decl.status] || STATUS_CONFIG.WARN;
  const Icon = cfg.icon;

  return (
    <div className={`rounded-xl border ${cfg.bg} overflow-hidden transition-all duration-200`}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        aria-expanded={open}
      >
        <span className="text-xs font-bold text-gray-400 dark:text-gray-600 w-5 flex-shrink-0">
          {String(index + 1).padStart(2, '0')}
        </span>
        <Icon
          size={18}
          className={`flex-shrink-0 ${
            decl.status === 'PASS' ? 'text-green-500' :
            decl.status === 'FAIL' ? 'text-red-500' : 'text-amber-500'
          }`}
        />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm text-gray-900 dark:text-white truncate">
            {decl.rule_name}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">{decl.statutory_citation}</div>
        </div>
        <span className={cfg.cls}>{cfg.label}</span>
        {open ? <ChevronUp size={14} className="text-gray-400 flex-shrink-0" /> : <ChevronDown size={14} className="text-gray-400 flex-shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-0 animate-fade-in">
          <div className="ml-8 space-y-2">
            {decl.extracted_value && (
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-0.5">Extracted Value</div>
                <div className="text-sm font-mono text-gray-800 dark:text-gray-200 bg-white/60 dark:bg-gray-900/50 rounded px-3 py-2 border border-gray-200 dark:border-gray-700">
                  "{decl.extracted_value}"
                </div>
              </div>
            )}
            {decl.violation_reason && (
              <div>
                <div className="text-xs text-red-500 uppercase tracking-wide font-semibold mb-0.5">Violation</div>
                <div className="text-sm text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 rounded px-3 py-2 border border-red-200 dark:border-red-800">
                  {decl.violation_reason}
                </div>
              </div>
            )}
            {decl.measured_font_height_mm && (
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span className="font-semibold">Font height:</span>
                <span className={`font-mono font-bold ${decl.measured_font_height_mm >= 1 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {decl.measured_font_height_mm} mm
                </span>
                {decl.confidence_score && (
                  <span>· Confidence: <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{(decl.confidence_score * 100).toFixed(1)}%</span></span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ComplianceScorecard({ result, onReset }) {
  const { t } = useLang();
  const { user, token, isConsumer, isInspector } = useAuth();
  const [downloading, setDownloading] = useState(false);

  if (!result) return null;

  const statusColor = result.overall_status === 'COMPLIANT'
    ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
    : result.overall_status === 'NON_COMPLIANT'
    ? 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    : 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';

  const scoreColor = result.compliance_score >= 80 ? 'text-green-500'
    : result.compliance_score >= 50 ? 'text-amber-500' : 'text-red-500';

  const handleDownload = async () => {
    setDownloading(true);
    const url = isConsumer
      ? `/api/v1/scan/${result.scan_id}/report.pdf`
      : (result.pdf_url || `/api/v1/scan/${result.scan_id}/certificate.pdf`);

    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = isConsumer
        ? `MetroScan_${result.scan_id?.slice(0, 8)}_Consumer_Report.pdf`
        : `MetroScan_${result.scan_id?.slice(0, 8)}_Certificate.pdf`;
      a.click();
    } catch (err) {
      alert(`PDF download failed: ${err.message || 'Offline demo'}`);
    }
    setDownloading(false);
  };

  const passCount = result.declarations?.filter(d => d.status === 'PASS').length ?? 0;
  const failCount = result.declarations?.filter(d => d.status === 'FAIL').length ?? 0;
  const warnCount = result.declarations?.filter(d => d.status === 'WARN' || d.status === 'WARNING').length ?? 0;

  return (
    <div className="space-y-5 animate-slide-in-up">
      {/* Overall verdict */}
      <div className={`rounded-2xl border-2 p-5 ${statusColor}`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest opacity-70 mb-1">{t('overallStatus')}</div>
            <div className="text-2xl font-black tracking-tight">
              {result.overall_status === 'COMPLIANT' ? t('compliant') :
               result.overall_status === 'NON_COMPLIANT' ? t('nonCompliant') : t('warning')}
            </div>
            {result.product_name && (
              <div className="text-sm font-semibold opacity-80 mt-1">{result.product_name}</div>
            )}
            {result.brand_name && (
              <div className="text-xs opacity-60">{result.brand_name}</div>
            )}
          </div>
          <div className="text-right">
            <div className={`text-4xl font-black ${scoreColor}`}>{result.compliance_score?.toFixed(0)}%</div>
            <div className="text-xs font-semibold opacity-70 mt-0.5">{t('complianceScore')}</div>
          </div>
        </div>

        {/* Score bar */}
        <div className="mt-3 bg-white/30 dark:bg-black/20 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${
              result.compliance_score >= 80 ? 'bg-green-500' :
              result.compliance_score >= 50 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${result.compliance_score}%` }}
          />
        </div>

        {/* Summary pills */}
        <div className="flex gap-2 mt-3 flex-wrap">
          <span className="badge-pass">{passCount} Pass</span>
          <span className="badge-fail">{failCount} Fail</span>
          {warnCount > 0 && <span className="badge-warn">{warnCount} Warning</span>}
        </div>
      </div>

      {/* Rule-by-rule accordion */}
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">{t('ruleCheck')}</h3>
          <span className="text-xs text-gray-400 font-mono">Rule 6(1)(a)–(i) + 6(3)</span>
        </div>
        {result.declarations?.map((decl, i) => (
          <RuleRow key={decl.rule_code || i} decl={decl} index={i} />
        ))}
      </div>

      {/* Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="btn-gov-primary justify-center py-3"
        >
          <Download size={15} />
          {downloading
            ? 'Generating...'
            : isConsumer
            ? 'Download Consumer Report (PDF)'
            : 'Download Statutory Notice (PDF)'}
        </button>
        <button
          onClick={onReset}
          className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 font-semibold text-sm transition-all"
        >
          <RotateCcw size={15} /> New Scan
        </button>
      </div>
    </div>
  );
}
