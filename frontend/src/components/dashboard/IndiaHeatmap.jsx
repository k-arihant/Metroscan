import { useEffect, useState, useRef, useMemo } from 'react';
import { MapPin, Info, ShieldCheck, Filter, Compass } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useLang } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

const STATUS_COLORS = {
  COMPLIANT: '#27AE60',
  NON_COMPLIANT: '#C0392B',
  WARNING: '#F1C40F',
};

export default function IndiaHeatmap() {
  const { t } = useLang();
  const { isInspector, getAuthHeaders } = useAuth();
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapReady, setMapReady] = useState(false);
  const [pins, setPins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    let active = true;
    setLoading(true);
    const headers = getAuthHeaders ? getAuthHeaders() : {};
    fetch('/api/v1/dashboard/heatmap', { headers })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (active && Array.isArray(data)) {
          setPins(data);
        } else if (active) {
          setPins([]);
        }
        if (active) setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load real GIS heatmap pins:', err);
        if (active) {
          setPins([]);
          setLoading(false);
        }
      });
    return () => { active = false; };
  }, [getAuthHeaders]);

  const counts = useMemo(() => {
    return {
      ALL: pins.length,
      COMPLIANT: pins.filter(p => p.overall_status === 'COMPLIANT').length,
      NON_COMPLIANT: pins.filter(p => p.overall_status === 'NON_COMPLIANT').length,
      WARNING: pins.filter(p => p.overall_status === 'WARNING').length,
    };
  }, [pins]);

  const filteredPins = useMemo(() => {
    if (statusFilter === 'ALL') return pins;
    return pins.filter(p => p.overall_status === statusFilter);
  }, [pins, statusFilter]);

  useEffect(() => {
    if (!mapRef.current) return;

    const container = mapRef.current;
    if (container._leaflet_id) {
      delete container._leaflet_id;
    }

    let map = null;
    try {
      map = L.map(container, {
        center: [22.5, 80],
        zoom: 4.8,
        zoomControl: true,
        scrollWheelZoom: false,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
      setMapReady(true);

      setTimeout(() => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.invalidateSize();
        }
      }, 250);
    } catch (err) {
      console.warn('Leaflet initialization notice:', err);
    }

    const handleResize = () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Leaflet removal notice:', e);
        }
        mapInstanceRef.current = null;
      }
      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    const layerGroup = L.layerGroup().addTo(map);
    const validCoords = [];

    filteredPins.forEach(pin => {
      if (pin.latitude == null || pin.longitude == null) return;
      const lat = Number(pin.latitude);
      const lng = Number(pin.longitude);
      if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return;

      validCoords.push([lat, lng]);

      const color = STATUS_COLORS[pin.overall_status] || '#999';
      const marker = L.circleMarker([lat, lng], {
        radius: 9,
        fillColor: color,
        color: '#ffffff',
        weight: 2.5,
        opacity: 1,
        fillOpacity: 0.9,
      });

      // Interactive hover effects
      marker.on('mouseover', function () {
        this.setRadius(12);
        this.setStyle({ weight: 3.5 });
      });
      marker.on('mouseout', function () {
        this.setRadius(9);
        this.setStyle({ weight: 2.5 });
      });

      // Interactive smooth zoom on click
      marker.on('click', () => {
        map.flyTo([lat, lng], Math.max(map.getZoom(), 9), { duration: 0.8 });
      });

      // Tooltip on hover
      marker.bindTooltip(
        `<strong>${pin.product_name || 'Packaged Item'}</strong><br/>${pin.store_name || 'Enforcement Site'}`,
        { direction: 'top', offset: [0, -8] }
      );

      const dateStr = pin.created_at ? new Date(pin.created_at).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      }) : '';

      const popupContent = `
        <div style="font-family: Outfit, sans-serif; min-width: 220px; padding: 6px;">
          <div style="font-weight: 800; font-size: 13px; color: #1e293b; margin-bottom: 2px;">
            ${pin.product_name || 'Packaged Commodity'}
          </div>
          <div style="font-size: 11px; color: #475569; margin-bottom: 2px;">
            📍 ${pin.store_name || 'Inspection Site'}
          </div>
          <div style="font-size: 10px; font-family: monospace; color: #64748b; margin-bottom: 6px;">
            Audit ID: #${(pin.scan_id || '').slice(0, 8)} ${dateStr ? `· ${dateStr}` : ''}
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: #94a3b8; font-family: monospace; margin-bottom: 8px;">
            <span>GPS: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E</span>
            <button onclick="navigator.clipboard && navigator.clipboard.writeText('${lat.toFixed(4)}, ${lng.toFixed(4)}'); this.innerText='✓ Copied'; setTimeout(() => this.innerText='📋 Copy', 1200);" style="cursor: pointer; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 1px 5px; font-size: 9px; color: #334155; font-weight: 700;">📋 Copy</button>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 6px;">
            <span style="display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px; background: ${color}20; color: ${color}; border: 1px solid ${color}50;">
              ${(pin.overall_status || 'UNKNOWN').replace('_', ' ')}
            </span>
            <span style="font-size: 10px; color: #0284c7; font-weight: 700;">Legal Metrology GIS</span>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      layerGroup.addLayer(marker);
    });

    // Auto fit bounds if points exist
    if (validCoords.length > 0) {
      try {
        const bounds = L.latLngBounds(validCoords);
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
      } catch (e) {
        console.warn('Bounds notice:', e);
      }
    }

    return () => {
      try {
        layerGroup.clearLayers();
        layerGroup.remove();
      } catch (e) {
        console.warn('Layer removal notice:', e);
      }
    };
  }, [filteredPins, mapReady]);

  return (
    <div className="glass-card rounded-2xl p-5 border border-white/60 dark:border-white/10 space-y-4 shadow-lg">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2.5">
          <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <MapPin size={18} className="text-gov-blue dark:text-blue-400" />
            {t('heatmapTitle')}
          </h3>
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 border bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700">
            <ShieldCheck size={12} />
            Legal Metrology Enforcement GIS ({filteredPins.length} Active Pins)
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 text-xs font-semibold">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1 rounded-full border transition-all ${
              statusFilter === 'ALL'
                ? 'bg-gov-blue text-white border-gov-blue shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            All ({counts.ALL})
          </button>
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full border transition-all ${
                statusFilter === status
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-transparent shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              <span>{status.replace('_', ' ')} ({counts[status]})</span>
            </button>
          ))}
          <button
            onClick={() => {
              if (mapInstanceRef.current) {
                mapInstanceRef.current.setView([22.5, 80], 4.8);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all font-semibold shadow-xs"
            title="Reset to All-India Overview"
          >
            <Compass size={13} className="text-gov-blue dark:text-blue-400" />
            <span>Reset View</span>
          </button>
        </div>
      </div>

      <div className="relative">
        <div
          ref={mapRef}
          className="w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800 shadow-inner"
          style={{ height: 440 }}
          aria-label="India inspection heatmap"
        />

        {/* Empty state overlay */}
        {!loading && filteredPins.length === 0 && (
          <div className="absolute inset-0 bg-white/85 dark:bg-gray-950/85 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center p-6 text-center z-[500]">
            <MapPin size={36} className="text-gray-400 mb-2 animate-bounce" />
            <p className="font-bold text-gray-800 dark:text-gray-200 text-sm">No inspection records found for this filter</p>
            <p className="text-xs text-gray-500 max-w-sm mt-1">
              Select "All" or run new inspections with location tracking enabled in the Package Audit Studio to record GPS audit data.
            </p>
            <button
              onClick={() => setStatusFilter('ALL')}
              className="mt-3 px-3 py-1.5 text-xs font-semibold bg-gov-blue text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500 text-center flex items-center justify-center gap-1.5">
        <Info size={13} />
        Click any geographic pin to inspect GPS enforcement details · OpenStreetMap GIS Integration
      </p>
    </div>
  );
}
