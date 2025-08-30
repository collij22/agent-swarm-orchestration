#!/usr/bin/env python3
"""
SFA Frontend Specialist - Single File Agent for React Frontend Development

This agent creates complete React + TypeScript applications with:
- Vite build setup
- Tailwind CSS configuration
- API client generation from backend routes
- Authentication flow with JWT
- CRUD form components
- State management with Zustand and React Query
"""

import os
import sys
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.agent_logger import ReasoningLogger, get_logger

@dataclass
class FrontendConfig:
    """Configuration for frontend generation"""
    project_name: str
    api_base_url: str = "http://localhost:8000"
    auth_enabled: bool = True
    resources: List[Dict[str, Any]] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.resources is None:
            self.resources = []
        if self.features is None:
            self.features = []

class FrontendSpecialist:
    """Frontend specialist agent for React application development"""
    
    def __init__(self, logger: Optional[ReasoningLogger] = None):
        self.logger = logger or get_logger()
        self.reasoning_context = []
        
    def create_react_app(self, config: FrontendConfig, output_dir: str = "./frontend"):
        """Create a complete React application with TypeScript and Tailwind"""
        
        self.logger.log_agent_start(
            "frontend-specialist",
            json.dumps({"config": config.__dict__}),
            "Creating React application with full stack integration"
        )
        
        output_path = Path(output_dir)
        
        # Step 1: Create project structure
        self._create_project_structure(output_path, config)
        
        # Step 2: Generate package.json
        self._generate_package_json(output_path, config)
        
        # Step 3: Set up Vite configuration
        self._setup_vite_config(output_path, config)
        
        # Step 4: Configure Tailwind CSS
        self._setup_tailwind(output_path)
        
        # Step 5: Create API client
        self._generate_api_client(output_path, config)
        
        # Step 6: Set up authentication
        if config.auth_enabled:
            self._setup_authentication(output_path, config)
        
        # Step 7: Generate components for resources
        for resource in config.resources:
            self._generate_resource_components(output_path, resource, config)
        
        # Step 8: Create main App component and routing
        self._setup_app_routing(output_path, config)
        
        # Step 9: Set up state management
        self._setup_state_management(output_path, config)
        
        # Step 10: Create common components
        self._create_common_components(output_path, config)
        
        self.logger.log_agent_complete(
            "frontend-specialist",
            True,
            f"React application created successfully at {output_path}"
        )
        
        return True
    
    def _create_project_structure(self, output_path: Path, config: FrontendConfig):
        """Create the directory structure for the React app"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "create_structure",
            {"path": str(output_path)},
            "Creating React project directory structure"
        )
        
        directories = [
            "src/api",
            "src/components/common",
            "src/components/forms",
            "src/components/layout",
            "src/features/auth",
            "src/hooks",
            "src/stores",
            "src/utils",
            "src/types",
            "public"
        ]
        
        # Add feature directories for each resource
        for resource in config.resources:
            resource_name = resource.get("name", "").lower()
            if resource_name:
                directories.append(f"src/features/{resource_name}")
        
        for dir_path in directories:
            (output_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    def _generate_package_json(self, output_path: Path, config: FrontendConfig):
        """Generate package.json with all dependencies"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "generate_package_json",
            {"project": config.project_name},
            "Creating package.json with dependencies"
        )
        
        package_json = {
            "name": config.project_name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
                "preview": "vite preview",
                "test": "jest",
                "test:watch": "jest --watch"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "axios": "^1.6.2",
                "zustand": "^4.4.7",
                "@tanstack/react-query": "^5.12.0",
                "react-hook-form": "^7.48.0",
                "zod": "^3.22.4",
                "@hookform/resolvers": "^3.3.2",
                "react-hot-toast": "^2.4.1",
                "clsx": "^2.0.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.43",
                "@types/react-dom": "^18.2.17",
                "@typescript-eslint/eslint-plugin": "^6.14.0",
                "@typescript-eslint/parser": "^6.14.0",
                "@vitejs/plugin-react": "^4.2.1",
                "autoprefixer": "^10.4.16",
                "eslint": "^8.55.0",
                "eslint-plugin-react-hooks": "^4.6.0",
                "eslint-plugin-react-refresh": "^0.4.5",
                "postcss": "^8.4.32",
                "tailwindcss": "^3.3.6",
                "typescript": "^5.2.2",
                "vite": "^5.0.8"
            }
        }
        
        with open(output_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    def _setup_vite_config(self, output_path: Path, config: FrontendConfig):
        """Create Vite configuration"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "setup_vite",
            {},
            "Configuring Vite build tool"
        )
        
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: '""" + config.api_base_url + """',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
})
"""
        
        with open(output_path / "vite.config.ts", "w") as f:
            f.write(vite_config)
        
        # Create TypeScript config
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        
        with open(output_path / "tsconfig.json", "w") as f:
            json.dump(tsconfig, f, indent=2)
        
        # Create node TypeScript config
        tsconfig_node = {
            "compilerOptions": {
                "composite": True,
                "skipLibCheck": True,
                "module": "ESNext",
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True
            },
            "include": ["vite.config.ts"]
        }
        
        with open(output_path / "tsconfig.node.json", "w") as f:
            json.dump(tsconfig_node, f, indent=2)
    
    def _setup_tailwind(self, output_path: Path):
        """Configure Tailwind CSS"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "setup_tailwind",
            {},
            "Configuring Tailwind CSS for styling"
        )
        
        # Tailwind config
        tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
"""
        
        with open(output_path / "tailwind.config.js", "w") as f:
            f.write(tailwind_config)
        
        # PostCSS config
        postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        
        with open(output_path / "postcss.config.js", "w") as f:
            f.write(postcss_config)
        
        # Main CSS file
        main_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 text-gray-900;
  }
}

@layer components {
  .btn-primary {
    @apply bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors;
  }
  
  .btn-secondary {
    @apply bg-gray-200 text-gray-900 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors;
  }
  
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}
"""
        
        with open(output_path / "src/index.css", "w") as f:
            f.write(main_css)
    
    def _generate_api_client(self, output_path: Path, config: FrontendConfig):
        """Generate typed API client"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "generate_api_client",
            {"resources": len(config.resources)},
            "Generating typed API client from backend routes"
        )
        
        # Base API client
        api_client = """import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getAuthToken, refreshAuthToken, clearAuth } from './auth';

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '""" + config.api_base_url + """';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const newToken = await refreshAuthToken();
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            clearAuth();
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client(config);
    return response.data;
  }

  // CRUD operations
  async get<T>(url: string, params?: any): Promise<T> {
    return this.request<T>({ method: 'GET', url, params });
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'POST', url, data });
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PATCH', url, data });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
"""
        
        with open(output_path / "src/api/client.ts", "w") as f:
            f.write(api_client)
        
        # Generate resource-specific API methods
        for resource in config.resources:
            self._generate_resource_api(output_path, resource)
    
    def _generate_resource_api(self, output_path: Path, resource: Dict[str, Any]):
        """Generate API methods for a specific resource"""
        
        name = resource.get("name", "Resource")
        plural = resource.get("plural", name + "s")
        fields = resource.get("fields", [])
        
        # Generate TypeScript interfaces
        interface_content = f"""import {{ apiClient }} from './client';

// {name} interfaces
export interface {name} {{
  id: string;
"""
        
        for field in fields:
            field_name = field.get("name", "field")
            field_type = self._map_field_type(field.get("type", "string"))
            required = field.get("required", True)
            interface_content += f"  {field_name}{'?' if not required else ''}: {field_type};\n"
        
        interface_content += f"""  createdAt: string;
  updatedAt: string;
}}

export interface Create{name}DTO {{
"""
        
        for field in fields:
            if not field.get("readonly", False):
                field_name = field.get("name", "field")
                field_type = self._map_field_type(field.get("type", "string"))
                required = field.get("required", True)
                interface_content += f"  {field_name}{'?' if not required else ''}: {field_type};\n"
        
        interface_content += f"""}}

export interface Update{name}DTO extends Partial<Create{name}DTO> {{}}

export interface {name}QueryParams {{
  page?: number;
  limit?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}}

export interface {name}ListResponse {{
  data: {name}[];
  total: number;
  page: number;
  limit: number;
}}

// {name} API methods
export const {name.lower()}Api = {{
  list: async (params?: {name}QueryParams): Promise<{name}ListResponse> => {{
    return apiClient.get('/api/{plural.lower()}', params);
  }},

  get: async (id: string): Promise<{name}> => {{
    return apiClient.get(`/api/{plural.lower()}/${{id}}`);
  }},

  create: async (data: Create{name}DTO): Promise<{name}> => {{
    return apiClient.post('/api/{plural.lower()}', data);
  }},

  update: async (id: string, data: Update{name}DTO): Promise<{name}> => {{
    return apiClient.put(`/api/{plural.lower()}/${{id}}`, data);
  }},

  delete: async (id: string): Promise<void> => {{
    return apiClient.delete(`/api/{plural.lower()}/${{id}}`);
  }},
}};
"""
        
        api_file = output_path / f"src/api/{name.lower()}.ts"
        with open(api_file, "w") as f:
            f.write(interface_content)
    
    def _setup_authentication(self, output_path: Path, config: FrontendConfig):
        """Set up authentication flow with JWT"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "setup_authentication",
            {},
            "Implementing JWT authentication flow"
        )
        
        # Auth utilities
        auth_utils = """import apiClient from './client';

const TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// Token management
export const getAuthToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setAuthData = (data: AuthResponse): void => {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
};

export const clearAuth = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const getCurrentUser = (): User | null => {
  const userData = localStorage.getItem(USER_KEY);
  return userData ? JSON.parse(userData) : null;
};

// Auth API methods
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', credentials);
    setAuthData(response);
    return response;
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/auth/register', data);
    setAuthData(response);
    return response;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/api/auth/logout');
    } finally {
      clearAuth();
    }
  },

  refresh: async (): Promise<string | null> => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/refresh', {
        refresh_token: refreshToken,
      });
      setAuthData(response);
      return response.access_token;
    } catch (error) {
      clearAuth();
      return null;
    }
  },

  me: async (): Promise<User> => {
    return apiClient.get<User>('/api/auth/me');
  },
};

export const refreshAuthToken = authApi.refresh;
"""
        
        with open(output_path / "src/api/auth.ts", "w") as f:
            f.write(auth_utils)
        
        # Create auth store with Zustand
        auth_store = """import { create } from 'zustand';
import { authApi, User, LoginCredentials, RegisterData, clearAuth } from '@/api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login(credentials);
      set({ 
        user: response.user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || 'Login failed', 
        isLoading: false 
      });
      throw error;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.register(data);
      set({ 
        user: response.user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.message || 'Registration failed', 
        isLoading: false 
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      });
    }
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const user = await authApi.me();
      set({ 
        user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch {
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false 
      });
    }
  },

  clearError: () => set({ error: null }),
}));
"""
        
        with open(output_path / "src/stores/authStore.ts", "w") as f:
            f.write(auth_store)
        
        # Create auth components
        self._create_auth_components(output_path)
    
    def _create_auth_components(self, output_path: Path):
        """Create authentication UI components"""
        
        # Login component
        login_component = """import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import toast from 'react-hot-toast';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginForm: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Login failed. Please check your credentials.');
    }
  };

  React.useEffect(() => {
    return () => clearError();
  }, [clearError]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="card w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">Login</h2>
        
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              {...register('email')}
              type="email"
              className="input-field"
              placeholder="you@example.com"
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              {...register('password')}
              type="password"
              className="input-field"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full disabled:opacity-50"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <p className="text-center mt-4 text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary-600 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
};
"""
        
        with open(output_path / "src/features/auth/LoginForm.tsx", "w") as f:
            f.write(login_component)
        
        # Register component
        register_component = """import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import toast from 'react-hot-toast';

const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export const RegisterForm: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data);
      toast.success('Registration successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Registration failed. Please try again.');
    }
  };

  React.useEffect(() => {
    return () => clearError();
  }, [clearError]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="card w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">Create Account</h2>
        
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              {...register('name')}
              type="text"
              className="input-field"
              placeholder="John Doe"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              {...register('email')}
              type="email"
              className="input-field"
              placeholder="you@example.com"
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              {...register('password')}
              type="password"
              className="input-field"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Confirm Password</label>
            <input
              {...register('confirmPassword')}
              type="password"
              className="input-field"
              placeholder="••••••••"
            />
            {errors.confirmPassword && (
              <p className="text-red-500 text-sm mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full disabled:opacity-50"
          >
            {isLoading ? 'Creating account...' : 'Register'}
          </button>
        </form>
        
        <p className="text-center mt-4 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 hover:underline">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
};
"""
        
        with open(output_path / "src/features/auth/RegisterForm.tsx", "w") as f:
            f.write(register_component)
    
    def _generate_resource_components(self, output_path: Path, resource: Dict[str, Any], config: FrontendConfig):
        """Generate CRUD components for a resource"""
        
        name = resource.get("name", "Resource")
        plural = resource.get("plural", name + "s")
        fields = resource.get("fields", [])
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "generate_components",
            {"resource": name},
            f"Creating CRUD components for {name}"
        )
        
        # Create list component
        self._create_list_component(output_path, name, plural, fields)
        
        # Create form component
        self._create_form_component(output_path, name, fields)
        
        # Create detail component
        self._create_detail_component(output_path, name, fields)
    
    def _create_list_component(self, output_path: Path, name: str, plural: str, fields: List[Dict]):
        """Create list component for a resource"""
        
        list_component = f"""import React from 'react';
import {{ useQuery, useMutation, useQueryClient }} from '@tanstack/react-query';
import {{ Link }} from 'react-router-dom';
import {{ {name.lower()}Api, {name} }} from '@/api/{name.lower()}';
import toast from 'react-hot-toast';

export const {name}List: React.FC = () => {{
  const queryClient = useQueryClient();
  
  const {{ data, isLoading, error }} = useQuery({{
    queryKey: ['{plural.lower()}'],
    queryFn: () => {name.lower()}Api.list(),
  }});
  
  const deleteMutation = useMutation({{
    mutationFn: {name.lower()}Api.delete,
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: ['{plural.lower()}'] }});
      toast.success('{name} deleted successfully');
    }},
    onError: () => {{
      toast.error('Failed to delete {name.lower()}');
    }},
  }});
  
  const handleDelete = (id: string) => {{
    if (confirm('Are you sure you want to delete this {name.lower()}?')) {{
      deleteMutation.mutate(id);
    }}
  }};
  
  if (isLoading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-600">Error loading {plural.lower()}</div>;
  
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">{plural}</h1>
        <Link to="/{plural.lower()}/new" className="btn-primary">
          Add {name}
        </Link>
      </div>
      
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
"""
        
        # Add table headers for first 3 fields
        display_fields = fields[:3] if len(fields) > 3 else fields
        for field in display_fields:
            field_name = field.get("name", "field")
            list_component += f"""              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {field_name.replace('_', ' ').title()}
              </th>
"""
        
        list_component += f"""              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {{data?.data.map((item: {name}) => (
              <tr key={{item.id}} className="hover:bg-gray-50">
"""
        
        # Add table cells for fields
        for field in display_fields:
            field_name = field.get("name", "field")
            list_component += f"""                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{item.{field_name}}}
                </td>
"""
        
        list_component += f"""                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <Link
                    to={{`/{plural.lower()}/${{item.id}}`}}
                    className="text-primary-600 hover:text-primary-900 mr-4"
                  >
                    View
                  </Link>
                  <Link
                    to={{`/{plural.lower()}/${{item.id}}/edit`}}
                    className="text-primary-600 hover:text-primary-900 mr-4"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={{() => handleDelete(item.id)}}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}}
          </tbody>
        </table>
        
        {{data?.data.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No {plural.lower()} found. Create your first one!
          </div>
        )}}
      </div>
    </div>
  );
}};
"""
        
        list_file = output_path / f"src/features/{name.lower()}/{name}List.tsx"
        list_file.parent.mkdir(parents=True, exist_ok=True)
        with open(list_file, "w") as f:
            f.write(list_component)
    
    def _create_form_component(self, output_path: Path, name: str, fields: List[Dict]):
        """Create form component for a resource"""
        
        # Build schema
        schema_fields = []
        for field in fields:
            if not field.get("readonly", False):
                field_name = field.get("name", "field")
                field_type = field.get("type", "string")
                required = field.get("required", True)
                
                if field_type == "string":
                    validation = f"z.string()"
                    if required:
                        validation += f".min(1, '{field_name} is required')"
                elif field_type == "number":
                    validation = f"z.number()"
                elif field_type == "boolean":
                    validation = f"z.boolean()"
                else:
                    validation = f"z.any()"
                
                if not required:
                    validation += ".optional()"
                
                schema_fields.append(f"  {field_name}: {validation}")
        
        form_component = f"""import React from 'react';
