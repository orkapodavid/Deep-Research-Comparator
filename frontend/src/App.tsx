import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Login } from './components/Login';
import { AgentsPage } from './components/AgentsPage';
import { ConversationHistory } from './components/ConversationHistory';
import { testAuthentication } from './utils/auth';
import { useState } from 'react';

function AuthenticatedApp() {
  const { isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return null; // This shouldn't happen as parent handles it
  }

  return (
    <Router>
      <div className="min-h-screen bg-[#F9F7F7]">
        <nav className="bg-[#213555] shadow-sm">
          <div className="max-w-6xl mx-auto px-0 py-3">
            <div className="flex justify-between items-center px-4">
              <Link to="/" className="text-xl font-bold text-[#F5EFE7]">
                Deep Research Comparator
              </Link>
              <div className="flex items-center space-x-4">
                <Link to="/" className="text-[#F5EFE7] hover:text-white transition-colors">
                  Home
                </Link>
                <Link to="/history" className="text-[#F5EFE7] hover:text-white transition-colors">
                  History
                </Link>
                <button
                  onClick={logout}
                  className="text-[#F5EFE7] hover:text-white transition-colors text-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<AgentsPage />} />
          <Route path="/history" element={<ConversationHistory />} />
        </Routes>
      </div>
    </Router>
  );
}

function AppMain() {
  const [loginError, setLoginError] = useState<string | null>(null);

  return (
    <AuthProvider>
      <AppContent loginError={loginError} setLoginError={setLoginError} />
    </AuthProvider>
  );
}

export default AppMain;

function AppContent({ loginError, setLoginError }: { 
  loginError: string | null; 
  setLoginError: (error: string | null) => void; 
}) {
  const { isAuthenticated, login } = useAuth();

  const handleLogin = async (username: string, password: string): Promise<boolean> => {
    setLoginError(null);
    
    const isValid = await testAuthentication(username, password);
    if (isValid) {
      login(username, password);
      return true;
    } else {
      setLoginError('Invalid username or password');
      return false;
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} error={loginError || undefined} />;
  }

  return <AuthenticatedApp />;
}