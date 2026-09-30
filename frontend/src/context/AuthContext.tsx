import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../services/api';
import type { UserMe, LoginRequest } from '../types';
import apiClient from '../services/apiClient';

interface AuthContextType {
  user: UserMe | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserMe | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = async () => {
    const token = localStorage.getItem('sentinelx_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await authApi.me();
      setUser(userData);
      localStorage.setItem('sentinelx_user', JSON.stringify(userData));
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('sentinelx_token');
      localStorage.removeItem('sentinelx_user');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    const { access_token } = await authApi.login(credentials);
    localStorage.setItem('sentinelx_token', access_token);
    
    // Setup api client token immediately for the next request
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    await checkAuth();
  };

  const logout = () => {
    localStorage.removeItem('sentinelx_token');
    localStorage.removeItem('sentinelx_user');
    delete apiClient.defaults.headers.common['Authorization'];
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
