interface IdeSelectorProps {
  selectedIdes: string[];
  onChange: (ides: string[]) => void;
}

const IDES = [
  { id: 'vscode', name: 'VS Code', icon: 'V' },
  { id: 'kilo', name: 'Kilo Code', icon: 'K' },
  { id: 'cursor', name: 'Cursor', icon: 'C' },
  { id: 'windsurf', name: 'Windsurf', icon: 'W' },
  { id: 'zed', name: 'Zed', icon: 'Z' },
  { id: 'void', name: 'Void', icon: 'V' },
  { id: 'cline', name: 'Cline', icon: 'C' },
  { id: 'claudecode', name: 'Claude Code', icon: 'C' },
  { id: 'antigravity', name: 'Antigravity', icon: 'A' },
];

export function IdeSelector({ selectedIdes, onChange }: IdeSelectorProps) {
  const toggleIde = (ideId: string) => {
    if (selectedIdes.includes(ideId)) {
      onChange(selectedIdes.filter((id) => id !== ideId));
    } else {
      onChange([...selectedIdes, ideId]);
    }
  };
  
  return (
    <div>
      <label className="block text-sm font-medium text-[#cbd5e1] mb-4">
        Which AI-powered IDEs do you use? (select all that apply)
      </label>
      <div className="grid grid-cols-3 gap-3">
        {IDES.map((ide) => {
          const isSelected = selectedIdes.includes(ide.id);
          return (
            <button
              key={ide.id}
              type="button"
              onClick={() => toggleIde(ide.id)}
              className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all ${
                isSelected
                  ? 'border-[#3b82f6] bg-[#3b82f6]/10'
                  : 'border-gray-700 bg-[#1e293b] hover:border-gray-600'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium ${
                  isSelected
                    ? 'bg-[#3b82f6] text-white'
                    : 'bg-gray-700 text-[#cbd5e1]'
                }`}
              >
                {ide.icon}
              </div>
              <span className={`text-sm font-medium ${isSelected ? 'text-[#3b82f6]' : 'text-white'}`}>
                {ide.name}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
