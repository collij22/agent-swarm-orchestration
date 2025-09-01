import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  User,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  TokenResponse,
  Product,
  CreateProductData,
  UpdateProductData,
  Category,
  CartItem,
  AddToCartData,
  UpdateCartItemData,
  Order,
  CreateOrderData,
  PaymentIntent,
  CreatePaymentData,
  PaginatedResponse,
  ProductFilters,
  QueryParams,
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Try to refresh token
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.auth.refresh();
              localStorage.setItem('token', response.access_token);
              
              // Retry original request
              const originalRequest = error.config;
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
              return this.client.request(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  auth = {
    login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await this.client.post<AuthResponse>('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    },

    register: async (data: RegisterData): Promise<User> => {
      const response = await this.client.post<User>('/api/auth/register', data);
      return response.data;
    },

    refresh: async (): Promise<TokenResponse> => {
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await this.client.post<TokenResponse>('/api/auth/refresh', {
        refresh_token: refreshToken,
      });
      return response.data;
    },

    me: async (): Promise<User> => {
      const response = await this.client.get<User>('/api/auth/me');
      return response.data;
    },
  };

  // Product endpoints
  products = {
    list: async (filters?: ProductFilters, params?: QueryParams): Promise<PaginatedResponse<Product>> => {
      const response = await this.client.get<PaginatedResponse<Product>>('/api/products', {
        params: { ...filters, ...params },
      });
      return response.data;
    },

    get: async (id: string): Promise<Product> => {
      const response = await this.client.get<Product>(`/api/products/${id}`);
      return response.data;
    },

    create: async (data: CreateProductData): Promise<Product> => {
      const response = await this.client.post<Product>('/api/products', data);
      return response.data;
    },

    update: async (id: string, data: UpdateProductData): Promise<Product> => {
      const response = await this.client.put<Product>(`/api/products/${id}`, data);
      return response.data;
    },

    delete: async (id: string): Promise<void> => {
      await this.client.delete(`/api/products/${id}`);
    },

    search: async (query: string, params?: QueryParams): Promise<PaginatedResponse<Product>> => {
      const response = await this.client.get<PaginatedResponse<Product>>('/api/products/search', {
        params: { q: query, ...params },
      });
      return response.data;
    },
  };

  // Category endpoints
  categories = {
    list: async (): Promise<Category[]> => {
      const response = await this.client.get<Category[]>('/api/categories');
      return response.data;
    },

    get: async (id: string): Promise<Category> => {
      const response = await this.client.get<Category>(`/api/categories/${id}`);
      return response.data;
    },

    create: async (data: Omit<Category, 'id' | 'created_at' | 'updated_at'>): Promise<Category> => {
      const response = await this.client.post<Category>('/api/categories', data);
      return response.data;
    },

    update: async (id: string, data: Partial<Category>): Promise<Category> => {
      const response = await this.client.put<Category>(`/api/categories/${id}`, data);
      return response.data;
    },

    delete: async (id: string): Promise<void> => {
      await this.client.delete(`/api/categories/${id}`);
    },
  };

  // Cart endpoints
  cart = {
    list: async (): Promise<CartItem[]> => {
      const response = await this.client.get<CartItem[]>('/api/cart');
      return response.data;
    },

    add: async (data: AddToCartData): Promise<CartItem> => {
      const response = await this.client.post<CartItem>('/api/cart', data);
      return response.data;
    },

    update: async (itemId: string, data: UpdateCartItemData): Promise<CartItem> => {
      const response = await this.client.put<CartItem>(`/api/cart/${itemId}`, data);
      return response.data;
    },

    remove: async (itemId: string): Promise<void> => {
      await this.client.delete(`/api/cart/${itemId}`);
    },

    clear: async (): Promise<void> => {
      await this.client.delete('/api/cart');
    },
  };

  // Order endpoints
  orders = {
    list: async (params?: QueryParams): Promise<PaginatedResponse<Order>> => {
      const response = await this.client.get<PaginatedResponse<Order>>('/api/orders', {
        params,
      });
      return response.data;
    },

    get: async (id: string): Promise<Order> => {
      const response = await this.client.get<Order>(`/api/orders/${id}`);
      return response.data;
    },

    create: async (data: CreateOrderData): Promise<Order> => {
      const response = await this.client.post<Order>('/api/orders', data);
      return response.data;
    },

    updateStatus: async (id: string, status: string): Promise<Order> => {
      const response = await this.client.patch<Order>(`/api/orders/${id}/status`, { status });
      return response.data;
    },
  };

  // Payment endpoints
  payments = {
    createIntent: async (data: CreatePaymentData): Promise<PaymentIntent> => {
      const response = await this.client.post<PaymentIntent>('/api/payments/create-intent', data);
      return response.data;
    },

    confirmPayment: async (paymentIntentId: string): Promise<{ success: boolean }> => {
      const response = await this.client.post<{ success: boolean }>('/api/payments/confirm', {
        payment_intent_id: paymentIntentId,
      });
      return response.data;
    },
  };

  // Admin endpoints
  admin = {
    users: {
      list: async (params?: QueryParams): Promise<PaginatedResponse<User>> => {
        const response = await this.client.get<PaginatedResponse<User>>('/api/admin/users', {
          params,
        });
        return response.data;
      },

      update: async (id: string, data: Partial<User>): Promise<User> => {
        const response = await this.client.put<User>(`/api/admin/users/${id}`, data);
        return response.data;
      },

      delete: async (id: string): Promise<void> => {
        await this.client.delete(`/api/admin/users/${id}`);
      },
    },

    orders: {
      list: async (params?: QueryParams): Promise<PaginatedResponse<Order>> => {
        const response = await this.client.get<PaginatedResponse<Order>>('/api/admin/orders', {
          params,
        });
        return response.data;
      },

      updateStatus: async (id: string, status: string): Promise<Order> => {
        const response = await this.client.patch<Order>(`/api/admin/orders/${id}/status`, { status });
        return response.data;
      },
    },

    analytics: {
      dashboard: async (): Promise<{
        totalUsers: number;
        totalOrders: number;
        totalRevenue: number;
        recentOrders: Order[];
      }> => {
        const response = await this.client.get('/api/admin/analytics/dashboard');
        return response.data;
      },
    },
  };
}

export const apiClient = new ApiClient();