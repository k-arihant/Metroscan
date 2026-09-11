import { useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, X, ImagePlus, Camera } from 'lucide-react';

const PANEL_LABELS = [
  { key: 'front', label: 'Front Panel (PDP)', hint: 'Brand, Product Name, Net Qty', color: 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' },
  { key: 'back', label: 'Info / Packer Panel', hint: 'Manufacturer, Packer, Address, Care', color: 'border-purple-400 bg-purple-50 dark:bg-purple-900/20' },
  { key: 'mrp', label: 'MRP & Date Panel', hint: 'MRP, Batch, Mfg Date, Expiry', color: 'border-amber-400 bg-amber-50 dark:bg-amber-900/20' },
  { key: 'side_1', label: 'Side Panel 1', hint: 'Ingredients, Nutrition, Directions', color: 'border-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'side_2', label: 'Side Panel 2', hint: 'FSSAI, Certifications, Warnings', color: 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20' },
  { key: 'reference', label: 'Reference / Base', hint: 'EAN Barcode for scale calibration', color: 'border-rose-400 bg-rose-50 dark:bg-rose-900/20' },
];

const SLOT_KEYS = ['front', 'back', 'mrp', 'side_1', 'side_2', 'reference'];

function ImageSlot({ slot, file, onSelect, onRemove }) {
  const inputRef = useRef(null);

  const handleClick = () => {
    if (!file && inputRef.current) {
      inputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      onSelect(slot.key, f);
    }
    e.target.value = '';
  };

  return (
    <div
      onClick={handleClick}
      className={`relative rounded-xl border-2 border-dashed ${slot.color} p-3 flex flex-col items-center justify-center min-h-[120px] transition-all group ${
        file ? '' : 'cursor-pointer hover:scale-[1.02] hover:shadow-md'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/jpg"
        onChange={handleFileChange}
        className="hidden"
      />
      {file ? (
        <>
          <img
            src={file instanceof Blob ? URL.createObjectURL(file) : ''}
            alt={slot.label}
            className="w-full h-24 object-cover rounded-lg shadow-sm"
          />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(slot.key);
            }}
            className="absolute top-2 right-2 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-xs hover:bg-red-600 transition-colors shadow"
            aria-label="Remove"
          >
            <X size={12} />
          </button>
          <div className="mt-1.5 text-xs font-semibold text-center text-gray-700 dark:text-gray-300 truncate max-w-full">
            {slot.label}
          </div>
        </>
      ) : (
        <>
          <div className="w-8 h-8 rounded-full bg-black/5 dark:bg-white/5 flex items-center justify-center mb-1.5 group-hover:scale-110 transition-transform">
            <Camera size={16} className="text-gray-500 dark:text-gray-400" />
          </div>
          <div className="text-xs font-bold text-gray-700 dark:text-gray-200 text-center leading-tight">
            {slot.label}
          </div>
          <div className="text-[10px] text-gray-400 dark:text-gray-500 text-center mt-0.5 leading-tight">
            {slot.hint}
          </div>
          <div className="mt-1.5 text-[9px] font-bold text-gov-blue dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Click to upload
          </div>
        </>
      )}
    </div>
  );
}

export default function PackageDropzone({ files, onFilesChange }) {
  const handleSelectSlot = (key, file) => {
    onFilesChange(prev => ({ ...prev, [key]: file }));
  };
  const onDrop = useCallback((acceptedFiles) => {
    onFilesChange(prev => {
      const newFiles = { ...prev };
      let si = 0;
      for (const f of acceptedFiles) {
        while (si < SLOT_KEYS.length && newFiles[SLOT_KEYS[si]]) si++;
        if (si < SLOT_KEYS.length) {
          newFiles[SLOT_KEYS[si]] = f;
          si++;
        }
      }
      return newFiles;
    });
  }, [onFilesChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.heic'] },
    multiple: true,
    maxFiles: 6,
  });

  const removeFile = (key) => onFilesChange(prev => ({ ...prev, [key]: null }));

  const hasAnyFile = Object.values(files).some(Boolean);
  const fileCount = Object.values(files).filter(Boolean).length;

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? 'border-gov-blue bg-blue-50 dark:bg-blue-900/20 scale-[1.01]'
            : 'border-gray-200 dark:border-gray-700 hover:border-gov-blue/60 hover:bg-blue-50/50 dark:hover:bg-blue-900/10'
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud
          size={36}
          className={`mx-auto mb-3 transition-colors ${isDragActive ? 'text-gov-blue' : 'text-gray-300 dark:text-gray-600'}`}
        />
        {isDragActive ? (
          <p className="text-gov-blue font-bold text-sm">Drop your package photos here!</p>
        ) : (
          <>
            <p className="text-gray-600 dark:text-gray-400 font-semibold text-sm mb-1">
              Drag & drop package photos, or <span className="text-gov-blue underline">browse files</span>
            </p>
            <p className="text-gray-400 text-xs">
              Supports JPG, PNG, WEBP · Up to 6 panel photos recommended
            </p>
          </>
        )}

        {hasAnyFile && (
          <div className="absolute top-3 right-3 bg-gov-blue text-white text-xs font-bold px-2 py-0.5 rounded-full shadow-sm">
            {fileCount} / 6
          </div>
        )}
      </div>

      {/* 6 Panel Slots */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {PANEL_LABELS.map(slot => (
          <ImageSlot
            key={slot.key}
            slot={slot}
            file={files[slot.key]}
            onSelect={handleSelectSlot}
            onRemove={removeFile}
          />
        ))}
      </div>
    </div>
  );
}
