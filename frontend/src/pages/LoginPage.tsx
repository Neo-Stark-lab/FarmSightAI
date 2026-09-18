import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sprout, Lock, Mail, ArrowRight } from 'lucide-react';
import { demoAuth } from '../utils/demoPersistence';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // If already authenticated, redirect to /farms
  useEffect(() => {
    if (demoAuth.isAuthenticated()) {
      navigate('/farms', { replace: true });
    }
  }, [navigate]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    demoAuth.login();
    navigate('/farms');
  };

  const handleDemoLogin = () => {
    demoAuth.login();
    navigate('/farms');
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-farm-light opacity-50 blur-3xl" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-farm-DEFAULT/10 opacity-50 blur-3xl" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md bg-white rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8 md:p-12 relative z-10"
      >
        <div className="text-center mb-10">
          <div className="w-16 h-16 bg-farm-light text-farm-DEFAULT rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Sprout size={32} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Welcome back</h1>
          <p className="text-gray-500">Sign in to your Digital Farm Twin</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-farm-DEFAULT/20 focus:border-farm-DEFAULT transition-shadow"
                placeholder="farmer@example.com"
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-farm-DEFAULT/20 focus:border-farm-DEFAULT transition-shadow"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button 
            type="submit"
            className="w-full bg-gray-900 hover:bg-black text-white font-medium py-3 rounded-xl transition-colors mt-2"
          >
            Continue
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-gray-100">
          <div className="bg-blue-50 text-blue-800 p-4 rounded-xl text-sm mb-4">
            <strong>Hackathon Demo Mode:</strong> You may bypass the full authentication system to explore the application.
          </div>
          <button 
            onClick={handleDemoLogin}
            type="button"
            className="w-full bg-farm-DEFAULT hover:bg-farm-secondary text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-farm-DEFAULT/20 flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98]"
          >
            Continue as demo farmer <ArrowRight size={18} />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
