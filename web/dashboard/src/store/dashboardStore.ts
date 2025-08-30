import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import apiService from '../services/api';
import type { Session, Metrics, PerformanceSnapshot, Agent, Error } from '../services/api';
import websocketService from '../services/websocket';
import type { WebSocketEvent } from '../services/websocket';

interface DashboardState {
  // Connection status
  isConnected: boolean;
  connectionError: string | null;
  
  // Sessions
  sessions: Session[];
  currentSession: any | null;
  activeSessions: string[];
  sessionsLoading: boolean;
  
  // Metrics
  metrics: Metrics | null;
  metricsLoading: boolean;
  
  // Performance
  performance: PerformanceSnapshot | null;
  performanceHistory: PerformanceSnapshot[];
  
  // Agents
  agents: Agent[];
  agentsLoading: boolean;
  
  // Errors
  errors: Error[];
  errorsLoading: boolean;
  
  // Events
  recentEvents: WebSocketEvent[];
  maxEvents: number;
  
  // UI State
  selectedView: 'overview' | 'sessions' | 'monitoring' | 'analytics' | 'agents' | 'errors';
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  autoRefresh: boolean;
  refreshInterval: number;
  
  // Actions
  connect: () => Promise<void>;
  disconnect: () => void;
  
  // Session actions
  fetchSessions: (status?: string) => Promise<void>;
  fetchSession: (sessionId: string) => Promise<void>;
  replaySession: (sessionId: string) => Promise<void>;
  
  // Metrics actions
  fetchMetrics: (period?: 'hourly' | 'daily' | 'weekly' | 'monthly') => Promise<void>;
  
  // Performance actions
  fetchPerformance: () => Promise<void>;
  
  // Agent actions
  fetchAgents: () => Promise<void>;
  
  // Error actions
  fetchErrors: (sessionId?: string) => Promise<void>;
  
  // Event actions
  addEvent: (event: WebSocketEvent) => void;
  clearEvents: () => void;
  
  // UI actions
  setSelectedView: (view: DashboardState['selectedView']) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
}

const useDashboardStore = create<DashboardState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        isConnected: false,
        connectionError: null,
        
        sessions: [],
        currentSession: null,
        activeSessions: [],
        sessionsLoading: false,
        
        metrics: null,
        metricsLoading: false,
        
        performance: null,
        performanceHistory: [],
        
        agents: [],
        agentsLoading: false,
        
        errors: [],
        errorsLoading: false,
        
        recentEvents: [],
        maxEvents: 100,
        
        selectedView: 'overview',
        sidebarCollapsed: false,
        theme: 'dark',
        autoRefresh: true,
        refreshInterval: 30000,  // 30 seconds instead of 5
        
        // Connection actions
        connect: async () => {
          try {
            await websocketService.connect();
            
            // Subscribe to events
            websocketService.subscribe('*', (event) => {
              get().addEvent(event);
              
              // Handle specific events
              if (event.event === 'session.started') {
                get().fetchSessions();
              } else if (event.event === 'session.completed') {
                get().fetchSessions();
                get().fetchMetrics();
              } else if (event.event === 'performance.update') {
                set((state) => ({
                  performance: {
                    ...event.data,
                    timestamp: event.timestamp,
                  } as PerformanceSnapshot,
                }));
              }
            });
            
            websocketService.subscribe('connection.status', (event) => {
              set({ isConnected: event.data.connected });
            });
            
            set({ isConnected: true, connectionError: null });
            
            // Initial data fetch
            await Promise.all([
              get().fetchSessions(),
              get().fetchMetrics(),
              get().fetchPerformance(),
              get().fetchAgents(),
            ]);
          } catch (error: any) {
            set({ 
              isConnected: false, 
              connectionError: error.message || 'Failed to connect',
            });
            throw error;
          }
        },
        
        disconnect: () => {
          websocketService.disconnect();
          set({ isConnected: false });
        },
        
        // Session actions
        fetchSessions: async (status?: string) => {
          set({ sessionsLoading: true });
          try {
            const sessions = await apiService.getSessions(status);
            const activeSessions = sessions
              .filter(s => s.status === 'running')
              .map(s => s.session_id);
            set({ sessions, activeSessions, sessionsLoading: false });
          } catch (error) {
            console.error('Failed to fetch sessions:', error);
            set({ sessionsLoading: false });
          }
        },
        
        fetchSession: async (sessionId: string) => {
          try {
            const session = await apiService.getSession(sessionId);
            set({ currentSession: session });
          } catch (error) {
            console.error('Failed to fetch session:', error);
          }
        },
        
        replaySession: async (sessionId: string) => {
          try {
            await apiService.replaySession(sessionId);
            // Refresh sessions after replay starts
            await get().fetchSessions();
          } catch (error) {
            console.error('Failed to replay session:', error);
            throw error;
          }
        },
        
        // Metrics actions
        fetchMetrics: async (period = 'daily') => {
          set({ metricsLoading: true });
          try {
            const metrics = await apiService.getMetrics(period);
            set({ metrics, metricsLoading: false });
          } catch (error) {
            console.error('Failed to fetch metrics:', error);
            set({ metricsLoading: false });
          }
        },
        
        // Performance actions
        fetchPerformance: async () => {
          try {
            const performance = await apiService.getPerformance();
            set((state) => ({
              performance,
              performanceHistory: [
                ...state.performanceHistory.slice(-99),
                performance,
              ],
            }));
          } catch (error) {
            console.error('Failed to fetch performance:', error);
          }
        },
        
        // Agent actions
        fetchAgents: async () => {
          set({ agentsLoading: true });
          try {
            const agents = await apiService.getAgents();
            set({ agents, agentsLoading: false });
          } catch (error) {
            console.error('Failed to fetch agents:', error);
            set({ agentsLoading: false });
          }
        },
        
        // Error actions
        fetchErrors: async (sessionId?: string) => {
          set({ errorsLoading: true });
          try {
            const errors = await apiService.getErrors(sessionId);
            set({ errors, errorsLoading: false });
          } catch (error) {
            console.error('Failed to fetch errors:', error);
            set({ errorsLoading: false });
          }
        },
        
        // Event actions
        addEvent: (event: WebSocketEvent) => {
          set((state) => ({
            recentEvents: [
              event,
              ...state.recentEvents.slice(0, state.maxEvents - 1),
            ],
          }));
        },
        
        clearEvents: () => {
          set({ recentEvents: [] });
        },
        
        // UI actions
        setSelectedView: (view) => {
          set({ selectedView: view });
        },
        
        toggleSidebar: () => {
          set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
        },
        
        setTheme: (theme) => {
          set({ theme });
          // Apply theme to document
          if (theme === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        },
        
        setAutoRefresh: (enabled) => {
          set({ autoRefresh: enabled });
        },
        
        setRefreshInterval: (interval) => {
          set({ refreshInterval: interval });
        },
      }),
      {
        name: 'dashboard-storage',
        partialize: (state) => ({
          theme: state.theme,
          sidebarCollapsed: state.sidebarCollapsed,
          autoRefresh: state.autoRefresh,
          refreshInterval: state.refreshInterval,
        }),
      }
    )
  )
);

export default useDashboardStore;