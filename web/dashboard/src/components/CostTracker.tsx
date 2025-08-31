import React, { useEffect, useState } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface CostData {
  timestamp: number;
  provider: string;
  model: string;
  agent: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
  cached: boolean;
}

interface ProviderCosts {
  anthropic: number;
  openai: number;
  gemini: number;
  cached: number;
}

interface AgentCosts {
  [key: string]: number;
}

interface CostSummary {
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  cacheSavings: number;
  averageCostPerRequest: number;
  providerCosts: ProviderCosts;
  agentCosts: AgentCosts;
  hourlyData: Array<{ hour: string; cost: number }>;
  dailyData: Array<{ date: string; cost: number }>;
}

const CostTracker: React.FC = () => {
  const [costData, setCostData] = useState<CostData[]>([]);
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [timeRange, setTimeRange] = useState<'hour' | 'day' | 'week' | 'month'>('day');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [budgetLimit, setBudgetLimit] = useState<number>(100);
  const [budgetAlert, setBudgetAlert] = useState<boolean>(false);
  const [refreshInterval, setRefreshInterval] = useState<number>(5000);

  // Fetch cost data from API
  useEffect(() => {
    const fetchCostData = async () => {
      try {
        const response = await fetch(`/api/costs?range=${timeRange}&provider=${selectedProvider}`);
        const data = await response.json();
        setCostData(data.costs || []);
        
        // Calculate summary
        const summary = calculateSummary(data.costs || []);
        setSummary(summary);
        
        // Check budget alert
        if (summary.totalCost > budgetLimit * 0.8) {
          setBudgetAlert(true);
        }
      } catch (error) {
        console.error('Failed to fetch cost data:', error);
      }
    };

    fetchCostData();
    const interval = setInterval(fetchCostData, refreshInterval);
    return () => clearInterval(interval);
  }, [timeRange, selectedProvider, refreshInterval, budgetLimit]);

  const calculateSummary = (data: CostData[]): CostSummary => {
    const providerCosts: ProviderCosts = {
      anthropic: 0,
      openai: 0,
      gemini: 0,
      cached: 0
    };
    
    const agentCosts: AgentCosts = {};
    let totalCost = 0;
    let totalTokens = 0;
    let cacheSavings = 0;
    
    // Process each cost entry
    data.forEach(entry => {
      if (entry.cached) {
        cacheSavings += entry.cost;
        providerCosts.cached += entry.cost;
      } else {
        totalCost += entry.cost;
        
        // Provider costs
        if (entry.provider.toLowerCase().includes('anthropic')) {
          providerCosts.anthropic += entry.cost;
        } else if (entry.provider.toLowerCase().includes('openai')) {
          providerCosts.openai += entry.cost;
        } else if (entry.provider.toLowerCase().includes('gemini')) {
          providerCosts.gemini += entry.cost;
        }
      }
      
      // Agent costs
      if (!agentCosts[entry.agent]) {
        agentCosts[entry.agent] = 0;
      }
      agentCosts[entry.agent] += entry.cost;
      
      // Token count
      totalTokens += entry.inputTokens + entry.outputTokens;
    });
    
    // Calculate hourly data for chart
    const hourlyData = calculateHourlyData(data);
    const dailyData = calculateDailyData(data);
    
    return {
      totalCost,
      totalTokens,
      totalRequests: data.length,
      cacheSavings,
      averageCostPerRequest: data.length > 0 ? totalCost / data.length : 0,
      providerCosts,
      agentCosts,
      hourlyData,
      dailyData
    };
  };

  const calculateHourlyData = (data: CostData[]) => {
    const hourlyMap = new Map<string, number>();
    
    data.forEach(entry => {
      const date = new Date(entry.timestamp);
      const hour = `${date.getHours()}:00`;
      const current = hourlyMap.get(hour) || 0;
      hourlyMap.set(hour, current + entry.cost);
    });
    
    return Array.from(hourlyMap.entries())
      .map(([hour, cost]) => ({ hour, cost }))
      .sort((a, b) => a.hour.localeCompare(b.hour));
  };

  const calculateDailyData = (data: CostData[]) => {
    const dailyMap = new Map<string, number>();
    
    data.forEach(entry => {
      const date = new Date(entry.timestamp).toLocaleDateString();
      const current = dailyMap.get(date) || 0;
      dailyMap.set(date, current + entry.cost);
    });
    
    return Array.from(dailyMap.entries())
      .map(([date, cost]) => ({ date, cost }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  // Chart configurations
  const costTrendChartData = {
    labels: summary?.hourlyData.map(d => d.hour) || [],
    datasets: [
      {
        label: 'Cost per Hour',
        data: summary?.hourlyData.map(d => d.cost) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const providerChartData = {
    labels: ['Anthropic', 'OpenAI', 'Gemini', 'Cached'],
    datasets: [
      {
        data: [
          summary?.providerCosts.anthropic || 0,
          summary?.providerCosts.openai || 0,
          summary?.providerCosts.gemini || 0,
          summary?.providerCosts.cached || 0
        ],
        backgroundColor: [
          'rgba(147, 51, 234, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(107, 114, 128, 0.8)'
        ],
        borderWidth: 0
      }
    ]
  };

  const agentChartData = {
    labels: Object.keys(summary?.agentCosts || {}).slice(0, 10),
    datasets: [
      {
        label: 'Cost by Agent',
        data: Object.values(summary?.agentCosts || {}).slice(0, 10),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y || context.parsed;
            return `$${value.toFixed(4)}`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: any) => `$${value.toFixed(2)}`
        }
      }
    }
  };

  return (
    <div className="cost-tracker p-6 space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Cost Tracking Dashboard</h2>
        
        <div className="flex gap-4">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="hour">Last Hour</option>
            <option value="day">Last 24 Hours</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
          </select>
          
          {/* Provider Filter */}
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Providers</option>
            <option value="anthropic">Anthropic</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Gemini</option>
          </select>
          
          {/* Refresh Interval */}
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="5000">5 seconds</option>
            <option value="10000">10 seconds</option>
            <option value="30000">30 seconds</option>
            <option value="60000">1 minute</option>
          </select>
        </div>
      </div>

      {/* Budget Alert */}
      {budgetAlert && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                Warning: You've used {((summary?.totalCost || 0) / budgetLimit * 100).toFixed(1)}% of your ${budgetLimit} budget
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Cost</h3>
          <p className="text-2xl font-bold text-gray-900">${summary?.totalCost.toFixed(4) || '0.00'}</p>
          <p className="text-xs text-gray-500 mt-1">This {timeRange}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Tokens</h3>
          <p className="text-2xl font-bold text-gray-900">{summary?.totalTokens.toLocaleString() || '0'}</p>
          <p className="text-xs text-gray-500 mt-1">Processed</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">API Calls</h3>
          <p className="text-2xl font-bold text-gray-900">{summary?.totalRequests || '0'}</p>
          <p className="text-xs text-gray-500 mt-1">Total requests</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Cache Savings</h3>
          <p className="text-2xl font-bold text-green-600">${summary?.cacheSavings.toFixed(4) || '0.00'}</p>
          <p className="text-xs text-gray-500 mt-1">Saved by caching</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Avg Cost/Request</h3>
          <p className="text-2xl font-bold text-gray-900">${summary?.averageCostPerRequest.toFixed(4) || '0.00'}</p>
          <p className="text-xs text-gray-500 mt-1">Per API call</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trend Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cost Trend</h3>
          <div className="h-64">
            <Line data={costTrendChartData} options={chartOptions} />
          </div>
        </div>
        
        {/* Provider Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Provider Distribution</h3>
          <div className="h-64">
            <Doughnut data={providerChartData} options={{ ...chartOptions, scales: undefined }} />
          </div>
        </div>
      </div>

      {/* Agent Costs Bar Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top 10 Agents by Cost</h3>
        <div className="h-64">
          <Bar data={agentChartData} options={chartOptions} />
        </div>
      </div>

      {/* Cost Optimization Recommendations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Cost Optimization Recommendations</h3>
        <div className="space-y-3">
          {Object.entries(summary?.agentCosts || {})
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([agent, cost]) => {
              const avgCost = cost / (summary?.totalRequests || 1);
              const recommendation = avgCost > 0.01 
                ? 'Consider using a cheaper model for routine tasks'
                : avgCost > 0.005 
                ? 'Good balance of cost and performance'
                : 'Excellent cost optimization';
              
              return (
                <div key={agent} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium text-gray-900">{agent}</p>
                    <p className="text-sm text-gray-500">{recommendation}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">${cost.toFixed(4)}</p>
                    <p className="text-sm text-gray-500">${avgCost.toFixed(4)}/request</p>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Budget Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Settings</h3>
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Daily Budget Limit:</label>
          <input
            type="number"
            value={budgetLimit}
            onChange={(e) => setBudgetLimit(parseFloat(e.target.value))}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
            step="10"
          />
          <span className="text-sm text-gray-500">USD</span>
          
          <div className="ml-auto">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Budget Used:</span>
              <div className="w-48 bg-gray-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${
                    (summary?.totalCost || 0) / budgetLimit > 0.8 
                      ? 'bg-yellow-500' 
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(((summary?.totalCost || 0) / budgetLimit) * 100, 100)}%` }}
                />
              </div>
              <span className="text-sm font-medium">
                {((summary?.totalCost || 0) / budgetLimit * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostTracker;