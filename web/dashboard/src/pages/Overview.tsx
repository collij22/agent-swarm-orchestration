import React from 'react';
import useDashboardStore from '../store/dashboardStore';
import MetricCard from '../components/MetricCard';
import SessionCard from '../components/SessionCard';
import PerformanceChart from '../components/PerformanceChart';
import RecentEvents from '../components/RecentEvents';

const Overview: React.FC = () => {
  const { 
    sessions, 
    metrics, 
    performance,
    agents,
    errors,
    activeSessions
  } = useDashboardStore();

  const stats = {
    totalSessions: sessions.length,
    activeSessions: activeSessions.length,
    successRate: metrics?.success_rate || 0,
    avgDuration: metrics?.avg_duration || 0,
    totalAgents: agents.length,
    activeAgents: agents.filter(a => a.status === 'running').length,
    errorCount: errors.length,
    criticalErrors: errors.filter(e => e.error.includes('critical')).length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
          System Overview
        </h1>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Sessions"
          value={stats.totalSessions}
          change={12}
          icon="📊"
          color="blue"
        />
        <MetricCard
          title="Active Sessions"
          value={stats.activeSessions}
          change={0}
          icon="🔄"
          color="green"
        />
        <MetricCard
          title="Success Rate"
          value={`${(stats.successRate * 100).toFixed(1)}%`}
          change={5}
          icon="✅"
          color="emerald"
        />
        <MetricCard
          title="Errors"
          value={stats.errorCount}
          change={-25}
          icon="⚠️"
          color="red"
        />
      </div>

      {/* Performance Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
          System Performance
        </h2>
        <PerformanceChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Sessions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
            Recent Sessions
          </h2>
          <div className="space-y-3">
            {sessions.slice(0, 5).map((session) => (
              <SessionCard key={session.session_id} session={session} />
            ))}
            {sessions.length === 0 && (
              <div className="text-gray-500 dark:text-gray-400 text-center py-4">
                No sessions yet
              </div>
            )}
          </div>
        </div>

        {/* Recent Events */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
            Recent Events
          </h2>
          <RecentEvents />
        </div>
      </div>

      {/* Agent Status Grid */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-white">
          Agent Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {agents.slice(0, 15).map((agent) => (
            <div
              key={agent.name}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded"
            >
              <div>
                <div className="text-sm font-medium text-gray-800 dark:text-white">
                  {agent.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Tier {agent.tier} • {agent.model}
                </div>
              </div>
              <div className={`w-2 h-2 rounded-full ${
                agent.status === 'ready' ? 'bg-green-500' : 'bg-gray-400'
              }`} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Overview;