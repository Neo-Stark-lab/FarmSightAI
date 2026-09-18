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

  const handleDemoLogin = (userId: string) => {
    demoAuth.login(userId);
    navigate('/farms');
  };

  const demoUsers = [
    { id: 'user1', name: 'Arjun Kumar', email: 'arjun@example.com' },
    { id: 'user2', name: 'Meena Ravi', email: 'meena@example.com' },
    { id: 'user3', name: 'Kumaravel S', email: 'kumaravel@example.com' }
  ];

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

        <div className="bg-blue-50 text-blue-800 p-4 rounded-xl text-sm mb-8 text-center">
          <strong>Demo Authentication</strong><br />
          Select a demo account below to explore the application.
        </div>

        <div className="space-y-4">
          {demoUsers.map((user) => (
            <button
              key={user.id}
              onClick={() => handleDemoLogin(user.id)}
              className="w-full text-left bg-white border border-gray-200 hover:border-farm-DEFAULT hover:shadow-md p-4 rounded-xl transition-all flex items-center justify-between group"
            >
              <div>
                <p className="font-semibold text-gray-900 group-hover:text-farm-DEFAULT transition-colors">{user.name}</p>
                <p className="text-sm text-gray-500">{user.email}</p>
              </div>
              <ArrowRight size={20} className="text-gray-300 group-hover:text-farm-DEFAULT transition-colors group-hover:translate-x-1" />
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