import {{ useForm }} from 'react-hook-form';
import {{ zodResolver }} from '@hookform/resolvers/zod';
import {{ z }} from 'zod';
import {{ useNavigate, useParams }} from 'react-router-dom';
import {{ useMutation, useQuery, useQueryClient }} from '@tanstack/react-query';
import {{ {name.lower()}Api, Create{name}DTO, Update{name}DTO }} from '@/api/{name.lower()}';
import toast from 'react-hot-toast';

const {name.lower()}Schema = z.object({{
{','.join(schema_fields)},
}});

type {name}FormData = z.infer<typeof {name.lower()}Schema>;

export const {name}Form: React.FC = () => {{
  const navigate = useNavigate();
  const {{ id }} = useParams();
  const queryClient = useQueryClient();
  const isEdit = !!id;
  
  const {{ data: existing{name}, isLoading: loadingExisting }} = useQuery({{
    queryKey: ['{name.lower()}', id],
    queryFn: () => {name.lower()}Api.get(id!),
    enabled: isEdit,
  }});
  
  const {{
    register,
    handleSubmit,
    formState: {{ errors, isSubmitting }},
    reset,
  }} = useForm<{name}FormData>({{
    resolver: zodResolver({name.lower()}Schema),
    defaultValues: existing{name} || {{}},
  }});
  
  React.useEffect(() => {{
    if (existing{name}) {{
      reset(existing{name});
    }}
  }}, [existing{name}, reset]);
  
  const createMutation = useMutation({{
    mutationFn: (data: Create{name}DTO) => {name.lower()}Api.create(data),
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: ['{name.lower()}s'] }});
      toast.success('{name} created successfully');
      navigate('/{name.lower()}s');
    }},
    onError: () => {{
      toast.error('Failed to create {name.lower()}');
    }},
  }});
  
  const updateMutation = useMutation({{
    mutationFn: (data: Update{name}DTO) => {name.lower()}Api.update(id!, data),
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: ['{name.lower()}s'] }});
      queryClient.invalidateQueries({{ queryKey: ['{name.lower()}', id] }});
      toast.success('{name} updated successfully');
      navigate('/{name.lower()}s');
    }},
    onError: () => {{
      toast.error('Failed to update {name.lower()}');
    }},
  }});
  
  const onSubmit = (data: {name}FormData) => {{
    if (isEdit) {{
      updateMutation.mutate(data);
    }} else {{
      createMutation.mutate(data);
    }}
  }};
  
  if (loadingExisting) return <div className="p-4">Loading...</div>;
  
  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">
        {{isEdit ? 'Edit' : 'Create'}} {name}
      </h1>
      
      <form onSubmit={{handleSubmit(onSubmit)}} className="card space-y-4">
