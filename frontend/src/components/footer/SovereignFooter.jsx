import { ExternalLink, Phone, Mail, MapPin } from 'lucide-react';
import { useLang } from '../../context/LanguageContext';

/* ─── Rotating Four-Point ✱ Star (DESIGN2.md reference) ─── */
function RotatingStar({ size = 40, color = 'currentColor', speed = '8s' }) {
  return (
    <span
      className="inline-block flex-shrink-0"
      aria-hidden="true"
      style={{
        animation: `star-rotate ${speed} linear infinite`,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: size,
        height: size,
        transformOrigin: 'center center',
      }}
    >
      <svg
        viewBox="0 0 40 40"
        width={size}
        height={size}
        xmlns="http://www.w3.org/2000/svg"
        fill={color}
      >
        {/*
          Four-point concave star — matches the ✱ shape from DESIGN2.md Osmo reference:
          "Mono Tag Strip: prefixed with a green '✱' marker"
          The shape is created by four fat teardrop/diamond lobes meeting at the center.
        */}
        <path d="
          M 20 0
          C 22 8, 22 10, 20 20
          C 18 10, 18 8, 20 0
          Z
        " opacity="1" />
        <path d="
          M 40 20
          C 32 22, 30 22, 20 20
          C 30 18, 32 18, 40 20
          Z
        " opacity="1" />
        <path d="
          M 20 40
          C 18 32, 18 30, 20 20
          C 22 30, 22 32, 20 40
          Z
        " opacity="1" />
        <path d="
          M 0 20
          C 8 18, 10 18, 20 20
          C 10 22, 8 22, 0 20
          Z
        " opacity="1" />
        {/* Center dot */}
        <circle cx="20" cy="20" r="2.5" />
      </svg>
    </span>
  );
}

export default function SovereignFooter() {
  const { t } = useLang();

  const quickLinks = [
    { label: t('home'), href: '#home' },
    { label: t('aboutUs'), href: '#about' },
    { label: t('howItWorks'), href: '#how-it-works' },
    { label: t('legalRules'), href: '#legal-rules' },
    { label: t('guidelines'), href: '#guidelines' },
    { label: t('contactUs'), href: '#contact' },
  ];

  const govLinks = [
    { label: 'Ministry of Consumer Affairs', href: 'https://consumeraffairs.nic.in', external: true },
    { label: 'Legal Metrology Division', href: 'https://legalmetrology.gov.in', external: true },
    { label: 'National Consumer Helpline', href: 'https://consumerhelpline.gov.in', external: true },
    { label: 'BIS Standards', href: 'https://bis.gov.in', external: true },
    { label: 'FSSAI Food Safety', href: 'https://fssai.gov.in', external: true },
  ];

  return (
    <footer id="contact" className="bg-gov-navy dark:bg-gray-950 text-white">
      {/* Main footer content */}
      <div className="max-w-screen-xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">

          {/* Brand column */}
          <div className="lg:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              {/* India emblem simplified */}
              <div className="w-10 h-10 rounded-full bg-gov-saffron/20 border border-gov-saffron/40 flex items-center justify-center text-gov-saffron font-black text-lg">
                ⚖
              </div>
              <div>
                <div className="font-black text-base text-white">MetroScan</div>
                <div className="text-[10px] text-blue-300/60 font-medium uppercase tracking-wider">SIH 2026</div>
              </div>
            </div>
            <p className="text-blue-200/70 text-xs leading-relaxed mb-4">
              Automated compliance verification for Legal Metrology (Packaged Commodities) Rules, 2011.
              Protecting consumers across India.
            </p>
            {/* Rotating star animation from DESIGN2.md */}
            <div className="flex items-center gap-3 mt-4">
              <RotatingStar size={32} color="#F39C12" speed="6s" />
              <RotatingStar size={22} color="#AED6F1" speed="10s" />
              <RotatingStar size={16} color="rgba(255,255,255,0.25)" speed="14s" />
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-widest text-gov-saffron mb-4">
              {t('quickLinks')}
            </h4>
            <ul className="space-y-2">
              {quickLinks.map(link => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    onClick={e => {
                      e.preventDefault();
                      document.querySelector(link.href)?.scrollIntoView({ behavior: 'smooth' });
                    }}
                    className="text-blue-200/70 hover:text-white text-sm transition-colors flex items-center gap-1.5 group"
                  >
                    <span className="w-1 h-1 rounded-full bg-gov-saffron/50 group-hover:bg-gov-saffron transition-colors" />
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Government Links */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-widest text-gov-saffron mb-4">
              {t('importantLinks')}
            </h4>
            <ul className="space-y-2">
              {govLinks.map(link => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    target={link.external ? '_blank' : undefined}
                    rel={link.external ? 'noopener noreferrer' : undefined}
                    className="text-blue-200/70 hover:text-white text-sm transition-colors flex items-center gap-1.5 group"
                  >
                    <span className="w-1 h-1 rounded-full bg-gov-saffron/50 group-hover:bg-gov-saffron transition-colors" />
                    {link.label}
                    {link.external && <ExternalLink size={10} className="opacity-50 group-hover:opacity-100" />}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-widest text-gov-saffron mb-4">
              {t('contactInfo')}
            </h4>
            <ul className="space-y-3 text-sm text-blue-200/70">
              <li className="flex gap-2.5">
                <MapPin size={15} className="text-gov-saffron flex-shrink-0 mt-0.5" />
                <span>Department of Legal Metrology, Udyog Bhavan, New Delhi — 110 011</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Phone size={15} className="text-gov-saffron flex-shrink-0" />
                <a href="tel:1915" className="hover:text-white transition-colors">1915 (Consumer Helpline)</a>
              </li>
              <li className="flex items-center gap-2.5">
                <Mail size={15} className="text-gov-saffron flex-shrink-0" />
                <a href="mailto:metrology@gov.in" className="hover:text-white transition-colors">metrology@gov.in</a>
              </li>
            </ul>

            {/* Additional star animations for contact column */}
            <div className="mt-6 flex items-center gap-2 opacity-30">
              <RotatingStar size={14} color="#F39C12" speed="5s" />
              <div className="h-px flex-1 bg-white/10" />
              <RotatingStar size={14} color="#F39C12" speed="7s" />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/10">
        <div className="max-w-screen-xl mx-auto px-6 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-blue-300/50">
              <RotatingStar size={14} color="#F39C12" speed="8s" />
              <span>© 2026 {t('govOfIndia')} · {t('allRightsReserved')}</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-blue-300/40">
              <span>{t('poweredBy')}</span>
              <RotatingStar size={12} color="rgba(243,156,18,0.6)" speed="10s" />
            </div>
          </div>
          <p className="text-[10px] text-blue-300/30 text-center mt-2 leading-relaxed">
            {t('disclaimer')}
          </p>
        </div>
      </div>
    </footer>
  );
}
