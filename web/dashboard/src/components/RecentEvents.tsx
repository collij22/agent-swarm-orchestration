import React from 'react';
import useDashboardStore from '../store/dashboardStore';

const RecentEvents: React.FC = () => {
  const { recentEvents } = useDashboardStore();

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('session')) return '📁';
    if (eventType.includes('agent')) return '🤖';
    if (eventType.includes('error')) return '❌';
    if (eventType.includes('performance')) return '📈';
    if (eventType.includes('cost')) return '💰';
    if (eventType.includes('checkpoint')) return '💾';
    if (eventType.includes('memory')) return '🧠';
    return '📍';
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'error':
        return 'text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {recentEvents.length > 0 ? (
        recentEvents.slice(0, 20).map((event, index) => (
          <div 
            key={`${event.timestamp}-${index}`}
            className="flex items-start space-x-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <span className="text-lg mt-0.5">{getEventIcon(event.event)}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${getSeverityColor(event.metadata?.severity)}`}>
                  {event.event}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {formatTime(event.timestamp)}
                </span>
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 mt-1 truncate">
                {typeof event.data === 'string' 
                  ? event.data 
                  : event.data?.message || JSON.stringify(event.data).substring(0, 100)}
              </div>
              {event.metadata?.agent_name && (
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Agent: {event.metadata.agent_name}
                </div>
              )}
            </div>
          </div>
        ))
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <div className="text-2xl mb-2">📭</div>
          <div>No events yet</div>
          <div className="text-sm mt-1">Events will appear here as they occur</div>
        </div>
      )}
    </div>
  );
};

export default RecentEvents;