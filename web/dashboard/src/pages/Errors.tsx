import React, { useEffect } from 'react';
import useDashboardStore from '../store/dashboardStore';

const Errors: React.FC = () => {
  const { errors, fetchErrors, errorsLoading } = useDashboardStore();

  useEffect(() => {
    fetchErrors();
  }, [fetchErrors]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Error Tracking</h1>
        <button
          onClick={() => fetchErrors()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh
        </button>
      </div>
      
      {errorsLoading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading errors...</div>
        </div>
      ) : errors.length > 0 ? (
        <div className="space-y-4">
          {errors.map((error, index) => (
            <div 
              key={`${error.session_id}-${index}`}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-red-500 text-lg">❌</span>
                    <span className="font-semibold text-gray-800 dark:text-white">
                      {error.agent}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {formatTime(error.timestamp)}
                    </span>
                  </div>
                  
                  <div className="text-red-600 dark:text-red-400 mb-2">
                    {error.error}
                  </div>
                  
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Session: {error.session_id.substring(0, 8)}...
                  </div>
                  
                  {error.context && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-sm text-blue-600 dark:text-blue-400 hover:underline">
                        View Context
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-x-auto">
                        {JSON.stringify(error.context, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <div className="text-4xl mb-4">✅</div>
          <div className="text-lg">No errors found</div>
          <div className="text-sm mt-2">Errors will appear here when they occur</div>
        </div>
      )}
    </div>
  );
};

export default Errors;