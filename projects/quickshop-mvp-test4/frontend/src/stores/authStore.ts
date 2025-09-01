import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials, RegisterData } from '../types';
import { apiClient } from '../api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiClient.auth.login(credentials);
          
          // Store tokens and user data
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('refresh_token', response.refresh_token);
          localStorage.setItem('user', JSON.stringify(response.user));
          
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          // Reload page to update navigation and app state
          window.location.reload();
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed';
          set({
            isLoading: false,
            error: errorMessage,
            isAuthenticated: false,
            user: null,
          });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });
        try {
          const user = await apiClient.auth.register(data);
          
          // After successful registration, automatically log in
          await get().login({
            username: data.username,
            password: data.password,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed';
          set({
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      logout: () => {
        // Clear all stored data
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        set({
          user: null,
          isAuthenticated: false,
          error: null,
        });

        // Reload page to reset app state
        window.location.reload();
      },

      refreshToken: async () => {
        try {
          const response = await apiClient.auth.refresh();
          localStorage.setItem('token', response.access_token);
        } catch (error) {
          // Refresh failed, logout user
          get().logout();
        }
      },

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token');
        const userStr = localStorage.getItem('user');
        
        if (token && userStr) {
          try {
            const user = JSON.parse(userStr);
            // Verify token is still valid by fetching user data
            const currentUser = await apiClient.auth.me();
            
            set({
              user: currentUser,
              isAuthenticated: true,
            });
          } catch (error) {
            // Token invalid, clear auth data
            get().logout();
          }
        } else {
          set({
            user: null,
            isAuthenticated: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);