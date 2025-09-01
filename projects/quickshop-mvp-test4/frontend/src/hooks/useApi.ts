import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { ProductFilters, QueryParams } from '../types';

// Product hooks
export const useProducts = (filters?: ProductFilters, params?: QueryParams) => {
  return useQuery({
    queryKey: ['products', filters, params],
    queryFn: () => apiClient.products.list(filters, params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useProduct = (id: string) => {
  return useQuery({
    queryKey: ['product', id],
    queryFn: () => apiClient.products.get(id),
    enabled: !!id,
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.products.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      apiClient.products.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product', id] });
    },
  });
};

export const useDeleteProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.products.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};

// Category hooks
export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => apiClient.categories.list(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useCreateCategory = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.categories.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

// Cart hooks
export const useCart = () => {
  return useQuery({
    queryKey: ['cart'],
    queryFn: () => apiClient.cart.list(),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

export const useAddToCart = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.cart.add,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
};

export const useUpdateCartItem = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: any }) =>
      apiClient.cart.update(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
};

export const useRemoveFromCart = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.cart.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
};

// Order hooks
export const useOrders = (params?: QueryParams) => {
  return useQuery({
    queryKey: ['orders', params],
    queryFn: () => apiClient.orders.list(params),
  });
};

export const useOrder = (id: string) => {
  return useQuery({
    queryKey: ['order', id],
    queryFn: () => apiClient.orders.get(id),
    enabled: !!id,
  });
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.orders.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
  });
};

// Payment hooks
export const useCreatePaymentIntent = () => {
  return useMutation({
    mutationFn: apiClient.payments.createIntent,
  });
};

export const useConfirmPayment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.payments.confirmPayment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

// Admin hooks
export const useAdminUsers = (params?: QueryParams) => {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => apiClient.admin.users.list(params),
  });
};

export const useAdminOrders = (params?: QueryParams) => {
  return useQuery({
    queryKey: ['admin', 'orders', params],
    queryFn: () => apiClient.admin.orders.list(params),
  });
};

export const useAdminDashboard = () => {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: () => apiClient.admin.analytics.dashboard(),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
};

export const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiClient.admin.orders.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};