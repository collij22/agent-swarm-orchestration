import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import useDashboardStore from '../store/dashboardStore';

const PerformanceChart: React.FC = () => {
  const { performanceHistory } = useDashboardStore();

  // Transform data for the chart
  const chartData = performanceHistory.slice(-20).map((snapshot) => ({
    time: new Date(snapshot.timestamp).toLocaleTimeString(),
    cpu: snapshot.cpu_usage,
    memory: snapshot.memory_usage,
    apiCalls: snapshot.api_calls_per_minute,
  }));

  return (
    <div className="h-64">
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="dark:opacity-20" />
            <XAxis 
              dataKey="time" 
              className="text-xs"
              tick={{ fill: 'currentColor' }}
            />
            <YAxis 
              className="text-xs"
              tick={{ fill: 'currentColor' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(31, 41, 55, 0.9)',
                border: 'none',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="cpu" 
              stroke="#3b82f6" 
              name="CPU %"
              strokeWidth={2}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="#10b981" 
              name="Memory %"
              strokeWidth={2}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="apiCalls" 
              stroke="#f59e0b" 
              name="API Calls/min"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <div>No performance data yet</div>
            <div className="text-sm mt-1">Data will appear once the system starts monitoring</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceChart;