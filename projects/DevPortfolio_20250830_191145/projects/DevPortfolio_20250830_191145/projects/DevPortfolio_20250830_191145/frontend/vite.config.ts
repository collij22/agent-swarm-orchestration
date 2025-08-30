/**
 * Vite Configuration - Optimized for Performance
 * Target: <3s initial page load
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import { splitVendorChunkPlugin } from 'vite'

export default defineConfig({
  plugins: [
    react({
      // Enable React Fast Refresh
      fastRefresh: true,
    }),
    
    // Bundle analyzer
    visualizer({
      filename: 'dist/bundle-analysis.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
    
    // Smart vendor chunk splitting
    splitVendorChunkPlugin(),
  ],

  // Development server
  server: {
    port: 3000,
    host: true,
    open: true,
    cors: true,
  },

  // Build optimizations
  build: {
    target: 'es2020',
    minify: 'terser',
    sourcemap: false, // Disable in production for smaller bundles
    
    // Terser options for maximum compression
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
      },
      mangle: {
        safari10: true,
      },
    },
    
    // Rollup options for advanced chunking
    rollupOptions: {
      output: {
        // Manual chunk splitting for optimal loading
        manualChunks: {
          // Core React libraries
          'react-vendor': ['react', 'react-dom'],
          
          // Routing
          'router': ['react-router-dom'],
          
          // State management
          'state': ['zustand'],
          
          // UI components (if using a library)
          'ui': ['@headlessui/react', '@heroicons/react'],
          
          // Utilities
          'utils': ['date-fns', 'clsx'],
          
          // Rich text editor (if used)
          'editor': ['@tiptap/react', '@tiptap/starter-kit'],
          
          // Charts/visualization (if used)
          'charts': ['recharts', 'd3'],
          
          // HTTP client
          'http': ['axios'],
        },
        
        // Optimize chunk file names
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace('.tsx', '').replace('.ts', '')
            : 'chunk'
          return `js/${facadeModuleId}-[hash].js`
        },
        
        // Optimize asset file names
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name || '')) {
            return `images/[name]-[hash][extname]`
          }
          
          if (/\.(css)$/i.test(assetInfo.name || '')) {
            return `css/[name]-[hash][extname]`
          }
          
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return `fonts/[name]-[hash][extname]`
          }
          
          return `assets/[name]-[hash][extname]`
        },
      },
    },
    
    // Chunk size warnings
    chunkSizeWarningLimit: 500, // Warn for chunks > 500kb
    
    // Asset inlining threshold
    assetsInlineLimit: 4096, // Inline assets < 4kb
  },

  // CSS optimization
  css: {
    modules: {
      localsConvention: 'camelCase',
    },
    postcss: {
      plugins: [
        // Add PostCSS plugins here if needed
      ],
    },
  },

  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@pages': resolve(__dirname, 'src/pages'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
      '@api': resolve(__dirname, 'src/api'),
      '@assets': resolve(__dirname, 'src/assets'),
      '@stores': resolve(__dirname, 'src/stores'),
    },
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'zustand',
      'axios',
    ],
    exclude: [
      // Exclude dev dependencies
    ],
  },

  // Environment variables
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },

  // Preview server (for production builds)
  preview: {
    port: 4173,
    host: true,
  },
})