"""
        
        # Add form fields
        for field in fields:
            if not field.get("readonly", False):
                field_name = field.get("name", "field")
                field_type = field.get("type", "string")
                required = field.get("required", True)
                
                input_type = "text"
                if field_type == "number":
                    input_type = "number"
                elif field_type == "boolean":
                    input_type = "checkbox"
                elif "email" in field_name:
                    input_type = "email"
                elif "password" in field_name:
                    input_type = "password"
                
                form_component += f"""        <div>
          <label className="block text-sm font-medium mb-1">
            {field_name.replace('_', ' ').title()}
            {' ' if required else ' (optional)'}
          </label>
"""
                
                if input_type == "checkbox":
                    form_component += f"""          <input
            {{...register('{field_name}')}}
            type="checkbox"
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
"""
                else:
                    form_component += f"""          <input
            {{...register('{field_name}')}}
            type="{input_type}"
            className="input-field"
            placeholder="Enter {field_name.replace('_', ' ')}"
          />
"""
                
                form_component += f"""          {{errors.{field_name} && (
            <p className="text-red-500 text-sm mt-1">{{errors.{field_name}.message}}</p>
          )}}
        </div>
"""
        
        form_component += f"""        
        <div className="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={{() => navigate('/{name.lower()}s')}}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={{isSubmitting}}
            className="btn-primary disabled:opacity-50"
          >
            {{isSubmitting ? 'Saving...' : isEdit ? 'Update' : 'Create'}}
          </button>
        </div>
      </form>
    </div>
  );
}};
"""
        
        form_file = output_path / f"src/features/{name.lower()}/{name}Form.tsx"
        with open(form_file, "w") as f:
            f.write(form_component)
    
    def _create_detail_component(self, output_path: Path, name: str, fields: List[Dict]):
        """Create detail/view component for a resource"""
        
        detail_component = f"""import React from 'react';
import {{ useParams, useNavigate, Link }} from 'react-router-dom';
import {{ useQuery }} from '@tanstack/react-query';
import {{ {name.lower()}Api }} from '@/api/{name.lower()}';

