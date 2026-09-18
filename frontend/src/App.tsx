import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { Sprout, Menu, UserCircle } from 'lucide-react';
import { IS_DEMO_MODE } from './api/client';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import MyFarmsPage from './pages/MyFarmsPage';
import FarmSetupPage from './pages/FarmSetupPage';
import DashboardPage from './pages/DashboardPage';
import ZoneDetailPage from './pages/ZoneDetailPage';
import { demoAuth } from './utils/demoPersistence';
import type { ReactNode } from 'react';

const PrivateRoute = ({ children }: { children: ReactNode }) => {
  if (!demoAuth.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const Navigation = () => {
  const location = useLocation();
  const isLanding = location.pathname === '/';
  const isAuthed = demoAuth.isAuthenticated();

  // Hide main nav on login page to keep it clean
  if (location.pathname === '/login') return null;

  return (
    <header className={`px-6 py-4 flex items-center justify-between sticky top-0 z-50 transition-colors duration-300 ${isLanding ? 'bg-transparent absolute w-full' : 'bg-white border-b border-gray-100 shadow-sm'}`}>
      <div className="flex items-center gap-8">
        <Link to="/" className={`flex items-center gap-2 text-xl font-bold tracking-tight ${isLanding ? 'text-white' : 'text-farm-DEFAULT'}`}>
          <Sprout size={28} />
          FarmSight AI
        </Link>
        {isAuthed && !isLanding && (
          <nav className="hidden md:flex gap-6">
            <Link to="/farms" className="text-gray-600 hover:text-farm-DEFAULT font-medium transition-colors">
              My Farms
            </Link>
            <button onClick={(e) => e.preventDefault()} className="text-gray-600 hover:text-farm-DEFAULT font-medium transition-colors cursor-pointer">
              How it works
            </button>
          </nav>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className={`hidden md:block text-xs px-3 py-1 rounded-full font-medium tracking-wide ${isLanding ? 'bg-white/20 text-white backdrop-blur-sm' : 'bg-farm-light text-farm-dark'}`}>
          {IS_DEMO_MODE ? 'DEMO DATA • FIXTURES' : 'REAL DATA • LIVE'}
        </div>
        {isAuthed ? (
          <button 
            onClick={() => { demoAuth.logout(); window.location.href = '/'; }}
            className={`flex items-center gap-2 ${isLanding ? 'text-white hover:text-white/80' : 'text-gray-600 hover:text-farm-DEFAULT'} transition-colors`}
          >
            <UserCircle size={24} />
          </button>
        ) : (
          !isLanding && <Link to="/login" className="text-farm-DEFAULT font-medium hover:text-farm-dark transition-colors">Log In</Link>
        )}
        <button className={`md:hidden ${isLanding ? 'text-white' : 'text-gray-900'}`}>
          <Menu size={24} />
        </button>
      </div>
    </header>
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-surface selection:bg-farm-light selection:text-farm-dark font-sans text-gray-900">
        <Navigation />
        <main className="flex-grow flex flex-col relative">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/farms" element={<PrivateRoute><MyFarmsPage /></PrivateRoute>} />
            <Route path="/farms/new" element={<PrivateRoute><FarmSetupPage /></PrivateRoute>} />
            <Route path="/farms/:farmId" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
            <Route path="/farms/:farmId/zones/:zoneId" element={<PrivateRoute><ZoneDetailPage /></PrivateRoute>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
