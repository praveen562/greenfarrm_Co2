import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import * as apiService from "../services/api";
import { TOKEN_STORAGE_KEY } from "../services/api";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// sessionStorage (not localStorage) is a deliberate choice for this academic
// MVP: the token clears when the tab closes, which is a reasonable default
// when there's no refresh-token / rotation story yet. Documented in the
// README's Limitations section.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const currentUser = await apiService.getCurrentUser();
      setUser(currentUser);
    } catch {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiService.login(email, password);
    sessionStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    const currentUser = await apiService.getCurrentUser();
    setUser(currentUser);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    await apiService.register(email, password, fullName);
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
