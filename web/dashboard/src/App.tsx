import { useEffect } from 'react';
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

  // Connect to WebSocket on mount
  useEffect(() => {
    connect().catch(console.error);
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
      fetchPerformance();
      if (selectedView === 'sessions') {
        fetchSessions();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, isConnected, selectedView, fetchPerformance, fetchSessions]);

  const renderView = () => {
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

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        {/* Connection Status */}
        {connectionError && (
          <div className="bg-red-500 text-white px-4 py-2 text-sm">
            Connection Error: {connectionError}
          </div>
        )}
        
        {!isConnected && !connectionError && (
          <div className="bg-yellow-500 text-white px-4 py-2 text-sm">
            Connecting to server...
          </div>
        )}
        
        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 p-6">
          {renderView()}
        </main>
      </div>
    </div>
  );
}

export default App;
