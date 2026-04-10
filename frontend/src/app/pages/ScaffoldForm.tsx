import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Navbar } from '../components/Navbar';
import { IdeSelector } from '../components/IdeSelector';
import { LoadingState } from '../components/LoadingState';
import { ErrorAlert } from '../components/ErrorAlert';
import { ResultsDisplay } from '../components/ResultsDisplay';
import { scaffoldProject, getCwd, openFolder } from '../api/client';

export function ScaffoldForm() {
  const navigate = useNavigate();
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [outputPath, setOutputPath] = useState('');
  const [selectedIdes, setSelectedIdes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ files_written: string[]; output_path: string } | null>(null);

  const handleUseCwd = async () => {
    try {
      const data = await getCwd();
      setOutputPath(data.cwd);
    } catch (err) {
      setError('Failed to get current directory');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await scaffoldProject({
        project_name: projectName,
        project_description: projectDescription,
        output_path: outputPath,
        ides: selectedIdes,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to generate files');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAnother = () => {
    setResult(null);
    setProjectName('');
    setProjectDescription('');
    setOutputPath('');
    setSelectedIdes([]);
    setError(null);
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

  const isFormValid = projectName.trim() && projectDescription.trim() && outputPath.trim() && selectedIdes.length > 0;

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
            Quick Scaffold
          </h1>
          <p className="text-[#cbd5e1]">
            Generate standard AI config files using just a project name and description.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Section A — Project Info */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Project Info</h2>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="projectName" className="block text-sm font-medium text-[#cbd5e1] mb-2">
                  Project Name <span className="text-[#ef4444]">*</span>
                </label>
                <input
                  id="projectName"
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="my-awesome-app"
                  required
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="projectDescription" className="block text-sm font-medium text-[#cbd5e1] mb-2">
                  Project Description <span className="text-[#ef4444]">*</span>
                </label>
                <textarea
                  id="projectDescription"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="A REST API built with FastAPI and PostgreSQL..."
                  required
                  rows={4}
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:border-transparent resize-none"
                />
              </div>
            </div>
          </div>

          {/* Section B — Output Folder */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Output Folder</h2>
            
            <div>
              <label htmlFor="outputPath" className="block text-sm font-medium text-[#cbd5e1] mb-2">
                Where should the files be written? <span className="text-[#ef4444]">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  id="outputPath"
                  type="text"
                  value={outputPath}
                  onChange={(e) => setOutputPath(e.target.value)}
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
                Type the full path to your project folder. Files will be written there directly.
              </p>
            </div>
          </div>

          {/* Section C — Choose Your IDEs */}
          <div className="bg-[#1e293b] rounded-[12px] p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-6">Choose Your IDEs</h2>
            <IdeSelector selectedIdes={selectedIdes} onChange={setSelectedIdes} />
          </div>

          {/* Error Display */}
          {error && (
            <ErrorAlert message={error} />
          )}

          {/* Generate Button / Loading State */}
          {isLoading ? (
            <LoadingState mode="scaffold" />
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
