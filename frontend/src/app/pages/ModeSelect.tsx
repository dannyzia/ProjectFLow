import { useNavigate } from 'react-router';
import { Navbar } from '../components/Navbar';

export function ModeSelect() {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-[#0f172a]">
      <Navbar />
      
      <div className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-semibold text-white mb-4">
            Choose Your Mode
          </h1>
          <p className="text-lg text-[#cbd5e1]">
            How would you like to generate your config files?
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-6">
          {/* Quick Scaffold Card */}
          <div className="bg-[#1e293b] rounded-[12px] p-8 border border-gray-700 hover:border-[#3b82f6] transition-all cursor-pointer group">
            <div className="text-5xl mb-4">⚡</div>
            <h2 className="text-2xl font-semibold text-white mb-3">
              Quick Scaffold
            </h2>
            <p className="text-[#cbd5e1] mb-6 leading-relaxed">
              Generate standard AI config files using just a project name and description. No code analysis. Done in seconds.
            </p>
            <button
              onClick={() => navigate('/generate/scaffold')}
              className="w-full bg-[#3b82f6] hover:bg-[#2563eb] text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              Choose Scaffold →
            </button>
          </div>
          
          {/* Smart Analyze Card */}
          <div className="bg-[#1e293b] rounded-[12px] p-8 border border-gray-700 hover:border-[#3b82f6] transition-all cursor-pointer group">
            <div className="text-5xl mb-4">🔍</div>
            <h2 className="text-2xl font-semibold text-white mb-3">
              Smart Analyze
            </h2>
            <p className="text-[#cbd5e1] mb-6 leading-relaxed">
              Point to an existing project on your machine. AI reads your actual code and generates tailored config files.
            </p>
            <button
              onClick={() => navigate('/generate/analyze')}
              className="w-full bg-[#3b82f6] hover:bg-[#2563eb] text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              Choose Analyze →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
