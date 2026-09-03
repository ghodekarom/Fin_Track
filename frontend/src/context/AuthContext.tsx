"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { apiClient, setAccessToken } from "@/lib/api-client";
import { AuthResponse, RefreshResponse, User } from "@/types/auth";
import { googleLogout } from "@react-oauth/google";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  sendVerificationCode: (email: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    code: string,
    fullName?: string
  ) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await apiClient.get<User>("/auth/me");
      setUser(response.data);
    } catch {
      setUser(null);
      setAccessToken(null);
    }
  }, []);

  // Initial silent auth refresh on mount
  useEffect(() => {
    let isMounted = true;

    const initializeAuth = async () => {
      try {
        const refreshRes = await apiClient.post<RefreshResponse>("/auth/refresh");
        if (isMounted && refreshRes.data.access_token) {
          setAccessToken(refreshRes.data.access_token);
          await fetchCurrentUser();
        }
      } catch {
        if (isMounted) {
          setUser(null);
          setAccessToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initializeAuth();

    return () => {
      isMounted = false;
    };
  }, [fetchCurrentUser]);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<AuthResponse>("/auth/login", {
      email,
      password,
    });
    setAccessToken(response.data.access_token);
    setUser(response.data.user);
  };

  const sendVerificationCode = async (email: string) => {
    await apiClient.post("/auth/send-verification-code", {
      email,
    });
  };

  const register = async (
    email: string,
    password: string,
    code: string,
    fullName?: string
  ) => {
    const response = await apiClient.post<AuthResponse>("/auth/register", {
      email,
      password,
      code,
      full_name: fullName,
    });
    setAccessToken(response.data.access_token);
    setUser(response.data.user);
  };

  const loginWithGoogle = async (idToken: string) => {
    const response = await apiClient.post<AuthResponse>("/auth/google", {
      id_token: idToken,
    });
    setAccessToken(response.data.access_token);
    setUser(response.data.user);
  };

  const logout = async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      try {
        googleLogout();
      } catch (e) {}
      setAccessToken(null);
      setUser(null);
    }
  };

  const logoutAll = async () => {
    try {
      await apiClient.post("/auth/logout-all");
    } finally {
      try {
        googleLogout();
      } catch (e) {}
      setAccessToken(null);
      setUser(null);
    }
  };

  const refreshUser = async () => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        sendVerificationCode,
        register,
        loginWithGoogle,
        logout,
        logoutAll,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
