import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';
import SessionCard from '../components/SessionCard';

const Sessions: React.FC = () => {
  const { sessions, fetchSessions, sessionsLoading, replaySession } = useDashboardStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleReplay = async (sessionId: string) => {
    try {
      await replaySession(sessionId);
      alert(`Replaying session ${sessionId}`);
    } catch (error) {
      alert(`Failed to replay session: ${error}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Sessions</h1>
        <button
          onClick={() => fetchSessions()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh
        </button>
      </div>

      {sessionsLoading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading sessions...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map((session) => (
            <div key={session.session_id} className="relative">
              <SessionCard session={session} />
              {session.status === 'completed' && (
                <button
                  onClick={() => handleReplay(session.session_id)}
                  className="absolute top-2 right-2 px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                >
                  Replay
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {!sessionsLoading && sessions.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <div className="text-4xl mb-4">📂</div>
          <div className="text-lg">No sessions found</div>
          <div className="text-sm mt-2">Sessions will appear here once agents start running</div>
        </div>
      )}
    </div>
  );
};

export default Sessions;