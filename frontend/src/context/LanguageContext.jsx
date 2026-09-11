import { createContext, useContext, useState } from 'react';

const translations = {
  en: {
    // Header
    deptName: 'Department of Legal Metrology',
    ministry: 'Ministry of Consumer Affairs, Food & Public Distribution · Government of India',
    appTitle: 'MetroScan',
    appSubtitle: 'Packaged Commodity Compliance System',
    login: 'Login',
    getStarted: 'Get Started',
    logout: 'Logout',

    // Navigation
    home: 'Home',
    aboutUs: 'About Us',
    howItWorks: 'How It Works',
    legalRules: 'Legal Metrology (PC) Rules, 2011',
    guidelines: 'Guidelines',
    contactUs: 'Contact Us',

    // Hero Section
    heroHeadline: 'Protect Consumers.',
    heroHeadline2: 'Enforce Compliance.',
    heroSubtitle: 'Scan any packaged commodity and verify compliance with Legal Metrology (Packaged Commodities) Rules, 2011 in under 30 seconds.',
    scanNowBtn: 'Scan a Package',
    viewDashboard: 'View Dashboard',

    // Scan Section
    uploadTitle: 'Upload Package Images',
    uploadHint: 'Drag & drop or click to upload package photos (Front, Back, MRP panel)',
    analyzeBtn: 'Analyse Package',
    clearBtn: 'Clear',
    processingMsg: 'Analysing package for compliance...',

    // Results
    overallStatus: 'Overall Status',
    compliant: 'COMPLIANT',
    nonCompliant: 'NON-COMPLIANT',
    warning: 'WARNING',
    complianceScore: 'Compliance Score',
    ruleCheck: 'Rule Verification',
    downloadPdf: 'Download PDF Certificate',

    // Dashboard
    dashboardTitle: 'Command Dashboard',
    totalScans: 'Total Scans',
    violations: 'Violations Detected',
    complianceRate: 'Compliance Rate',
    pendingNotices: 'Pending Notices',
    heatmapTitle: 'Inspection Heatmap — India',
    recentScans: 'Recent Audit Activity',

    // Auth
    loginTitle: 'Welcome to MetroScan',
    loginSubtitle: 'Sign in to continue',
    email: 'Email Address',
    password: 'Password',
    forgotPassword: 'Forgot Password?',
    loginBtn: 'Sign In',
    noAccount: "Don't have an account?",
    registerLink: 'Register',
    citizenTab: 'Citizen Consumer',
    officialTab: 'Official Inspector',
    demoLoginCitizen: 'Demo — Citizen Login',
    demoLoginInspector: 'Demo — Inspector Login',
    badgeId: 'Badge ID',
    department: 'Department',
    designation: 'Designation',

    // Footer
    quickLinks: 'Quick Links',
    importantLinks: 'Important Links',
    contactInfo: 'Contact Us',
    allRightsReserved: 'All Rights Reserved',
    poweredBy: 'Powered by Smart India Hackathon 2026',
    disclaimer: 'This is a prototype developed for SIH 2026. For official compliance matters, contact your State Legal Metrology Department.',
    ministry2: 'Ministry of Consumer Affairs, Food & Public Distribution',
    govOfIndia: 'Government of India',
  },

  hi: {
    deptName: 'विधिक माप विज्ञान विभाग',
    ministry: 'उपभोक्ता मामले, खाद्य एवं सार्वजनिक वितरण मंत्रालय · भारत सरकार',
    appTitle: 'मेट्रोस्कैन (MetroScan)',
    appSubtitle: 'पैकेज्ड कमोडिटी अनुपालन प्रणाली',
    login: 'लॉगिन',
    getStarted: 'शुरू करें',
    logout: 'लॉग आउट',

    home: 'होम',
    aboutUs: 'हमारे बारे में',
    howItWorks: 'यह कैसे काम करता है',
    legalRules: 'विधिक माप (PC) नियम, 2011',
    guidelines: 'दिशानिर्देश',
    contactUs: 'संपर्क करें',

    heroHeadline: 'उपभोक्ताओं की रक्षा करें।',
    heroHeadline2: 'अनुपालन सुनिश्चित करें।',
    heroSubtitle: 'किसी भी पैकेज्ड वस्तु को स्कैन करें और 30 सेकंड में विधिक माप (पैकेज्ड कमोडिटीज) नियम, 2011 के अनुपालन की जाँच करें।',
    scanNowBtn: 'पैकेज स्कैन करें',
    viewDashboard: 'डैशबोर्ड देखें',

    uploadTitle: 'पैकेज छवियाँ अपलोड करें',
    uploadHint: 'पैकेज की फ़ोटो यहाँ खींचें और छोड़ें (आगे, पीछे, MRP पैनल)',
    analyzeBtn: 'पैकेज विश्लेषण करें',
    clearBtn: 'साफ़ करें',
    processingMsg: 'अनुपालन के लिए पैकेज का विश्लेषण हो रहा है...',

    overallStatus: 'समग्र स्थिति',
    compliant: 'अनुपालित',
    nonCompliant: 'गैर-अनुपालित',
    warning: 'चेतावनी',
    complianceScore: 'अनुपालन स्कोर',
    ruleCheck: 'नियम सत्यापन',
    downloadPdf: 'PDF प्रमाणपत्र डाउनलोड करें',

    dashboardTitle: 'कमांड डैशबोर्ड',
    totalScans: 'कुल स्कैन',
    violations: 'उल्लंघन पाए गए',
    complianceRate: 'अनुपालन दर',
    pendingNotices: 'लंबित नोटिस',
    heatmapTitle: 'निरीक्षण हीटमैप — भारत',
    recentScans: 'हालिया ऑडिट गतिविधि',

    loginTitle: 'MetroScan में आपका स्वागत है',
    loginSubtitle: 'जारी रखने के लिए साइन इन करें',
    email: 'ईमेल पता',
    password: 'पासवर्ड',
    forgotPassword: 'पासवर्ड भूल गए?',
    loginBtn: 'साइन इन करें',
    noAccount: 'खाता नहीं है?',
    registerLink: 'पंजीकरण करें',
    citizenTab: 'नागरिक उपभोक्ता',
    officialTab: 'आधिकारिक निरीक्षक',
    demoLoginCitizen: 'डेमो — नागरिक लॉगिन',
    demoLoginInspector: 'डेमो — निरीक्षक लॉगिन',
    badgeId: 'बैज ID',
    department: 'विभाग',
    designation: 'पदनाम',

    quickLinks: 'त्वरित लिंक',
    importantLinks: 'महत्वपूर्ण लिंक',
    contactInfo: 'संपर्क जानकारी',
    allRightsReserved: 'सर्वाधिकार सुरक्षित',
    poweredBy: 'स्मार्ट इंडिया हैकाथॉन 2026 द्वारा संचालित',
    disclaimer: 'यह SIH 2026 के लिए एक प्रोटोटाइप है।',
    ministry2: 'उपभोक्ता मामले, खाद्य एवं सार्वजनिक वितरण मंत्रालय',
    govOfIndia: 'भारत सरकार',
  },

  mr: {
    deptName: 'कायदेशीर मेट्रोलॉजी विभाग',
    ministry: 'ग्राहक व्यवहार, अन्न व सार्वजनिक वितरण मंत्रालय · भारत सरकार',
    appTitle: 'मेट्रोस्कॅन (MetroScan)',
    appSubtitle: 'पॅकेज्ड कमोडिटी अनुपालन प्रणाली',
    login: 'लॉगिन',
    getStarted: 'सुरू करा',
    logout: 'लॉग आउट',

    home: 'मुख्यपृष्ठ',
    aboutUs: 'आमच्याबद्दल',
    howItWorks: 'हे कसे कार्य करते',
    legalRules: 'कायदेशीर माप (PC) नियम, 2011',
    guidelines: 'मार्गदर्शक तत्त्वे',
    contactUs: 'संपर्क करा',

    heroHeadline: 'ग्राहकांचे रक्षण करा।',
    heroHeadline2: 'अनुपालन लागू करा।',
    heroSubtitle: 'कोणत्याही पॅकेज्ड वस्तूचे स्कॅन करा आणि 30 सेकंदात कायदेशीर माप नियम 2011 चे अनुपालन तपासा।',
    scanNowBtn: 'पॅकेज स्कॅन करा',
    viewDashboard: 'डॅशबोर्ड पाहा',

    uploadTitle: 'पॅकेज प्रतिमा अपलोड करा',
    uploadHint: 'पॅकेजचे फोटो येथे ड्रॅग करा (समोर, मागे, MRP पॅनल)',
    analyzeBtn: 'पॅकेज विश्लेषण करा',
    clearBtn: 'साफ करा',
    processingMsg: 'अनुपालनासाठी पॅकेजचे विश्लेषण केले जात आहे...',

    overallStatus: 'एकूण स्थिती',
    compliant: 'अनुपालित',
    nonCompliant: 'अनुपालित नाही',
    warning: 'चेतावणी',
    complianceScore: 'अनुपालन गुण',
    ruleCheck: 'नियम सत्यापन',
    downloadPdf: 'PDF प्रमाणपत्र डाउनलोड करा',

    dashboardTitle: 'कमांड डॅशबोर्ड',
    totalScans: 'एकूण स्कॅन',
    violations: 'उल्लंघने आढळली',
    complianceRate: 'अनुपालन दर',
    pendingNotices: 'प्रलंबित नोटिसेस',
    heatmapTitle: 'निरीक्षण हीटमॅप — भारत',
    recentScans: 'अलीकडील लेखापरीक्षण क्रियाकलाप',

    loginTitle: 'MetroScan मध्ये आपले स्वागत आहे',
    loginSubtitle: 'सुरू ठेवण्यासाठी साइन इन करा',
    email: 'ईमेल पत्ता',
    password: 'पासवर्ड',
    forgotPassword: 'पासवर्ड विसरलात?',
    loginBtn: 'साइन इन करा',
    noAccount: 'खाते नाही?',
    registerLink: 'नोंदणी करा',
    citizenTab: 'नागरिक ग्राहक',
    officialTab: 'अधिकृत निरीक्षक',
    demoLoginCitizen: 'डेमो — नागरिक लॉगिन',
    demoLoginInspector: 'डेमो — निरीक्षक लॉगिन',
    badgeId: 'बॅज ID',
    department: 'विभाग',
    designation: 'पदनाम',

    quickLinks: 'द्रुत दुवे',
    importantLinks: 'महत्त्वाचे दुवे',
    contactInfo: 'संपर्क माहिती',
    allRightsReserved: 'सर्व हक्क राखीव',
    poweredBy: 'स्मार्ट इंडिया हॅकाथॉन 2026 द्वारे संचालित',
    disclaimer: 'हे SIH 2026 साठी एक प्रोटोटाइप आहे।',
    ministry2: 'ग्राहक व्यवहार, अन्न व सार्वजनिक वितरण मंत्रालय',
    govOfIndia: 'भारत सरकार',
  },
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('metroscan_lang') || 'en');

  const t = (key) => translations[lang]?.[key] ?? translations.en[key] ?? key;

  const changeLang = (l) => {
    setLang(l);
    localStorage.setItem('metroscan_lang', l);
    document.documentElement.lang = l === 'en' ? 'en' : l === 'hi' ? 'hi' : 'mr';
  };

  return (
    <LanguageContext.Provider value={{ lang, t, changeLang, languages: [
      { code: 'en', label: 'English', native: 'English' },
      { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
      { code: 'mr', label: 'Marathi', native: 'मराठी' },
    ]}}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLang = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLang must be used within LanguageProvider');
  return ctx;
};
