import { useEffect, useState } from 'react';
import useDashboardStore from './store/dashboardStore';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Overview from './pages/Overview';
import Sessions from './pages/Sessions';
import Monitoring from './pages/Monitoring';
import Analytics from './pages/Analytics';
import AgentView from './pages/AgentView';
import Errors from './pages/Errors';

function App() {
  const { 
    selectedView, 
    theme, 
    connect, 
    isConnected,
    connectionError,
    autoRefresh,
    refreshInterval,
    fetchPerformance,
    fetchSessions
  } = useDashboardStore();
  
  const [isLoading, setIsLoading] = useState(true);
  const [showConnectionWarning, setShowConnectionWarning] = useState(false);

  // Connect to WebSocket on mount with error handling
  useEffect(() => {
    const connectWithRetry = async () => {
      try {
        await connect();
        setIsLoading(false);
      } catch (error) {
        console.warn('Backend connection failed, running in offline mode:', error);
        setShowConnectionWarning(true);
        setIsLoading(false);
      }
    };
    
    connectWithRetry();
  }, [connect]);

  // Apply theme
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  // Auto-refresh data
  useEffect(() => {
    if (!autoRefresh || !isConnected) return;

    const interval = setInterval(() => {
      fetchPerformance().catch(console.error);
      if (selectedView === 'sessions') {
        fetchSessions().catch(console.error);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, isConnected, selectedView, fetchPerformance, fetchSessions]);

  const renderContent = () => {
    switch (selectedView) {
      case 'overview':
        return <Overview />;
      case 'sessions':
        return <Sessions />;
      case 'monitoring':
        return <Monitoring />;
      case 'analytics':
        return <Analytics />;
      case 'agents':
        return <AgentView />;
      case 'errors':
        return <Errors />;
      default:
        return <Overview />;
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        {showConnectionWarning && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 px-4 py-2">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              ⚠️ Running in offline mode. Connect backend for live data.
            </p>
          </div>
        )}
        {connectionError && (
          <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-4 py-2">
            <p className="text-sm text-red-800 dark:text-red-200">
              Connection Error: {connectionError}
            </p>
          </div>
        )}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto px-6 py-8">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;