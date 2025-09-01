import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CartItem, Product } from '../types';
import { apiClient } from '../api/client';

interface CartState {
  items: CartItem[];
  isLoading: boolean;
  error: string | null;
  
  // Computed values
  itemCount: number;
  totalAmount: number;
  
  // Actions
  fetchCart: () => Promise<void>;
  addItem: (productId: string, quantity?: number) => Promise<void>;
  updateItem: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  clearError: () => void;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      isLoading: false,
      error: null,
      
      get itemCount() {
        return get().items.reduce((total, item) => total + item.quantity, 0);
      },
      
      get totalAmount() {
        return get().items.reduce((total, item) => total + (item.product.price * item.quantity), 0);
      },

      fetchCart: async () => {
        set({ isLoading: true, error: null });
        try {
          const items = await apiClient.cart.list();
          set({ items, isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to fetch cart';
          set({ error: errorMessage, isLoading: false });
        }
      },

      addItem: async (productId: string, quantity = 1) => {
        set({ isLoading: true, error: null });
        try {
          const newItem = await apiClient.cart.add({ product_id: productId, quantity });
          
          // Check if item already exists in cart
          const existingItemIndex = get().items.findIndex(item => item.product_id === productId);
          
          if (existingItemIndex >= 0) {
            // Update existing item
            const updatedItems = [...get().items];
            updatedItems[existingItemIndex] = newItem;
            set({ items: updatedItems, isLoading: false });
          } else {
            // Add new item
            set({ items: [...get().items, newItem], isLoading: false });
          }
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to add item to cart';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      updateItem: async (itemId: string, quantity: number) => {
        if (quantity <= 0) {
          await get().removeItem(itemId);
          return;
        }

        set({ isLoading: true, error: null });
        try {
          const updatedItem = await apiClient.cart.update(itemId, { quantity });
          
          const updatedItems = get().items.map(item =>
            item.id === itemId ? updatedItem : item
          );
          
          set({ items: updatedItems, isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to update cart item';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      removeItem: async (itemId: string) => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.cart.remove(itemId);
          
          const updatedItems = get().items.filter(item => item.id !== itemId);
          set({ items: updatedItems, isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to remove cart item';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      clearCart: async () => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.cart.clear();
          set({ items: [], isLoading: false });
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Failed to clear cart';
          set({ error: errorMessage, isLoading: false });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'cart-storage',
      partialize: (state) => ({
        items: state.items,
      }),
    }
  )
);