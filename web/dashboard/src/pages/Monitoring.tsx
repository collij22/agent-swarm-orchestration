import React from 'react';
import useDashboardStore from '../store/dashboardStore';
import PerformanceChart from '../components/PerformanceChart';

const Monitoring: React.FC = () => {
  const { performance, performanceHistory } = useDashboardStore();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-white">System Monitoring</h1>
      
      {/* Current Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</div>
          <div className="text-3xl font-bold text-gray-800 dark:text-white">
            {performance?.cpu_usage.toFixed(1) || 0}%
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</div>
          <div className="text-3xl font-bold text-gray-800 dark:text-white">
            {performance?.memory_usage.toFixed(1) || 0}%
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 dark:text-gray-400">Active Sessions</div>
          <div className="text-3xl font-bold text-gray-800 dark:text-white">
            {performance?.active_sessions || 0}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 dark:text-gray-400">API Calls/min</div>
          <div className="text-3xl font-bold text-gray-800 dark:text-white">
            {performance?.api_calls_per_minute.toFixed(0) || 0}
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
          Performance History
        </h2>
        <PerformanceChart />
      </div>

      {/* System Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
          System Information
        </h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600 dark:text-gray-400">Response Time:</span>
            <span className="ml-2 text-gray-800 dark:text-white">
              {performance?.avg_response_time.toFixed(0) || 0}ms
            </span>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Data Points:</span>
            <span className="ml-2 text-gray-800 dark:text-white">
              {performanceHistory.length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;