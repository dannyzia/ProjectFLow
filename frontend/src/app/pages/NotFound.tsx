import { useNavigate } from 'react-router';
import { Navbar } from '../components/Navbar';

export function NotFound() {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-[#0f172a]">
      <Navbar />
      
      <div className="max-w-3xl mx-auto px-6 py-16 text-center">
        <h1 className="text-6xl font-semibold text-white mb-4">404</h1>
        <p className="text-xl text-[#cbd5e1] mb-8">Page not found</p>
        <button
          onClick={() => navigate('/')}
          className="bg-[#3b82f6] hover:bg-[#2563eb] text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Go Home
        </button>
      </div>
    </div>
  );
}
