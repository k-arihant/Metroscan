import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

const AuthContext = createContext(null);

const SUPABASE_PROJECT_URL = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key';

export const supabaseClient = createClient(SUPABASE_PROJECT_URL, SUPABASE_ANON_KEY);

const DEMO_USERS = {
  inspector: {
    id: 'demo-inspector-001',
    email: 'inspector@legalmetrology.gov.in',
    full_name: 'Rajesh Kumar Sharma',
    role: 'inspector',
    badge_id: 'LM-DEL-8492',
    department: 'Department of Legal Metrology, Delhi Region',
    designation: 'Senior Inspector',
    authenticated: true,
    access_token: 'mock-jwt-token-inspector-active',
  },
  consumer: {
    id: 'demo-citizen-001',
    email: 'citizen@example.in',
    full_name: 'Priya Mehta',
    role: 'consumer',
    authenticated: true,
    access_token: 'mock-jwt-token-xyz-12345',
  },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loginMode, setLoginMode] = useState('consumer'); // 'consumer' | 'inspector'

  // Validate session on mount
  useEffect(() => {
    const initAuth = async () => {
      const stored = localStorage.getItem('metroscan_user');
      let initialUser = null;
      if (stored) {
        try {
          initialUser = JSON.parse(stored);
        } catch {
          localStorage.removeItem('metroscan_user');
        }
      }

      // Check active Supabase OAuth session on redirect
      try {
        const { data: { session } } = await supabaseClient.auth.getSession();
        if (session?.user && session?.access_token) {
          // Fetch authoritative profile from backend using token
          try {
            const meRes = await fetch('/api/v1/auth/me', {
              headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (meRes.ok) {
              const profile = await meRes.json();
              const oauthUser = {
                ...profile,
                authenticated: true,
                access_token: session.access_token,
              };
              setUser(oauthUser);
              localStorage.setItem('metroscan_user', JSON.stringify(oauthUser));
              setLoading(false);
              return;
            }
          } catch { /* proceed to fallback below */ }

          const fallbackUser = {
            id: session.user.id,
            email: session.user.email,
            full_name: session.user.user_metadata?.full_name || session.user.email?.split('@')[0] || 'Verified Citizen',
            role: session.user.user_metadata?.role || 'consumer',
            authenticated: true,
            access_token: session.access_token,
          };
          setUser(fallbackUser);
          localStorage.setItem('metroscan_user', JSON.stringify(fallbackUser));
          setLoading(false);
          return;
        }
      } catch (err) {
        console.warn('OAuth session check notice:', err);
      }

      // If we had a stored user, verify their token with backend /api/v1/auth/me
      if (initialUser?.access_token) {
        try {
          const res = await fetch('/api/v1/auth/me', {
            headers: { 'Authorization': `Bearer ${initialUser.access_token}` },
          });
          if (res.ok) {
            const verified = await res.json();
            const updatedUser = {
              ...initialUser,
              ...verified,
              authenticated: true,
              access_token: initialUser.access_token,
            };
            setUser(updatedUser);
            localStorage.setItem('metroscan_user', JSON.stringify(updatedUser));
          } else {
            // Token expired or invalid — clear session
            localStorage.removeItem('metroscan_user');
            setUser(null);
          }
        } catch {
          // Backend offline or network error — if demo token allow it, otherwise keep
          if (initialUser.access_token?.startsWith('demo-')) {
            setUser(initialUser);
          } else {
            localStorage.removeItem('metroscan_user');
            setUser(null);
          }
        }
      } else {
        setUser(null);
      }

      setLoading(false);
    };

    initAuth();

    const { data: { subscription } } = supabaseClient.auth.onAuthStateChange(async (_event, session) => {
      if (session?.user && session?.access_token) {
        try {
          const meRes = await fetch('/api/v1/auth/me', {
            headers: { 'Authorization': `Bearer ${session.access_token}` },
          });
          if (meRes.ok) {
            const profile = await meRes.json();
            const oauthUser = {
              ...profile,
              authenticated: true,
              access_token: session.access_token,
            };
            setUser(oauthUser);
            localStorage.setItem('metroscan_user', JSON.stringify(oauthUser));
            return;
          }
        } catch {}

        const fallbackUser = {
          id: session.user.id,
          email: session.user.email,
          full_name: session.user.user_metadata?.full_name || session.user.email?.split('@')[0] || 'Verified Citizen',
          role: session.user.user_metadata?.role || 'consumer',
          authenticated: true,
          access_token: session.access_token,
        };
        setUser(fallbackUser);
        localStorage.setItem('metroscan_user', JSON.stringify(fallbackUser));
      }
    });

    return () => {
      subscription?.unsubscribe?.();
    };
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = await res.json().catch(() => null);

      if (res.ok && data && (data.status === 'success' || data.access_token)) {
        const userData = { ...data, authenticated: true };
        setUser(userData);
        localStorage.setItem('metroscan_user', JSON.stringify(userData));
        setLoading(false);
        return { success: true, user: userData };
      } else {
        setLoading(false);
        return {
          success: false,
          message: data?.detail || 'Invalid email or password. Please check credentials.',
        };
      }
    } catch (err) {
      setLoading(false);
      return {
        success: false,
        message: err.message || 'Unable to connect to authentication server.',
      };
    }
  }, []);

  const demoLogin = useCallback(async (role) => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/demo-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      });
      if (res.ok) {
        const data = await res.json();
        const demoUser = { ...data, authenticated: true };
        setUser(demoUser);
        localStorage.setItem('metroscan_user', JSON.stringify(demoUser));
        setLoading(false);
        return { success: true, user: demoUser };
      }
    } catch {}

    // Fallback isolated demo user if backend unreachable
    await new Promise(r => setTimeout(r, 400));
    const demoUser = DEMO_USERS[role] || DEMO_USERS.consumer;
    setUser(demoUser);
    localStorage.setItem('metroscan_user', JSON.stringify(demoUser));
    setLoading(false);
    return { success: true, user: demoUser };
  }, []);

  const signInWithGoogle = useCallback(async () => {
    setLoading(true);
    try {
      const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin,
        },
      });
      if (error) throw error;
      return { success: true, data };
    } catch (err) {
      console.warn('Google OAuth notice:', err);
      return {
        success: false,
        message: err.message || 'Google OAuth provider setup required in Supabase console.',
      };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try { await supabaseClient.auth.signOut(); } catch {}
    setUser(null);
    localStorage.removeItem('metroscan_user');
  }, []);

  const register = useCallback(async (data) => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await res.json().catch(() => null);
      if (res.ok && result?.status === 'success') {
        const userData = { ...result, authenticated: true };
        setUser(userData);
        localStorage.setItem('metroscan_user', JSON.stringify(userData));
        setLoading(false);
        return { success: true, data: result };
      } else {
        setLoading(false);
        return {
          success: false,
          message: result?.detail || 'Registration failed. Please check your details.',
        };
      }
    } catch (err) {
      setLoading(false);
      return {
        success: false,
        message: err.message || 'Failed to connect to server for registration.',
      };
    }
  }, []);

  const getAuthHeaders = useCallback(() => {
    return user?.access_token ? { 'Authorization': `Bearer ${user.access_token}` } : {};
  }, [user?.access_token]);

  const role = user?.role?.toLowerCase();
  const isInspector = ['inspector', 'admin', 'director', 'regulator'].includes(role);
  const isConsumer = !user || role === 'consumer' || role === 'citizen';

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      loginMode,
      setLoginMode,
      login,
      signInWithGoogle,
      demoLogin,
      logout,
      register,
      isAuthenticated: !!user && !!user.authenticated,
      isInspector,
      isConsumer,
      token: user?.access_token || null,
      getAuthHeaders,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
