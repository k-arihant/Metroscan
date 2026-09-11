import { useState, useRef, useEffect, useCallback } from 'react';
import { Eye, EyeOff, User, ShieldCheck, ChevronRight, Loader2, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLang } from '../../context/LanguageContext';

/* ─── Animated MetroScan Mascot ─── */
function MascotSVG({ mode, eyeX, eyeY, eyesCovered, peeking, celebrating, role }) {
  // mode: 'idle' | 'typing' | 'password' | 'success'
  const isInspector = role === 'inspector';

  // Eye positions based on cursor/typing tracking
  const pupilX = 3 + eyeX * 4;
  const pupilY = 3 + eyeY * 4;

  return (
    <svg
      viewBox="0 0 120 140"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-full drop-shadow-xl"
      style={{ filter: 'drop-shadow(0 8px 24px rgba(26,82,118,0.25))' }}
    >
      {/* Shadow */}
      <ellipse cx="60" cy="135" rx="28" ry="5" fill="rgba(0,0,0,0.1)" />

      {/* Inspector cap (shown when role=inspector) */}
      {isInspector && (
        <g>
          {/* Cap body */}
          <rect x="22" y="30" width="76" height="24" rx="4" fill="#152744" />
          {/* Cap brim */}
          <rect x="14" y="50" width="92" height="6" rx="3" fill="#0B3C5D" />
          {/* Gold band */}
          <rect x="22" y="48" width="76" height="4" fill="#F39C12" />
          {/* Ashoka star badge */}
          <circle cx="60" cy="42" r="8" fill="#F39C12" />
          <text x="60" y="46" textAnchor="middle" fontSize="9" fill="#0B3C5D" fontWeight="bold">✪</text>
        </g>
      )}

      {/* Body / face */}
      <circle
        cx="60"
        cy={isInspector ? "88" : "82"}
        r="40"
        fill={isInspector ? "#1A5276" : "#EBF5FB"}
        stroke={isInspector ? "#0B3C5D" : "#AED6F1"}
        strokeWidth="2"
      />

      {/* Inner face circle */}
      <circle
        cx="60"
        cy={isInspector ? "88" : "82"}
        r="30"
        fill={isInspector ? "#2980B9" : "#F4F9FD"}
      />

      {/* Collar / uniform detail for inspector */}
      {isInspector && (
        <g>
          <polygon points="45,120 60,110 75,120 70,130 50,130" fill="#F39C12" />
          <polygon points="60,110 55,122 65,122" fill="#F1C40F" />
        </g>
      )}

      {/* EYES */}
      {eyesCovered ? (
        /* Covered hands */
        <g>
          {/* Left hand */}
          <ellipse cx="43" cy={isInspector ? "88" : "82"} rx="16" ry="18" fill="#F0C27F" stroke="#E5A95C" strokeWidth="1.5" />
          <line x1="33" y1={isInspector ? "74" : "68"} x2="33" y2={isInspector ? "102" : "96"} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="38" y1={isInspector ? "72" : "66"} x2="38" y2={isInspector ? "104" : "98"} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="43" y1={isInspector ? "71" : "65"} x2="43" y2={isInspector ? "105" : "99"} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />
          {/* Right hand */}
          {!peeking ? (
            <ellipse cx="77" cy={isInspector ? "88" : "82"} rx="16" ry="18" fill="#F0C27F" stroke="#E5A95C" strokeWidth="1.5" />
          ) : (
            /* Peeking — right hand slightly lowered */
            <ellipse cx="77" cy={isInspector ? "96" : "90"} rx="16" ry="12" fill="#F0C27F" stroke="#E5A95C" strokeWidth="1.5" />
          )}
          {/* Lines on right hand */}
          <line x1="67" y1={isInspector ? "74" : "68"} x2="67" y2={isInspector ? (peeking ? "90" : "102") : (peeking ? "84" : "96")} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="72" y1={isInspector ? "72" : "66"} x2="72" y2={isInspector ? (peeking ? "88" : "104") : (peeking ? "82" : "98")} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="77" y1={isInspector ? "71" : "65"} x2="77" y2={isInspector ? (peeking ? "87" : "105") : (peeking ? "81" : "99")} stroke="#E5A95C" strokeWidth="1.5" strokeLinecap="round" />

          {/* One peeking eye visible through gap */}
          {peeking && (
            <g>
              <circle cx="60" cy={isInspector ? "80" : "74"} r="6" fill="white" />
              <circle cx={60 + pupilX * 0.3} cy={(isInspector ? 80 : 74) + pupilY * 0.3} r="3" fill="#1A5276" />
              <circle cx={60 + pupilX * 0.3 + 1} cy={(isInspector ? 80 : 74) + pupilY * 0.3 - 1} r="0.8" fill="white" />
            </g>
          )}
        </g>
      ) : (
        /* Normal expressive cute eyes with real-time cursor tracking */
        <g>
          {/* Left eye */}
          <ellipse cx="44" cy={isInspector ? "83" : "77"} rx="10" ry="12" fill="white" stroke="#cbd5e1" strokeWidth="0.8" />
          <g transform={`translate(${pupilX * 0.8}, ${pupilY * 0.8})`}>
            <circle cx="44" cy={isInspector ? "83" : "77"} r="7" fill="#0f172a" />
            <circle cx="44" cy={isInspector ? "83" : "77"} r="5.5" fill="#1e3a8a" />
            <circle cx="42" cy={(isInspector ? 83 : 77) - 2.5} r="2.5" fill="white" />
            <circle cx="46" cy={(isInspector ? 83 : 77) + 2} r="1" fill="white" />
          </g>

          {/* Right eye */}
          <ellipse cx="76" cy={isInspector ? "83" : "77"} rx="10" ry="12" fill="white" stroke="#cbd5e1" strokeWidth="0.8" />
          <g transform={`translate(${pupilX * 0.8}, ${pupilY * 0.8})`}>
            <circle cx="76" cy={isInspector ? "83" : "77"} r="7" fill="#0f172a" />
            <circle cx="76" cy={isInspector ? "83" : "77"} r="5.5" fill="#1e3a8a" />
            <circle cx="74" cy={(isInspector ? 83 : 77) - 2.5} r="2.5" fill="white" />
            <circle cx="78" cy={(isInspector ? 83 : 77) + 2} r="1" fill="white" />
          </g>
        </g>
      )}

      {/* Nose */}
      <circle cx="60" cy={isInspector ? "94" : "88"} r="2" fill={isInspector ? "#AED6F1" : "#AED6F1"} />

      {/* Mouth — changes per state */}
      {celebrating ? (
        /* Big smile */
        <path
          d={`M 46 ${isInspector ? 102 : 96} Q 60 ${isInspector ? 115 : 109} 74 ${isInspector ? 102 : 96}`}
          stroke={isInspector ? "#F39C12" : "#1A5276"}
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
        />
      ) : mode === 'typing' ? (
        /* Concentration mouth — slightly open */
        <path
          d={`M 50 ${isInspector ? 102 : 96} Q 60 ${isInspector ? 106 : 100} 70 ${isInspector ? 102 : 96}`}
          stroke="#1A5276"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      ) : (
        /* Neutral slight smile */
        <path
          d={`M 50 ${isInspector ? 102 : 96} Q 60 ${isInspector ? 109 : 103} 70 ${isInspector ? 102 : 96}`}
          stroke={isInspector ? "#F39C12" : "#1A5276"}
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      )}

      {/* Blush cheeks */}
      {!eyesCovered && !celebrating && (
        <>
          <ellipse cx="34" cy={isInspector ? "94" : "88"} rx="6" ry="4" fill="rgba(255,150,150,0.25)" />
          <ellipse cx="86" cy={isInspector ? "94" : "88"} rx="6" ry="4" fill="rgba(255,150,150,0.25)" />
        </>
      )}

      {/* Celebrating stars */}
      {celebrating && (
        <g>
          <text x="10" y="30" fontSize="14" className="animate-bounce-in">⭐</text>
          <text x="90" y="25" fontSize="12" className="animate-bounce-in">✨</text>
          <text x="100" y="55" fontSize="10" className="animate-bounce-in">🎉</text>
          <text x="5" y="60" fontSize="10" className="animate-bounce-in">🎊</text>
        </g>
      )}
    </svg>
  );
}

