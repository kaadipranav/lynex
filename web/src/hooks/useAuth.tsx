import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, User } from '../api/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const storedUser = authApi.getUser();
    if (storedUser && authApi.isAuthenticated()) {
      setUser(storedUser);
      // Optionally verify token is still valid
      authApi.getMe()
        .then(setUser)
        .catch(() => {
          // Token expired, clear auth
          authApi.logout();
          setUser(null);
        });
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setUser(response.user);
  };

  const signup = async (email: string, password: string, name?: string) => {
    const response = await authApi.signup(email, password, name);
    setUser(response.user);
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      signup,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
