// User types
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

// Product types
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category_id: string;
  image_url?: string;
  stock_quantity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  category?: Category;
}

export interface ProductCreate {
  name: string;
  description: string;
  price: number;
  category_id: string;
  image_url?: string;
  stock_quantity: number;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  price?: number;
  category_id?: string;
  image_url?: string;
  stock_quantity?: number;
  is_active?: boolean;
}

// Category types
export interface Category {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
}

// Cart types
export interface CartItem {
  id: string;
  user_id: string;
  product_id: string;
  quantity: number;
  created_at: string;
  product?: Product;
}

export interface CartItemCreate {
  product_id: string;
  quantity: number;
}

export interface CartItemUpdate {
  quantity: number;
}

// Order types
export interface Order {
  id: string;
  user_id: string;
  status: OrderStatus;
  total_amount: number;
  shipping_address: string;
  payment_intent_id?: string;
  created_at: string;
  updated_at: string;
  items?: OrderItem[];
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  quantity: number;
  price: number;
  product?: Product;
}

export interface OrderCreate {
  shipping_address: string;
  items: Array<{
    product_id: string;
    quantity: number;
    price: number;
  }>;
}

export enum OrderStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled'
}

// Auth types
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface TokenRefresh {
  refresh_token: string;
}

// Payment types
export interface PaymentIntent {
  client_secret: string;
  payment_intent_id: string;
}

export interface PaymentIntentCreate {
  amount: number;
  order_id: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Query params
export interface ProductFilters {
  category_id?: string;
  search?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  page?: number;
  size?: number;
}

export interface OrderFilters {
  status?: OrderStatus;
  page?: number;
  size?: number;
}

// Error types
export interface ApiError {
  detail: string;
  status_code: number;
}