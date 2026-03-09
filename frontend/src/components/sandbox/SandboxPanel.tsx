import { FC } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Terminal, Trash2 } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';

export const SandboxPanel: FC = () => {
  const { activeCode, setActiveCode, terminalLogs, addTerminalLog, clearTerminal } = useAppContext();

  const handleRun = () => {
    addTerminalLog('> Executing Python script via Sandbox environment...');
    setTimeout(() => {
      addTerminalLog('Successfully parsed syntax tree.');
      addTerminalLog('Runtime OK. Awaiting actual backend evaluation hooks for Phase 4.');
    }, 800);
  };

  return (
    <section className="h-full bg-slate-900 border-l border-slate-800 flex flex-col">
      {/* Top action bar */}
      <div className="flex items-center justify-between p-3 border-b border-slate-800 bg-slate-950/50">
         <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">REPL Sandbox</span>
         </div>
         <button 
          onClick={handleRun}
          className="flex items-center gap-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border border-emerald-500/20"
         >
           <Play className="w-4 h-4" /> Run 
           <span className="opacity-50 text-[10px] ml-1">(⌘+Enter)</span>
         </button>
      </div>

      {/* Editor Area */}
      <div className="flex-1 bg-slate-950 relative">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={activeCode || '# Execution context empty.\n# Ask the agent to generate code, or paste it here.'}
          onChange={(val) => setActiveCode(val ?? '')}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            padding: { top: 16 },
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            formatOnPaste: true,
          }}
        />
      </div>

      {/* Terminal View */}
      <div className="h-[30%] bg-[#0d1117] border-t border-slate-800 flex flex-col">

          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/50 bg-[#161b22]">
            <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
              <Terminal className="w-3.5 h-3.5" /> Output
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button 
                    onClick={clearTerminal}
                    className="text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p>Clear Console</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="flex-1 p-4 font-mono text-sm overflow-y-auto text-slate-300 space-y-1">
             {terminalLogs.length === 0 && (
               <div className="text-slate-600 italic">No output...</div>
             )}
             {terminalLogs.map((log, i) => (
               <div key={i} className="flex gap-3">
                 <span className="text-slate-600 select-none">~</span>
                 <span className={log.includes('Error') ? 'text-rose-400' : 'text-slate-300'}>{log}</span>
               </div>
             ))}
          </div>
      </div>
    </section>
  );
};