export const {name}Detail: React.FC = () => {{
  const {{ id }} = useParams();
  const navigate = useNavigate();
  
  const {{ data: {name.lower()}, isLoading, error }} = useQuery({{
    queryKey: ['{name.lower()}', id],
    queryFn: () => {name.lower()}Api.get(id!),
  }});
  
  if (isLoading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-600">Error loading {name.lower()}</div>;
  if (!{name.lower()}) return <div className="p-4">No {name.lower()} found</div>;
  
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">{name} Details</h1>
        <div className="space-x-2">
          <Link
            to={{`/{name.lower()}s/${{id}}/edit`}}
            className="btn-primary"
          >
            Edit
          </Link>
          <button
            onClick={{() => navigate('/{name.lower()}s')}}
            className="btn-secondary"
          >
            Back to List
          </button>
        </div>
      </div>
      
      <div className="card">
        <dl className="divide-y divide-gray-200">
"""
        
        # Add field displays
        for field in fields:
            field_name = field.get("name", "field")
            detail_component += f"""          <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
            <dt className="text-sm font-medium text-gray-500">
              {field_name.replace('_', ' ').title()}
            </dt>
            <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">
              {{{name.lower()}.{field_name} || 'N/A'}}
            </dd>
          </div>
"""
        
        detail_component += f"""        </dl>
      </div>
    </div>
  );
}};
"""
        
        detail_file = output_path / f"src/features/{name.lower()}/{name}Detail.tsx"
        with open(detail_file, "w") as f:
            f.write(detail_component)
    
    def _setup_app_routing(self, output_path: Path, config: FrontendConfig):
        """Set up main App component with routing"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "setup_routing",
            {},
            "Configuring React Router and main App component"
        )
        
        # Generate route imports
        route_imports = []
        routes = []
        
        if config.auth_enabled:
            route_imports.append("import { LoginForm } from './features/auth/LoginForm';")
            route_imports.append("import { RegisterForm } from './features/auth/RegisterForm';")
            routes.append("          <Route path='/login' element={<LoginForm />} />")
            routes.append("          <Route path='/register' element={<RegisterForm />} />")
        
        for resource in config.resources:
            name = resource.get("name", "Resource")
            plural = resource.get("plural", name + "s")
            route_imports.append(f"import {{ {name}List }} from './features/{name.lower()}/{name}List';")
            route_imports.append(f"import {{ {name}Form }} from './features/{name.lower()}/{name}Form';")
            route_imports.append(f"import {{ {name}Detail }} from './features/{name.lower()}/{name}Detail';")
            
            routes.append(f"          <Route path='/{plural.lower()}' element={{<{name}List />}} />")
            routes.append(f"          <Route path='/{plural.lower()}/new' element={{<{name}Form />}} />")
            routes.append(f"          <Route path='/{plural.lower()}/:id' element={{<{name}Detail />}} />")
            routes.append(f"          <Route path='/{plural.lower()}/:id/edit' element={{<{name}Form />}} />")
        
        app_component = """import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/layout/Layout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Dashboard } from './features/dashboard/Dashboard';
""" + "\n".join(route_imports) + """

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          {/* Public routes */}
""" + ("\n".join(routes[:2]) if config.auth_enabled else '') + """
          
          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path='/' element={<Navigate to='/dashboard' replace />} />
              <Route path='/dashboard' element={<Dashboard />} />
""" + ("\n".join(routes[2:]) if routes else '') + """
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
"""
        
        with open(output_path / "src/App.tsx", "w") as f:
            f.write(app_component)
        
        # Create main.tsx entry point
        main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
        
        with open(output_path / "src/main.tsx", "w") as f:
            f.write(main_tsx)
        
        # Create index.html
        index_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{config.project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        
        with open(output_path / "index.html", "w") as f:
            f.write(index_html)
    
    def _setup_state_management(self, output_path: Path, config: FrontendConfig):
        """Set up Zustand stores and React Query hooks"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "setup_state",
            {},
            "Configuring state management with Zustand and React Query"
        )
        
        # Create a global app store
        app_store = """import { create } from 'zustand';

interface AppState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Notification[];
  
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: Date;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  notifications: [],
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  setTheme: (theme) => {
    set({ theme });
    document.documentElement.classList.toggle('dark', theme === 'dark');
  },
  
  addNotification: (notification) => 
    set((state) => ({ 
      notifications: [...state.notifications, notification] 
    })),
  
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id)
    })),
}));
"""
        
        with open(output_path / "src/stores/appStore.ts", "w") as f:
            f.write(app_store)
        
        # Create custom hooks
        use_api_hook = """import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

// Generic error handler
export const handleApiError = (error: unknown) => {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.message || error.message;
    toast.error(message);
  } else {
    toast.error('An unexpected error occurred');
  }
};

// Custom hook for API queries with error handling
export function useApiQuery<TData = unknown>(
  queryKey: any[],
  queryFn: () => Promise<TData>,
  options?: UseQueryOptions<TData, AxiosError>
) {
  return useQuery({
    queryKey,
    queryFn,
    ...options,
  });
}

// Custom hook for API mutations with automatic error handling
export function useApiMutation<TData = unknown, TVariables = unknown>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: UseMutationOptions<TData, AxiosError, TVariables>
) {
  return useMutation({
    mutationFn,
    onError: handleApiError,
    ...options,
  });
}
"""
        
        with open(output_path / "src/hooks/useApi.ts", "w") as f:
            f.write(use_api_hook)
    
    def _create_common_components(self, output_path: Path, config: FrontendConfig):
        """Create common UI components"""
        
        self.logger.log_tool_call(
            "frontend-specialist",
            "create_components",
            {},
            "Creating common UI components and layout"
        )
        
        # Create Layout component
        layout_component = """import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useAppStore } from '@/stores/appStore';

