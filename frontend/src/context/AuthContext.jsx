import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    // Check if there is an existing saved session
    const saved = localStorage.getItem('packcheck_user');
    if (saved) {
      try { return JSON.parse(saved); } catch { return null; }
    }
    // Brand new visitor starts logged out - opens login screen first
    return null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('packcheck_user', JSON.stringify(user));
      localStorage.removeItem('packcheck_logged_out');
    } else {
      localStorage.removeItem('packcheck_user');
    }
  }, [user]);

  const login = async (emailOrUser, password) => {
    await new Promise(resolve => setTimeout(resolve, 300));
    // Support login(userObject)
    if (typeof emailOrUser === 'object' && emailOrUser !== null) {
      const name = emailOrUser.name || emailOrUser.username || 'Authorized Officer';
      const newUser = {
        id: emailOrUser.id || `OFF-2026-${Math.floor(Math.random() * 900) + 100}`,
        name: name,
        username: emailOrUser.username || name.toLowerCase().replace(/\s+/g, '.'),
        email: emailOrUser.email || (emailOrUser.username && emailOrUser.username.includes('@') ? emailOrUser.username : `${name.toLowerCase().replace(/\s+/g, '.')}@lm.gov.in`),
        role: emailOrUser.role || 'Legal Metrology Enforcement Officer',
        badge: emailOrUser.badgeNumber || emailOrUser.badge || `LMO-DL-${Math.floor(Math.random() * 9000) + 1000}`,
        location: emailOrUser.location || 'Delhi NCR Region',
      };
      setUser(newUser);
      return true;
    }
    // Support login(nameOrEmail, password)
    if (emailOrUser && password) {
      const name = emailOrUser.includes('@') 
        ? emailOrUser.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        : emailOrUser.replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      const newUser = {
        id: `OFF-2026-${Math.floor(Math.random() * 900) + 100}`,
        name: name,
        username: emailOrUser,
        email: emailOrUser.includes('@') ? emailOrUser : `${emailOrUser.toLowerCase().replace(/\s+/g, '.')}@lm.gov.in`,
        role: 'Legal Metrology Enforcement Officer',
        badge: `LMO-DL-${Math.floor(Math.random() * 9000) + 1000}`,
        location: 'Delhi NCR Region',
      };
      setUser(newUser);
      return true;
    }
    return false;
  };

  const updateUser = (fields = {}) => {
    setUser(prev => {
      if (!prev) return prev;
      const updated = { ...prev, ...fields };
      localStorage.setItem('packcheck_user', JSON.stringify(updated));
      return updated;
    });
  };

  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const logout = () => {
    setIsLoggingOut(true);
    localStorage.setItem('packcheck_logged_out', 'true');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoggingOut, setIsLoggingOut, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
