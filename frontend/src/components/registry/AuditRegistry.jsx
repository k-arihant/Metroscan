import { useState, useEffect } from 'react';
import { Search, Filter, Download, ExternalLink, ChevronDown } from 'lucide-react';
import { useLang } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

const STATUS_STYLES = {
  COMPLIANT: 'badge-pass',
  NON_COMPLIANT: 'badge-fail',
  WARNING: 'badge-warn',
};

export default function AuditRegistry() {
  const { t } = useLang();
  const { user, token, getAuthHeaders } = useAuth();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortField, setSortField] = useState('created_at');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 7;

  useEffect(() => {
    setPage(1);
    const params = new URLSearchParams();
    if (search) params.set('q', search);
    if (statusFilter && statusFilter !== 'ALL') params.set('status', statusFilter);
    params.set('limit', '8');
    if (user?.id) params.set('user_id', user.id);

    const headers = getAuthHeaders ? getAuthHeaders() : {};
    fetch(`/api/v1/dashboard/recent-scans?${params}`, { headers })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          setScans(data);
        } else {
          setScans([]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load recent scans from backend:', err);
        setScans([]);
        setLoading(false);
      });
  }, [search, statusFilter, getAuthHeaders, user?.id]);

  const exportCsv = () => {
    const rows = [
      ['Scan ID', 'Product', 'Brand', 'Status', 'Score %', 'Store', 'Date'],
      ...scans.map(s => [
        s.scan_id, s.product_name, s.brand_name, s.overall_status,
        s.compliance_score, s.store_name,
        new Date(s.created_at).toLocaleDateString('en-IN'),
      ]),
    ];
    const csv = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `MetroScan_AuditRegistry_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-1 max-w-sm">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              placeholder="Search products, brands..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="gov-input pl-9 py-2 text-sm"
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="gov-input py-2 text-sm w-40"
          >
            <option value="ALL">All Status</option>
            <option value="COMPLIANT">Compliant</option>
            <option value="NON_COMPLIANT">Non-Compliant</option>
            <option value="WARNING">Warning</option>
          </select>
        </div>
        <button onClick={exportCsv} className="btn-gov-outline py-2 px-4 text-sm flex-shrink-0">
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="gov-card overflow-hidden">
        <div className="table-responsive">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
                {['Scan ID', 'Product', 'Brand', 'Status', 'Score', 'Store', 'Date', ''].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-900">
              {loading ? (
                Array.from({ length: 5 }, (_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 8 }, (_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="skeleton h-4 w-full max-w-[80px]" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : scans.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-gray-400">
                    No scans found matching your criteria.
                  </td>
                </tr>
              ) : (
                scans.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map(scan => (
                  <tr key={scan.scan_id} className="hover:bg-gray-50/50 dark:hover:bg-gray-900/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
                        #{scan.scan_id?.slice(0, 8)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-gray-900 dark:text-white max-w-[180px] truncate">
                        {scan.product_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 max-w-[120px] truncate">
                      {scan.brand_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className={STATUS_STYLES[scan.overall_status] || 'badge-warn'}>
                        {scan.overall_status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`font-bold font-mono text-sm ${
                        scan.compliance_score >= 80 ? 'text-green-600 dark:text-green-400' :
                        scan.compliance_score >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {scan.compliance_score?.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 max-w-[140px] truncate text-xs">
                      {scan.store_name}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {new Date(scan.created_at).toLocaleDateString('en-IN')}
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={user?.role === 'consumer' ? `/api/v1/scan/${scan.scan_id}/report.pdf` : `/api/v1/scan/${scan.scan_id}/certificate.pdf${token ? `?token=${encodeURIComponent(token)}` : ''}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gov-blue hover:text-gov-dark dark:text-blue-400 transition-colors inline-flex items-center"
                        title={user?.role === 'consumer' ? 'View Consumer Compliance Report' : 'View Statutory Certificate'}
                      >
                        <ExternalLink size={14} />
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 text-xs text-gray-400 flex items-center justify-between flex-wrap gap-2">
          <span>
            {scans.length === 0 ? '0 records' : `Showing ${Math.min((page - 1) * PAGE_SIZE + 1, scans.length)} to ${Math.min(page * PAGE_SIZE, scans.length)} of ${scans.length} records`}
          </span>
          {scans.length > PAGE_SIZE && (
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="px-2.5 py-1 rounded border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                Previous
              </button>
              <span className="font-semibold text-gray-700 dark:text-gray-300">
                Page {page} of {Math.ceil(scans.length / PAGE_SIZE)}
              </span>
              <button
                disabled={page >= Math.ceil(scans.length / PAGE_SIZE)}
                onClick={() => setPage(p => p + 1)}
                className="px-2.5 py-1 rounded border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
