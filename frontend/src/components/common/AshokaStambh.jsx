/**
 * Official State Emblem of India (Ashoka Stambha / Lion Capital of Sarnath)
 * Features the four Asiatic Lions, Ashoka Chakra, flanking Horse and Bull,
 * Lotus base, and "सत्यमेव जयते" motto in Devanagari script.
 */
export default function AshokaStambh({ className = 'w-12 h-16', variant = 'gold' }) {
  const isGold = variant === 'gold';

  return (
    <svg
      viewBox="0 0 200 250"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      role="img"
      aria-label="State Emblem of India — Ashoka Stambha"
    >
      <defs>
        {/* Rich Regal Gold Gradients */}
        <linearGradient id="stambhGold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F9E79F" />
          <stop offset="35%" stopColor="#F39C12" />
          <stop offset="70%" stopColor="#D4AC0D" />
          <stop offset="100%" stopColor="#996515" />
        </linearGradient>

        <linearGradient id="stambhDarkGold" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#D4AC0D" />
          <stop offset="100%" stopColor="#7D5700" />
        </linearGradient>

        <linearGradient id="chakraBlue" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1B4F72" />
          <stop offset="100%" stopColor="#0B2545" />
        </linearGradient>

        <filter id="stambhShadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#000000" floodOpacity="0.25" />
        </filter>
      </defs>

      <g filter="url(#stambhShadow)">
        {/* ─── 1. CENTRAL LION (FACING FRONT) ─── */}
        {/* Ears */}
        <path d="M 86 38 C 84 28, 92 24, 94 32 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />
        <path d="M 114 38 C 116 28, 108 24, 106 32 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />

        {/* Mane / Crown of Central Lion */}
        <path
          d="M 94 30 C 88 20, 112 20, 106 30 C 118 28, 122 40, 118 48 C 122 55, 116 66, 112 70 C 110 80, 90 80, 88 70 C 84 66, 78 55, 82 48 C 78 40, 82 28, 94 30 Z"
          fill="url(#stambhGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />

        {/* Mane Curls / Tuft Texture */}
        <path d="M 88 38 Q 94 44 92 50" stroke="#7D5700" strokeWidth="1.2" fill="none" />
        <path d="M 112 38 Q 106 44 108 50" stroke="#7D5700" strokeWidth="1.2" fill="none" />
        <path d="M 95 34 Q 100 40 100 46" stroke="#7D5700" strokeWidth="1.2" fill="none" />
        <path d="M 105 34 Q 100 40 100 46" stroke="#7D5700" strokeWidth="1.2" fill="none" />
        <path d="M 86 52 Q 92 56 94 62" stroke="#7D5700" strokeWidth="1.2" fill="none" />
        <path d="M 114 52 Q 108 56 106 62" stroke="#7D5700" strokeWidth="1.2" fill="none" />

        {/* Central Lion Face */}
        <path
          d="M 92 40 C 92 36, 108 36, 108 40 C 110 46, 108 54, 105 58 C 103 62, 97 62, 95 58 C 92 54, 90 46, 92 40 Z"
          fill="url(#stambhGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />
        {/* Eyes & Brows */}
        <ellipse cx="96" cy="44" rx="2" ry="1.4" fill="#3D2700" />
        <ellipse cx="104" cy="44" rx="2" ry="1.4" fill="#3D2700" />
        <path d="M 94 41 Q 96 42 98 42" stroke="#5D3A00" strokeWidth="1" fill="none" />
        <path d="M 106 41 Q 104 42 102 42" stroke="#5D3A00" strokeWidth="1" fill="none" />
        {/* Nose & Muzzle */}
        <polygon points="100,47 98,49 102,49" fill="#5D3A00" />
        <path d="M 100 49 L 100 52 M 97 53 Q 100 54 103 53" stroke="#5D3A00" strokeWidth="1" fill="none" />
        {/* Roaring Open Mouth & Fangs */}
        <path d="M 97 54 C 98 57, 102 57, 103 54 Z" fill="#4A1505" stroke="#7D5700" strokeWidth="0.8" />
        <polygon points="98,54 98.5,56 99,54" fill="#FFF" />
        <polygon points="101,54 101.5,56 102,54" fill="#FFF" />

        {/* Central Lion Chest & Paws */}
        <path
          d="M 90 68 C 90 82, 88 105, 88 116 L 96 116 L 98 90 L 102 90 L 104 116 L 112 116 C 112 105, 110 82, 110 68 Z"
          fill="url(#stambhGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />
        {/* Chest Fur Details */}
        <path d="M 94 72 Q 100 78 100 86" stroke="#7D5700" strokeWidth="1" fill="none" />
        <path d="M 106 72 Q 100 78 100 86" stroke="#7D5700" strokeWidth="1" fill="none" />
        <path d="M 96 82 Q 100 88 100 94" stroke="#7D5700" strokeWidth="1" fill="none" />
        <path d="M 104 82 Q 100 88 100 94" stroke="#7D5700" strokeWidth="1" fill="none" />
        {/* Paws */}
        <path d="M 87 112 C 87 110, 97 110, 97 116 L 87 116 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />
        <path d="M 103 112 C 103 110, 113 110, 113 116 L 103 116 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />

        {/* ─── 2. LEFT LION (PROFILE LOOKING LEFT) ─── */}
        <path
          d="M 76 36 C 68 34, 62 42, 60 50 C 58 56, 62 64, 66 66 C 62 72, 64 84, 72 88 C 76 96, 78 110, 78 116 L 86 116 C 86 100, 84 75, 84 62 C 84 50, 82 42, 76 36 Z"
          fill="url(#stambhGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />
        {/* Left Lion Snout & Ear */}
        <path d="M 68 40 C 62 38, 56 42, 54 46 C 54 50, 60 54, 64 54 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />
        <ellipse cx="60" cy="45" rx="1.5" ry="1.2" fill="#3D2700" />
        <path d="M 55 49 L 58 50" stroke="#7D5700" strokeWidth="0.8" />
        <path d="M 72 34 C 70 28, 76 26, 76 32 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />
        {/* Mane details */}
        <path d="M 66 54 Q 72 58 74 66" stroke="#7D5700" strokeWidth="1" fill="none" />
        <path d="M 62 62 Q 68 66 70 74" stroke="#7D5700" strokeWidth="1" fill="none" />

        {/* ─── 3. RIGHT LION (PROFILE LOOKING RIGHT) ─── */}
        <path
          d="M 124 36 C 132 34, 138 42, 140 50 C 142 56, 138 64, 134 66 C 138 72, 136 84, 128 88 C 124 96, 122 110, 122 116 L 114 116 C 114 100, 116 75, 116 62 C 116 50, 118 42, 124 36 Z"
          fill="url(#stambhGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />
        {/* Right Lion Snout & Ear */}
        <path d="M 132 40 C 138 38, 144 42, 146 46 C 146 50, 140 54, 136 54 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />
        <ellipse cx="140" cy="45" rx="1.5" ry="1.2" fill="#3D2700" />
        <path d="M 145 49 L 142 50" stroke="#7D5700" strokeWidth="0.8" />
        <path d="M 128 34 C 130 28, 124 26, 124 32 Z" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1" />
        {/* Mane details */}
        <path d="M 134 54 Q 128 58 126 66" stroke="#7D5700" strokeWidth="1" fill="none" />
        <path d="M 138 62 Q 132 66 130 74" stroke="#7D5700" strokeWidth="1" fill="none" />

        {/* ─── 4. ABACUS / FRIEZE BASE ─── */}
        {/* Top Rim of Abacus */}
        <rect x="42" y="116" width="116" height="6" rx="2" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />

        {/* Main Abacus Band */}
        <rect x="46" y="122" width="108" height="28" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />

        {/* Bottom Rim of Abacus */}
        <rect x="40" y="150" width="120" height="6" rx="2" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />

        {/* ─── 5. CENTRAL ASHOKA CHAKRA ON ABACUS ─── */}
        <g transform="translate(100, 136)">
          <circle cx="0" cy="0" r="11" fill="#FFFDF8" stroke="#0B2545" strokeWidth="1.5" />
          <circle cx="0" cy="0" r="2.5" fill="#0B2545" />
          {/* 24 Spokes */}
          {Array.from({ length: 24 }, (_, i) => {
            const angle = (i * 15 * Math.PI) / 180;
            const x = 10 * Math.cos(angle);
            const y = 10 * Math.sin(angle);
            return <line key={i} x1="0" y1="0" x2={x} y2={y} stroke="#0B2545" strokeWidth="0.75" />;
          })}
        </g>

        {/* ─── 6. GALLOPING HORSE (LEFT OF CHAKRA) ─── */}
        <g transform="translate(68, 136) scale(0.65)">
          {/* Stylized high-relief horse */}
          <path
            d="M -18 8 C -14 0, -8 -4, 0 -3 C 6 -2, 10 -8, 12 -12 C 14 -10, 14 -4, 11 0 C 8 4, 6 10, 4 14 L 0 14 C 2 10, 0 6, -4 6 C -8 6, -12 12, -16 14 Z"
            fill="#5D3A00"
          />
          <circle cx="11" cy="-8" r="1.5" fill="#F9E79F" />
        </g>

        {/* ─── 7. ZEBU BULL (RIGHT OF CHAKRA) ─── */}
        <g transform="translate(132, 136) scale(0.65)">
          {/* Stylized high-relief bull with hump */}
          <path
            d="M 18 8 C 14 0, 8 -4, 0 -3 C -4 -2, -6 -6, -8 -9 C -10 -11, -14 -6, -11 -2 C -8 4, -6 10, -4 14 L 0 14 C -2 10, 0 6, 4 6 C 8 6, 12 12, 16 14 Z"
            fill="#5D3A00"
          />
          {/* Bull Hump */}
          <ellipse cx="-2" cy="-4" rx="4" ry="3" fill="#5D3A00" />
        </g>

        {/* ─── 8. INVERTED LOTUS BASE ─── */}
        <path
          d="M 55 156 C 65 170, 135 170, 145 156 C 148 162, 144 172, 138 178 C 122 188, 78 188, 62 178 C 56 172, 52 162, 55 156 Z"
          fill="url(#stambhDarkGold)"
          stroke="#7D5700"
          strokeWidth="1.2"
        />
        {/* Lotus Petals */}
        <path d="M 68 158 Q 74 174 80 182" stroke="#F9E79F" strokeWidth="1" fill="none" />
        <path d="M 85 158 Q 90 176 94 184" stroke="#F9E79F" strokeWidth="1" fill="none" />
        <path d="M 100 158 L 100 185" stroke="#F9E79F" strokeWidth="1.2" fill="none" />
        <path d="M 115 158 Q 110 176 106 184" stroke="#F9E79F" strokeWidth="1" fill="none" />
        <path d="M 132 158 Q 126 174 120 182" stroke="#F9E79F" strokeWidth="1" fill="none" />

        {/* ─── 9. BANNER BASE WITH "सत्यमेव जयते" MOTTO ─── */}
        <rect x="36" y="194" width="128" height="24" rx="4" fill="url(#stambhGold)" stroke="#7D5700" strokeWidth="1.2" />

        {/* Devanagari text "सत्यमेव जयते" */}
        <text
          x="100"
          y="211"
          textAnchor="middle"
          fontSize="14.5"
          fontWeight="900"
          fill="#3D2700"
          fontFamily="'Outfit', 'Noto Sans Devanagari', 'Mangal', 'Segoe UI', serif"
          letterSpacing="1.2"
        >
          सत्यमेव जयते
        </text>

        {/* Motto underline bar */}
        <line x1="48" y1="214" x2="152" y2="214" stroke="#7D5700" strokeWidth="1" opacity="0.6" />
      </g>
    </svg>
  );
}
