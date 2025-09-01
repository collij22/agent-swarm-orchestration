import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import {
  User,
  UserCreate,
  UserLogin,
  AuthResponse,
  Product,
  ProductCreate,
  ProductUpdate,
  ProductFilters,
  Category,
  CategoryCreate,
  CartItem,
  CartItemCreate,
  CartItemUpdate,
  Order,
  OrderCreate,
  OrderFilters,
  PaymentIntent,
  PaymentIntentCreate,
  PaginatedResponse,
  ApiError,
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
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
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.auth.refresh(refreshToken);
              localStorage.setItem('token', response.access_token);
              localStorage.setItem('refresh_token', response.refresh_token);
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.auth.logout();
          }
        }

        // Show error toast
        const message = error.response?.data?.detail || 'An error occurred';
        toast.error(message);
        
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  auth = {
    login: async (credentials: UserLogin): Promise<AuthResponse> => {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await this.client.post<AuthResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    },

    register: async (userData: UserCreate): Promise<User> => {
      const response = await this.client.post<User>('/auth/register', userData);
      return response.data;
    },

    refresh: async (refreshToken: string): Promise<AuthResponse> => {
      const response = await this.client.post<AuthResponse>('/auth/refresh', {
        refresh_token: refreshToken,
      });
      return response.data;
    },

    me: async (): Promise<User> => {
      const response = await this.client.get<User>('/auth/me');
      return response.data;
    },

    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    },
  };

  // Product endpoints
  products = {
    list: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
      const response = await this.client.get<PaginatedResponse<Product>>('/products', {
        params: filters,
      });
      return response.data;
    },

    get: async (id: string): Promise<Product> => {
      const response = await this.client.get<Product>(`/products/${id}`);
      return response.data;
    },

    create: async (productData: ProductCreate): Promise<Product> => {
      const response = await this.client.post<Product>('/products', productData);
      return response.data;
    },

    update: async (id: string, productData: ProductUpdate): Promise<Product> => {
      const response = await this.client.put<Product>(`/products/${id}`, productData);
      return response.data;
    },

    delete: async (id: string): Promise<void> => {
      await this.client.delete(`/products/${id}`);
    },

    search: async (query: string): Promise<Product[]> => {
      const response = await this.client.get<Product[]>('/products/search', {
        params: { q: query },
      });
      return response.data;
    },
  };

  // Category endpoints
  categories = {
    list: async (): Promise<Category[]> => {
      const response = await this.client.get<Category[]>('/categories');
      return response.data;
    },

    get: async (id: string): Promise<Category> => {
      const response = await this.client.get<Category>(`/categories/${id}`);
      return response.data;
    },

    create: async (categoryData: CategoryCreate): Promise<Category> => {
      const response = await this.client.post<Category>('/categories', categoryData);
      return response.data;
    },

    update: async (id: string, categoryData: CategoryCreate): Promise<Category> => {
      const response = await this.client.put<Category>(`/categories/${id}`, categoryData);
      return response.data;
    },

    delete: async (id: string): Promise<void> => {
      await this.client.delete(`/categories/${id}`);
    },
  };

  // Cart endpoints
  cart = {
    list: async (): Promise<CartItem[]> => {
      const response = await this.client.get<CartItem[]>('/cart');
      return response.data;
    },

    add: async (item: CartItemCreate): Promise<CartItem> => {
      const response = await this.client.post<CartItem>('/cart', item);
      return response.data;
    },

    update: async (id: string, item: CartItemUpdate): Promise<CartItem> => {
      const response = await this.client.put<CartItem>(`/cart/${id}`, item);
      return response.data;
    },

    remove: async (id: string): Promise<void> => {
      await this.client.delete(`/cart/${id}`);
    },

    clear: async (): Promise<void> => {
      await this.client.delete('/cart');
    },

    getTotal: async (): Promise<{ total: number; count: number }> => {
      const response = await this.client.get<{ total: number; count: number }>('/cart/total');
      return response.data;
    },
  };

  // Order endpoints
  orders = {
    list: async (filters?: OrderFilters): Promise<PaginatedResponse<Order>> => {
      const response = await this.client.get<PaginatedResponse<Order>>('/orders', {
        params: filters,
      });
      return response.data;
    },

    get: async (id: string): Promise<Order> => {
      const response = await this.client.get<Order>(`/orders/${id}`);
      return response.data;
    },

    create: async (orderData: OrderCreate): Promise<Order> => {
      const response = await this.client.post<Order>('/orders', orderData);
      return response.data;
    },

    updateStatus: async (id: string, status: string): Promise<Order> => {
      const response = await this.client.patch<Order>(`/orders/${id}/status`, { status });
      return response.data;
    },
  };

  // Payment endpoints
  payments = {
    createIntent: async (data: PaymentIntentCreate): Promise<PaymentIntent> => {
      const response = await this.client.post<PaymentIntent>('/payments/create-intent', data);
      return response.data;
    },

    confirmPayment: async (paymentIntentId: string): Promise<{ success: boolean }> => {
      const response = await this.client.post<{ success: boolean }>('/payments/confirm', {
        payment_intent_id: paymentIntentId,
      });
      return response.data;
    },
  };

  // Admin endpoints
  admin = {
    users: {
      list: async (): Promise<User[]> => {
        const response = await this.client.get<User[]>('/admin/users');
        return response.data;
      },
      
      updateRole: async (userId: string, isAdmin: boolean): Promise<User> => {
        const response = await this.client.patch<User>(`/admin/users/${userId}/role`, {
          is_admin: isAdmin,
        });
        return response.data;
      },
    },

    analytics: {
      dashboard: async (): Promise<{
        total_orders: number;
        total_revenue: number;
        total_products: number;
        total_users: number;
        recent_orders: Order[];
        top_products: Product[];
      }> => {
        const response = await this.client.get('/admin/analytics/dashboard');
        return response.data;
      },
    },
  };
}

export const apiClient = new ApiClient();
export default apiClient;