export const Layout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useAppStore();
  
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-md hover:bg-gray-100"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="ml-4 text-xl font-semibold">Dashboard</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.name || 'User'}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 overflow-hidden bg-white shadow-md`}>
          <nav className="mt-5 px-2">
            <Link
              to="/dashboard"
              className="group flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-100"
            >
              Dashboard
            </Link>
            {/* Add navigation links for resources */}
""" + "\n".join([f"""            <Link
              to="/{resource.get('plural', resource.get('name', 'Resource') + 's').lower()}"
              className="group flex items-center px-2 py-2 text-sm font-medium rounded-md hover:bg-gray-100"
            >
              {resource.get('plural', resource.get('name', 'Resource') + 's')}
            </Link>""" for resource in config.resources]) + """
          </nav>
        </aside>
        
        {/* Main content */}
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
"""
        
        with open(output_path / "src/components/layout/Layout.tsx", "w") as f:
            f.write(layout_component)
        
        # Create ProtectedRoute component
        protected_route = """import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  React.useEffect(() => {
    const checkAuth = async () => {
      const store = useAuthStore.getState();
      await store.checkAuth();
    };
    checkAuth();
  }, []);
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }
  
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};
"""
        
        protected_route_file = output_path / "src/components/auth/ProtectedRoute.tsx"
        protected_route_file.parent.mkdir(parents=True, exist_ok=True)
        with open(protected_route_file, "w") as f:
            f.write(protected_route)
        
        # Create Dashboard component
        dashboard_component = """import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';

export const Dashboard: React.FC = () => {
  // You can add dashboard-specific queries here
  
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-2">Welcome</h3>
          <p className="text-gray-600">
            This is your application dashboard. Navigate using the sidebar to manage your resources.
          </p>
        </div>
        
        {/* Add more dashboard widgets here */}
      </div>
    </div>
  );
};
"""
        
        dashboard_file = output_path / "src/features/dashboard/Dashboard.tsx"
        dashboard_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dashboard_file, "w") as f:
            f.write(dashboard_component)
        
        # Create environment file template
        env_template = f"""# API Configuration
VITE_API_URL={config.api_base_url}

# Feature Flags
VITE_ENABLE_AUTH=true
VITE_ENABLE_ANALYTICS=false

# App Configuration
VITE_APP_NAME={config.project_name}
"""
        
        with open(output_path / ".env.example", "w") as f:
            f.write(env_template)
    
    def _map_field_type(self, field_type: str) -> str:
        """Map field types to TypeScript types"""
        type_mapping = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "date": "string",
            "datetime": "string",
            "array": "any[]",
            "object": "Record<string, any>"
        }
        return type_mapping.get(field_type, "any")

# CLI Interface
def main():
    parser = argparse.ArgumentParser(
        description="Frontend Specialist Agent - Create React applications with full stack integration"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration JSON file",
        default=None
    )
    parser.add_argument(
        "--project-name",
        type=str,
        help="Project name",
        default="React App"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="Backend API URL",
        default="http://localhost:8000"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for the React app",
        default="./frontend"
    )
    parser.add_argument(
        "--resources",
        type=str,
        help="JSON string of resources to generate",
        default="[]"
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication features"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            config = FrontendConfig(**config_data)
    else:
        # Parse resources if provided
        resources = []
        if args.resources:
            try:
                resources = json.loads(args.resources)
            except json.JSONDecodeError:
                print("Error: Invalid JSON for resources")
                sys.exit(1)
        
        config = FrontendConfig(
            project_name=args.project_name,
            api_base_url=args.api_url,
            auth_enabled=not args.no_auth,
            resources=resources
        )
    
    # Initialize specialist
    specialist = FrontendSpecialist()
    
    # Create the React application
    try:
        success = specialist.create_react_app(config, args.output)
        
        if success:
            print(f"\n✅ React application created successfully at {args.output}")
            print("\n📦 Next steps:")
            print(f"  1. cd {args.output}")
            print("  2. npm install")
            print("  3. npm run dev")
            print("\n🚀 Your React app will be available at http://localhost:5173")
        else:
            print("\n❌ Failed to create React application")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()