import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';

const AgentView: React.FC = () => {
  const { agents, fetchAgents, agentsLoading } = useDashboardStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const tierColors = {
    1: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    2: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    3: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  };

  const modelColors = {
    opus: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
    sonnet: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
    haiku: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Agent Management</h1>
      
      {agentsLoading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading agents...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div 
              key={agent.name}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-800 dark:text-white">
                  {agent.name}
                </h3>
                <div className={`w-3 h-3 rounded-full ${
                  agent.status === 'ready' ? 'bg-green-500' : 'bg-gray-400'
                }`} />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    tierColors[agent.tier as keyof typeof tierColors]
                  }`}>
                    Tier {agent.tier}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    modelColors[agent.model as keyof typeof modelColors]
                  }`}>
                    {agent.model}
                  </span>
                </div>
                
                {agent.total_calls !== undefined && (
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <div>Total Calls: {agent.total_calls}</div>
                    {agent.success_rate !== undefined && (
                      <div>Success Rate: {(agent.success_rate * 100).toFixed(1)}%</div>
                    )}
                    {agent.avg_duration !== undefined && (
                      <div>Avg Duration: {agent.avg_duration.toFixed(1)}s</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentView;