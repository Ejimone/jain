import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import authService, { User, LoginRequest, RegisterRequest } from '../services/authService';
import { ApiResponse } from '../services/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<ApiResponse>;
  register: (userData: RegisterRequest) => Promise<ApiResponse>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<ApiResponse>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on app start
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const authenticated = await authService.isAuthenticated();
      if (authenticated) {
        const response = await authService.getProfile();
        if (response.success && response.data) {
          setUser(response.data);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          await authService.logout();
        }
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest): Promise<ApiResponse> => {
    setIsLoading(true);
    try {
      console.log('AuthContext: Starting login...', credentials.email);
      const response = await authService.login(credentials);
      console.log('AuthContext: Login response:', response);
      
      if (response.success && response.data) {
        console.log('AuthContext: Login successful, setting user:', response.data.user);
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        console.log('AuthContext: Login failed:', response.error);
      }
      return response;
    } catch (error) {
      console.error('AuthContext: Login error:', error);
      return {
        success: false,
        error: 'Login failed. Please try again.',
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<ApiResponse> => {
    setIsLoading(true);
    try {
      console.log('AuthContext: Starting registration...', userData.email);
      const response = await authService.register(userData);
      console.log('AuthContext: Registration response:', response);
      
      if (response.success && response.data) {
        console.log('AuthContext: Registration successful, setting user:', response.data.user);
        setUser(response.data.user);
        setIsAuthenticated(true);
      } else {
        console.log('AuthContext: Registration failed:', response.error);
      }
      return response;
    } catch (error) {
      console.error('AuthContext: Registration error:', error);
      return {
        success: false,
        error: 'Registration failed. Please try again.',
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<ApiResponse> => {
    try {
      const response = await authService.updateProfile(userData);
      if (response.success && response.data) {
        setUser(response.data);
      }
      return response;
    } catch (error) {
      console.error('Profile update failed:', error);
      return {
        success: false,
        error: 'Profile update failed. Please try again.',
      };
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const response = await authService.getProfile();
      if (response.success && response.data) {
        setUser(response.data);
      }
    } catch (error) {
      console.error('User refresh failed:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 