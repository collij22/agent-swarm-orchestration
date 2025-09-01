import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserLogin, UserCreate } from '../types/api';
import { apiClient } from '../api/client';
import toast from 'react-hot-toast';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  updateUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials: UserLogin) => {
        try {
          set({ isLoading: true });
          const response = await apiClient.auth.login(credentials);
          
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('refresh_token', response.refresh_token);
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });

          toast.success(`Welcome back, ${response.user.first_name}!`);
        } catch (error: any) {
          set({ isLoading: false });
          const message = error.response?.data?.detail || 'Login failed';
          toast.error(message);
          throw error;
        }
      },

      register: async (userData: UserCreate) => {
        try {
          set({ isLoading: true });
          const user = await apiClient.auth.register(userData);
          
          // Auto-login after registration
          await get().login({
            username: userData.username,
            password: userData.password,
          });

          toast.success('Account created successfully!');
        } catch (error: any) {
          set({ isLoading: false });
          const message = error.response?.data?.detail || 'Registration failed';
          toast.error(message);
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
        toast.success('Logged out successfully');
        window.location.href = '/';
      },

      checkAuth: async () => {
        const token = localStorage.getItem('token');
        if (!token) {
          set({ isAuthenticated: false, user: null, token: null });
          return;
        }

        try {
          const user = await apiClient.auth.me();
          set({
            user,
            token,
            isAuthenticated: true,
          });
        } catch (error) {
          // Token is invalid, clear auth state
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
        }
      },

      updateUser: (user: User) => {
        set({ user });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);