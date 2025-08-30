import axios from 'axios';
import type { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Session {
  session_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  agents_used: string[];
  total_tool_calls: number;
  error_count: number;
}

export interface Metrics {
  period: string;
  total_sessions: number;
  success_rate: number;
  avg_duration: number;
  most_used_agents: Array<{
    agent: string;
    count: number;
  }>;
  error_trends: Array<{
    date: string;
    count: number;
  }>;
}

export interface PerformanceSnapshot {
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  active_sessions: number;
  api_calls_per_minute: number;
  avg_response_time: number;
}

export interface Agent {
  name: string;
  tier: number;
  model: string;
  status: string;
  total_calls?: number;
  success_rate?: number;
  avg_duration?: number;
}

export interface Error {
  session_id: string;
  timestamp: string;
  agent: string;
  error: string;
  context?: any;
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    // Add request interceptor for auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Sessions
  async getSessions(status?: string, limit = 50, offset = 0): Promise<Session[]> {
    const response = await this.api.get('/api/sessions', {
      params: { status, limit, offset },
    });
    return response.data;
  }

  async getSession(sessionId: string): Promise<any> {
    const response = await this.api.get(`/api/sessions/${sessionId}`);
    return response.data;
  }

  async replaySession(sessionId: string): Promise<any> {
    const response = await this.api.post(`/api/sessions/${sessionId}/replay`);
    return response.data;
  }

  // Metrics
  async getMetrics(period: 'hourly' | 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<Metrics> {
    const response = await this.api.get('/api/metrics', {
      params: { period },
    });
    return response.data;
  }

  // Performance
  async getPerformance(): Promise<PerformanceSnapshot> {
    const response = await this.api.get('/api/performance');
    return response.data;
  }

  // Agents
  async getAgents(): Promise<Agent[]> {
    const response = await this.api.get('/api/agents');
    return response.data;
  }

  // Errors
  async getErrors(sessionId?: string, limit = 100): Promise<Error[]> {
    const response = await this.api.get('/api/errors', {
      params: { session_id: sessionId, limit },
    });
    return response.data;
  }

  // Analysis
  async analyzeSession(
    sessionId: string,
    analysisTypes: string[] = ['error_pattern', 'performance_bottleneck']
  ): Promise<any> {
    const response = await this.api.post(`/api/analyze/${sessionId}`, null, {
      params: { analysis_types: analysisTypes },
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.api.get('/');
      return response.data.status === 'running';
    } catch {
      return false;
    }
  }
}

// Export singleton instance
const apiService = new ApiService();
export default apiService;