import React from 'react';
import { Session } from '../services/api';

interface SessionCardProps {
  session: Session;
  onClick?: () => void;
}

const SessionCard: React.FC<SessionCardProps> = ({ session, onClick }) => {
  const statusColors = {
    running: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    completed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };

  return (
    <div 
      className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-gray-800 dark:text-white">
          {session.session_id.substring(0, 8)}...
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          statusColors[session.status as keyof typeof statusColors] || statusColors.running
        }`}>
          {session.status}
        </span>
      </div>
      
      <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
        <div className="flex justify-between">
          <span>Started:</span>
          <span>{formatTime(session.start_time)}</span>
        </div>
        {session.end_time && (
          <div className="flex justify-between">
            <span>Ended:</span>
            <span>{formatTime(session.end_time)}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Duration:</span>
          <span>{formatDuration(session.duration)}</span>
        </div>
        <div className="flex justify-between">
          <span>Agents:</span>
          <span>{session.agents_used.length}</span>
        </div>
        {session.error_count > 0 && (
          <div className="flex justify-between text-red-600 dark:text-red-400">
            <span>Errors:</span>
            <span>{session.error_count}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionCard;