import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';

const Analytics: React.FC = () => {
  const { metrics, fetchMetrics, metricsLoading } = useDashboardStore();

  useEffect(() => {
    fetchMetrics('daily');
  }, [fetchMetrics]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Analytics</h1>
      
      {metricsLoading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading metrics...</div>
        </div>
      ) : metrics ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Sessions</div>
              <div className="text-3xl font-bold text-gray-800 dark:text-white">
                {metrics.total_sessions}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400">Success Rate</div>
              <div className="text-3xl font-bold text-gray-800 dark:text-white">
                {(metrics.success_rate * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400">Avg Duration</div>
              <div className="text-3xl font-bold text-gray-800 dark:text-white">
                {metrics.avg_duration.toFixed(1)}s
              </div>
            </div>
          </div>

          {/* Most Used Agents */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
              Most Used Agents
            </h2>
            <div className="space-y-3">
              {metrics.most_used_agents.map((agent, index) => (
                <div key={agent.agent} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-medium text-gray-500">#{index + 1}</span>
                    <span className="text-gray-800 dark:text-white">{agent.agent}</span>
                  </div>
                  <span className="text-gray-600 dark:text-gray-400">{agent.count} calls</span>
                </div>
              ))}
            </div>
          </div>

          {/* Error Trends */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
              Error Trends
            </h2>
            <div className="space-y-2">
              {metrics.error_trends.map((trend) => (
                <div key={trend.date} className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">{trend.date}</span>
                  <span className="text-red-600 dark:text-red-400">{trend.count} errors</span>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No metrics available
        </div>
      )}
    </div>
  );
};

export default Analytics;