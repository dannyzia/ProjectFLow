import { Link, useLocation } from 'react-router';

export function Navbar() {
  const location = useLocation();
  
  return (
    <nav className="bg-[#1e293b] border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="text-xl font-semibold text-white hover:text-[#3b82f6] transition-colors">
            Project Flow
          </Link>
          
          {/* Nav Links */}
          <div className="flex items-center gap-6">
            <Link 
              to="/generate" 
              className={`text-sm font-medium transition-colors ${
                location.pathname.startsWith('/generate') 
                  ? 'text-[#3b82f6]' 
                  : 'text-[#cbd5e1] hover:text-white'
              }`}
            >
              Generator
            </Link>
            <Link 
              to="/settings" 
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/settings' 
                  ? 'text-[#3b82f6]' 
                  : 'text-[#cbd5e1] hover:text-white'
              }`}
            >
              Settings
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