/* ─── Confetti ─── */
function Confetti() {
  const pieces = Array.from({ length: 18 }, (_, i) => ({
    id: i,
    color: ['#F39C12', '#1A5276', '#27AE60', '#C0392B', '#F1C40F'][i % 5],
    left: `${5 + i * 5.5}%`,
    delay: `${(i * 0.12).toFixed(2)}s`,
    duration: `${1.2 + (i % 4) * 0.3}s`,
    size: 6 + (i % 3) * 3,
  }));

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
      {pieces.map(p => (
        <div
          key={p.id}
          style={{
            position: 'absolute',
            top: '-20px',
            left: p.left,
            width: p.size,
            height: p.size,
            background: p.color,
            borderRadius: i % 2 === 0 ? '50%' : '2px',
            animation: `confetti-piece ${p.duration} ${p.delay} ease-in forwards`,
          }}
        />
      ))}
    </div>
  );
}

/* ─── Main Login Page ─── */
export default function AnimatedLoginPage({ onClose, fullScreenMode = false }) {
  const { login, demoLogin, register, loginMode, setLoginMode, loading, signInWithGoogle } = useAuth();
  const { t } = useLang();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [activeField, setActiveField] = useState('none'); // 'email'|'password'|'none'
  const [eyePos, setEyePos] = useState({ x: 0, y: 0 });
  const [celebrating, setCelebrating] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('login'); // 'login'|'register'
  const [registerData, setRegisterData] = useState({
    full_name: '', email: '', password: '', badge_id: '', department: '', designation: '',
  });

  const containerRef = useRef(null);
  const emailRef = useRef(null);

  // Track mouse position for eye movement
  const handleMouseMove = useCallback((e) => {
    if (!containerRef.current || activeField === 'password') return;
    const rect = containerRef.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 3;
    const dx = (e.clientX - cx) / rect.width;
    const dy = (e.clientY - cy) / rect.height;
    setEyePos({ x: Math.max(-1, Math.min(1, dx)), y: Math.max(-1, Math.min(1, dy)) });
  }, [activeField]);

  // Eye tracking based on email cursor position
  const handleEmailChange = (e) => {
    const val = e.target.value;
    setEmail(val);
    const progress = Math.min(val.length / 30, 1);
    setEyePos({ x: progress * 2 - 1, y: -0.2 });
  };

  // Cover eyes when password focused
  const eyesCovered = activeField === 'password';
  const peeking = eyesCovered && showPass;

  const mascotMode = celebrating ? 'success' : activeField === 'email' ? 'typing' : 'idle';

  const handleLogin = async (e) => {
    e?.preventDefault();
    setError('');
    if (!email) { setError('Please enter your email address.'); return; }
    if (!password) { setError('Please enter your password.'); return; }

    const result = await login(email, password);
    if (result.success) {
      setCelebrating(true);
      setTimeout(() => { onClose?.(); }, 1200);
    } else {
      setError(result.message || 'Login failed. Please check your credentials.');
    }
  };

  const handleDemoLogin = async (role) => {
    setError('');
    const result = await demoLogin(role);
    if (result.success) {
      setCelebrating(true);
      setTimeout(() => { onClose?.(); }, 2000);
    }
  };

  return (
    <div
      className={
        fullScreenMode
          ? "min-h-screen w-full bg-gradient-to-br from-[#070c18] via-[#0b2545] to-[#040813] flex flex-col items-center justify-center p-4 relative overflow-y-auto"
          : "fixed inset-0 z-50 flex items-center justify-center p-4"
      }
      style={fullScreenMode ? {} : { background: 'rgba(11,60,93,0.85)', backdropFilter: 'blur(8px)' }}
      onClick={(e) => !fullScreenMode && e.target === e.currentTarget && onClose?.()}
    >
      {fullScreenMode && (
        <div className="w-full max-w-md flex items-center justify-between mb-4 px-2">
          <div className="flex items-center gap-2.5">
            <img
              src="/logo.webp"
              alt="Ashoka Stambh"
              className="w-8 h-11 object-contain invert mix-blend-multiply dark:invert-0 dark:mix-blend-screen"
            />
            <div>
              <div className="text-white font-black text-sm tracking-wide">METROSCAN 2026</div>
              <div className="text-blue-300 text-[10px]">Ministry of Consumer Affairs • Govt of India</div>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-[10px] font-bold uppercase tracking-wider">
            Portal Gateway
          </span>
        </div>
      )}

      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-bounce-in"
        style={{ maxHeight: fullScreenMode ? '85vh' : '90vh', overflowY: 'auto' }}
      >
        {celebrating && <Confetti />}

        {/* Gov header strip */}
        <div className="bg-gov-gradient px-6 pt-6 pb-16 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gov-mesh opacity-60" />

          {/* Close button (only shown when in modal mode) */}
          {!fullScreenMode && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-white/60 hover:text-white text-xl leading-none z-10"
              aria-label="Close"
            >
              ×
            </button>
          )}

          <p className="relative text-blue-200 text-xs font-medium uppercase tracking-widest mb-1">
            {t('ministry2')}
          </p>
          <h2 className="relative text-white text-xl font-bold">{t('loginTitle')}</h2>

          {/* Mascot */}
          <div className="relative mt-4 w-28 h-28 mx-auto animate-float">
            <MascotSVG
              mode={mascotMode}
              eyeX={eyePos.x}
              eyeY={eyePos.y}
              eyesCovered={eyesCovered}
              peeking={peeking}
              celebrating={celebrating}
              role={loginMode}
            />
          </div>
        </div>

        {/* Role switcher tabs */}
        <div className="flex border-b border-gray-100 dark:border-gray-800 -mt-8 relative z-10 mx-6 bg-white dark:bg-gray-900 rounded-xl shadow-md overflow-hidden">
          {[
            { key: 'consumer', label: t('citizenTab'), icon: User },
            { key: 'inspector', label: t('officialTab'), icon: ShieldCheck },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => { setLoginMode(key); setError(''); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-semibold transition-all duration-200 ${
                loginMode === key
                  ? 'bg-gov-blue text-white'
                  : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        {/* Form */}
        <div className="p-6 pt-4">

          {/* Tab: Login / Register */}
          <div className="flex gap-4 mb-4 border-b border-gray-100 dark:border-gray-800">
            {['login', 'register'].map(t2 => (
              <button
                key={t2}
                onClick={() => setTab(t2)}
                className={`pb-2 text-sm font-semibold capitalize border-b-2 transition-all ${
                  tab === t2
                    ? 'border-gov-blue text-gov-blue dark:text-blue-300 dark:border-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-600'
                }`}
              >
                {t2 === 'login' ? t('loginBtn') : t('registerLink')}
              </button>
            ))}
          </div>

          {/* Google OAuth 2.0 Button */}
          <div className="mb-4">
            <button
              type="button"
              onClick={async () => {
                setError('');
                const res = await signInWithGoogle();
                if (!res.success && res.message) {
                  setError(res.message);
                }
              }}
              disabled={loading || celebrating}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-700/80 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 font-bold py-2.5 px-4 rounded-xl shadow-sm transition-all text-xs group cursor-pointer hover:shadow-md"
            >
              <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
              </svg>
              <span>Continue with Google (OAuth 2.0)</span>
            </button>

            <div className="relative flex py-3 items-center">
              <div className="flex-grow border-t border-gray-200 dark:border-gray-800"></div>
              <span className="flex-shrink mx-3 text-[10px] text-gray-400 uppercase font-bold tracking-wider">or email login</span>
              <div className="flex-grow border-t border-gray-200 dark:border-gray-800"></div>
            </div>
          </div>

          {tab === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4" noValidate>
              {/* Email */}
              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide">
                  {t('email')}
                </label>
                <input
                  ref={emailRef}
                  type="email"
                  value={email}
                  onChange={handleEmailChange}
                  onFocus={() => setActiveField('email')}
                  onBlur={() => setActiveField('none')}
                  placeholder="inspector@legalmetrology.gov.in"
                  className="gov-input"
                  autoComplete="email"
                />
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                    {t('password')}
                  </label>
                  <button type="button" className="text-xs text-gov-blue dark:text-blue-400 hover:underline">
                    {t('forgotPassword')}
                  </button>
                </div>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onFocus={() => setActiveField('password')}
                    onBlur={() => setActiveField('none')}
                    placeholder="••••••••"
                    className="gov-input pr-11"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(s => !s)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gov-blue transition-colors"
                    tabIndex={-1}
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                  >
                    {showPass ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="text-red-600 dark:text-red-400 text-xs bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2 animate-slide-in-up">
                  {error}
                </div>
              )}

              {celebrating && (
                <div className="text-green-700 dark:text-green-300 text-sm bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-3 py-2 flex items-center gap-2 animate-bounce-in">
                  <Sparkles size={15} /> Login successful! Redirecting...
                </div>
              )}

              <button
                type="submit"
                disabled={loading || celebrating}
                className="btn-gov-primary w-full justify-center py-3 text-base"
              >
                {loading ? (
                  <><Loader2 size={16} className="animate-spin" /> Signing in...</>
                ) : celebrating ? (
                  <><Sparkles size={16} /> Welcome!</>
                ) : (
                  <>{t('loginBtn')} <ChevronRight size={16} /></>
                )}
              </button>
            </form>
          ) : (
            /* Register form */
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setError('');
                const result = await register({
                  email: registerData.email,
                  password: registerData.password,
                  full_name: registerData.full_name,
                  role: loginMode,
                  badge_id: registerData.badge_id || null,
                  department: registerData.department || null,
                  designation: registerData.designation || null,
                });
                if (result.success) {
                  setCelebrating(true);
                  setTimeout(() => onClose?.(), 1200);
                } else {
                  setError(result.message || 'Registration failed.');
                }
              }}
              className="space-y-3"
              noValidate
            >
              {[
                { key: 'full_name', label: 'Full Name', type: 'text', placeholder: 'Rajesh Kumar Sharma' },
                { key: 'email', label: t('email'), type: 'email', placeholder: 'you@example.in' },
                { key: 'password', label: t('password'), type: 'password', placeholder: '••••••••' },
              ].map(field => (
                <div key={field.key}>
                  <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide">
                    {field.label}
                  </label>
                  <input
                    type={field.type}
                    value={registerData[field.key]}
                    onChange={e => setRegisterData(d => ({ ...d, [field.key]: e.target.value }))}
                    placeholder={field.placeholder}
                    className="gov-input"
                  />
                </div>
              ))}

              {loginMode === 'inspector' && (
                <>
                  {[
                    { key: 'badge_id', label: t('badgeId'), placeholder: 'LM-DEL-8492' },
                    { key: 'department', label: t('department'), placeholder: 'Dept. of Legal Metrology, Delhi' },
                    { key: 'designation', label: t('designation'), placeholder: 'Senior Inspector' },
                  ].map(field => (
                    <div key={field.key}>
                      <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide">
                        {field.label}
                      </label>
                      <input
                        value={registerData[field.key]}
                        onChange={e => setRegisterData(d => ({ ...d, [field.key]: e.target.value }))}
                        placeholder={field.placeholder}
                        className="gov-input"
                      />
                    </div>
                  ))}
                </>
              )}

              {error && (
                <div className="text-red-600 text-xs bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              <button type="submit" disabled={loading} className="btn-gov-primary w-full justify-center py-3">
                {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                {t('registerLink')} <ChevronRight size={16} />
              </button>
            </form>
          )}

          {/* Demo quick logins */}
          <div className="mt-5 pt-4 border-t border-gray-100 dark:border-gray-800">
            <p className="text-center text-xs text-gray-400 mb-3 font-medium uppercase tracking-wide">
              Quick Demo Access
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleDemoLogin('consumer')}
                disabled={loading || celebrating}
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 text-xs font-semibold text-gov-blue dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-200"
              >
                <User size={13} /> {t('demoLoginCitizen')}
              </button>
              <button
                onClick={() => handleDemoLogin('inspector')}
                disabled={loading || celebrating}
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg border border-gov-saffron/40 bg-amber-50 dark:bg-amber-900/10 text-xs font-semibold text-amber-700 dark:text-amber-300 hover:bg-amber-100 transition-all duration-200"
              >
                <ShieldCheck size={13} /> {t('demoLoginInspector')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
