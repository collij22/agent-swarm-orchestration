import React from 'react';
import useDashboardStore from '../store/dashboardStore';

const Sidebar: React.FC = () => {
  const { selectedView, setSelectedView, sidebarCollapsed, toggleSidebar } = useDashboardStore();

  const menuItems = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'sessions', label: 'Sessions', icon: '📁' },
    { id: 'monitoring', label: 'Monitoring', icon: '📈' },
    { id: 'analytics', label: 'Analytics', icon: '📉' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'errors', label: 'Errors', icon: '⚠️' },
  ] as const;

  return (
    <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-gray-800 dark:bg-gray-900 text-white transition-all duration-300`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        {!sidebarCollapsed && <h1 className="text-xl font-bold">Agent Swarm</h1>}
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-gray-700 rounded transition-colors"
        >
          {sidebarCollapsed ? '→' : '←'}
        </button>
      </div>
      
      <nav className="mt-4">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setSelectedView(item.id)}
            className={`w-full flex items-center px-4 py-3 text-left hover:bg-gray-700 transition-colors ${
              selectedView === item.id ? 'bg-gray-700 border-l-4 border-blue-500' : ''
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            {!sidebarCollapsed && <span className="ml-3">{item.label}</span>}
          </button>
        ))}
      </nav>
      
      {!sidebarCollapsed && (
        <div className="absolute bottom-0 w-full p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            <div>Version 1.0.0</div>
            <div className="mt-1">© 2024 Agent Swarm</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;