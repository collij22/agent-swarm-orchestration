// User and Authentication Types
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

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Product Types
export interface Category {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category_id: string;
  category?: Category;
  image_url?: string;
  stock_quantity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateProductData {
  name: string;
  description: string;
  price: number;
  category_id: string;
  stock_quantity: number;
  image_url?: string;
}

export interface UpdateProductData extends Partial<CreateProductData> {}

// Cart Types
export interface CartItem {
  id: string;
  product_id: string;
  product: Product;
  quantity: number;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface AddToCartData {
  product_id: string;
  quantity: number;
}

export interface UpdateCartItemData {
  quantity: number;
}

// Order Types
export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled'
}

export interface OrderItem {
  id: string;
  product_id: string;
  product: Product;
  quantity: number;
  price: number;
  created_at: string;
}

export interface Order {
  id: string;
  user_id: string;
  user?: User;
  items: OrderItem[];
  total_amount: number;
  status: OrderStatus;
  stripe_payment_intent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOrderData {
  items: Array<{
    product_id: string;
    quantity: number;
  }>;
}

// Payment Types
export interface PaymentIntent {
  client_secret: string;
  amount: number;
  currency: string;
}

export interface CreatePaymentData {
  order_id: string;
  amount: number;
}

// API Response Types
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

export interface ApiError {
  detail: string;
  status_code: number;
}

// Search and Filter Types
export interface ProductFilters {
  category_id?: string;
  min_price?: number;
  max_price?: number;
  search?: string;
  is_active?: boolean;
}

export interface QueryParams {
  page?: number;
  size?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

// Form Types
export interface FormState {
  isLoading: boolean;
  error: string | null;
  success: boolean;
}

// Theme Types
export type Theme = 'light' | 'dark';

// Navigation Types
export interface NavItem {
  name: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}