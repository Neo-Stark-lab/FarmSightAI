import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';
import { IS_DEMO_MODE } from './api/client';
import LandingPage from './pages/LandingPage';
import FarmSetupPage from './pages/FarmSetupPage';
import DashboardPage from './pages/DashboardPage';
import ZoneDetailPage from './pages/ZoneDetailPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <header className="bg-farm-dark text-white p-4 shadow-md">
          <div className="container mx-auto flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-xl font-bold">
              <Sprout size={28} />
              FarmSight AI
            </Link>
            <div className="text-sm opacity-80 bg-white/10 px-3 py-1 rounded-full">
              {IS_DEMO_MODE ? 'DEMO DATA — Fixture analysis' : 'REAL DATA — Live providers'}
            </div>
          </div>
        </header>

        <main className="flex-grow flex flex-col relative">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/setup" element={<FarmSetupPage />} />
            <Route path="/farms/:farmId" element={<DashboardPage />} />
            <Route path="/farms/:farmId/zones/:zoneId" element={<ZoneDetailPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
