import { ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router';

export function Landing() {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-[#0f172a] flex flex-col items-center justify-center p-8 relative overflow-hidden">
      {/* Abstract code pattern background */}
      <div className="absolute inset-0 opacity-5 pointer-events-none overflow-hidden">
        <pre className="text-[#3b82f6] text-sm font-mono leading-relaxed whitespace-pre">
          {`const generateConfig = async () => {
  const rules = await analyzeProject();
  const config = buildAgentConfig(rules);
  return writeFiles(config);
};

function processFiles(files: string[]) {
  return files.map(f => analyze(f));
}

const IDE_CONFIGS = {
  vscode: '.vscode/instructions.md',
  cursor: '.cursor/rules.md',
  windsurf: '.windsurf/config.json'
};`.repeat(40)}
        </pre>
      </div>
      
      <div className="relative z-10 max-w-4xl mx-auto text-center">
        <h1 className="text-6xl font-semibold text-white mb-6">
          Project Flow
        </h1>
        <p className="text-2xl text-[#cbd5e1] mb-12">
          Generate AI config files for your developer projects.
        </p>
        
        <button
          onClick={() => navigate('/generate')}
          className="inline-flex items-center gap-2 bg-[#3b82f6] hover:bg-[#2563eb] text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Open Generator
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}
