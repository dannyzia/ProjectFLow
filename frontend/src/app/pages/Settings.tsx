import { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';

export function Settings() {
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    const checkServerStatus = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/cwd', {
          method: 'GET',
        });
        if (response.ok) {
          setServerStatus('online');
        } else {
          setServerStatus('offline');
        }
      } catch (err) {
        setServerStatus('offline');
      }
    };

    checkServerStatus();
    
    // Check every 10 seconds
    const interval = setInterval(checkServerStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0f172a]">
      <Navbar />
      
      <div className="max-w-3xl mx-auto px-6 py-16">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-white mb-2">
            Settings
          </h1>
          <p className="text-[#cbd5e1]">
            Configure your Project Flow instance.
          </p>
        </div>

        <div className="space-y-6">
          {/* Server Status */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Server Status</h2>
            <div className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${
                serverStatus === 'checking' ? 'bg-gray-500' :
                serverStatus === 'online' ? 'bg-[#22c55e]' : 'bg-[#ef4444]'
              }`} />
              <span className="text-[#cbd5e1]">
                {serverStatus === 'checking' ? 'Checking...' :
                 serverStatus === 'online' ? 'localhost:8080 is responding' : 
                 'localhost:8080 is not responding'}
              </span>
            </div>
          </div>

          {/* AI Backend */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">AI Backend</h2>
            <div className="flex items-center gap-2">
              <span className="text-[#cbd5e1]">Connected to:</span>
              <span className="text-white font-mono text-sm">project-flow-api.onrender.com</span>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              API key is managed server-side.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
