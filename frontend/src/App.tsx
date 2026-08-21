import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import ReportEmergency from './pages/ReportEmergency';
import AIAnalyzing from './pages/AIAnalyzing';
import ResponseInProgress from './pages/ResponseInProgress';
import Header from './components/Header';
import OfflineBanner from './components/OfflineBanner';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <div className="page-content items-center justify-center">Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;
  
  return <>{children}</>;
}

function App() {
  return (
    <div className="app-container">
      <OfflineBanner />
      <Header />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/report" element={<ProtectedRoute><ReportEmergency /></ProtectedRoute>} />
        <Route path="/analyzing/:incidentId" element={<ProtectedRoute><AIAnalyzing /></ProtectedRoute>} />
        <Route path="/response/:incidentId" element={<ProtectedRoute><ResponseInProgress /></ProtectedRoute>} />
      </Routes>
    </div>
  );
}

export default App;
