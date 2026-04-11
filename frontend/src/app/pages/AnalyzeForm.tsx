import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Navbar } from '../components/Navbar';
import { IdeSelector } from '../components/IdeSelector';
import { LoadingState } from '../components/LoadingState';
import { ErrorAlert } from '../components/ErrorAlert';
import { ResultsDisplay } from '../components/ResultsDisplay';
import { analyzeProject, getCwd, openFolder } from '../api/client';

export function AnalyzeForm() {
  const navigate = useNavigate();
  const [projectPath, setProjectPath] = useState('');
  const [selectedIdes, setSelectedIdes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ files_written: string[]; output_path: string } | null>(null);
  const [needsHint, setNeedsHint] = useState(false);
  const [hintPath, setHintPath] = useState('');

  const handleUseCwd = async () => {
    try {
      const data = await getCwd();
      setProjectPath(data.cwd);
    } catch (err) {
      setError('Failed to get current directory');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await analyzeProject({
        project_path: projectPath,
        ides: selectedIdes,
        hint_path: hintPath || undefined,
      });
      if ('needs_hint' in data && data.needs_hint) {
        setNeedsHint(true);
      } else {
        setResult(data as { files_written: string[]; output_path: string });
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAnother = () => {
    setResult(null);
    setProjectPath('');
    setSelectedIdes([]);
    setError(null);
    setNeedsHint(false);
    setHintPath('');
    navigate('/generate');
  };

  const handleOpenFolder = async () => {
    if (result) {
      try {
        await openFolder(result.output_path);
      } catch (err) {
        setError('Failed to open folder');
      }
    }
  };

  const isFormValid = projectPath.trim() && selectedIdes.length > 0;

  // Show results inline
  if (result) {
    return (
      <div className="min-h-screen bg-[#0f172a]">
        <Navbar />
        <div className="max-w-3xl mx-auto px-6 py-16">
          <ResultsDisplay
            filesWritten={result.files_written}
            outputPath={result.output_path}
            onGenerateAnother={handleGenerateAnother}
            onOpenFolder={handleOpenFolder}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f172a]">
      <Navbar />
      
      <div className="max-w-3xl mx-auto px-6 py-16">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-white mb-2">
            Smart Analyze
          </h1>
          <p className="text-[#cbd5e1]">
            Point to an existing project on your machine. AI reads your actual code and generates tailored config files.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Section A — Project Folder */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Project Folder</h2>
            
            <div>
              <label htmlFor="projectPath" className="block text-sm font-medium text-[#cbd5e1] mb-2">
                Path to your project <span className="text-[#ef4444]">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  id="projectPath"
                  type="text"
                  value={projectPath}
                  onChange={(e) => setProjectPath(e.target.value)}
                  placeholder="/Users/john/projects/my-app"
                  required
                  className="flex-1 bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={handleUseCwd}
                  className="px-4 py-2.5 bg-[#334155] hover:bg-[#475569] text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
                >
                  Use current directory
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                AI will read your code files to detect your tech stack and generate tailored configs.
              </p>
            </div>
          </div>

          {/* Section B — Choose Your IDEs */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Choose Your IDEs</h2>
            <IdeSelector selectedIdes={selectedIdes} onChange={setSelectedIdes} />
          </div>

          {/* Hint Section — shown when no config files were auto-detected */}
          {needsHint && (
            <div className="bg-[#1e293b] rounded-[12px] p-6 border border-yellow-600">
              <h2 className="text-lg font-semibold text-yellow-400 mb-2">Can't detect your tech stack</h2>
              <p className="text-sm text-[#cbd5e1] mb-3">
                The scanner looks for config files (<span className="text-white font-mono text-xs">package.json</span>, <span className="text-white font-mono text-xs">pyproject.toml</span>, <span className="text-white font-mono text-xs">Cargo.toml</span>, <span className="text-white font-mono text-xs">go.mod</span>, <span className="text-white font-mono text-xs">Dockerfile</span>, <span className="text-white font-mono text-xs">README.md</span>, etc.) and planning docs (<span className="text-white font-mono text-xs">docs/Plan/03-TECH-STACK.md</span>). It also samples source files as a fallback. None were found in that folder.
              </p>
              <p className="text-sm text-[#cbd5e1] mb-3">
                Point to any document that describes your stack — a <span className="text-white font-mono text-xs">TECH-STACK.md</span>, a <span className="text-white font-mono text-xs">README.md</span>, or any <span className="text-white font-mono text-xs">.md</span> / <span className="text-white font-mono text-xs">.txt</span> file that lists your languages and tools:
              </p>
              <input
                type="text"
                value={hintPath}
                onChange={(e) => setHintPath(e.target.value)}
                placeholder="/path/to/your/project/docs/Plan/03-TECH-STACK.md"
                className="w-full bg-[#0f172a] border border-gray-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <ErrorAlert message={error} />
          )}

          {/* Generate Button / Loading State */}
          {isLoading ? (
            <LoadingState mode="analyze" />
          ) : (
            <button
              type="submit"
              disabled={!isFormValid}
              className="w-full bg-[#3b82f6] hover:bg-[#2563eb] disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              Submit
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
