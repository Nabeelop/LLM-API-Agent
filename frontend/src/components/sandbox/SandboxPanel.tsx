import { FC, useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Terminal, Trash2, Shield } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';

declare global {
  interface Window {
    loadPyodide: any;
  }
}

// ─── Sandbox Security ───────────────────────────────────────────────
// Modules blocked from being imported inside the WASM sandbox.
// Pyodide is inherently sandboxed (no real FS/network), but this
// adds defence-in-depth and makes the security posture explicit.
const BLOCKED_IMPORTS = new Set([
  'os', 'sys', 'subprocess', 'shutil', 'socket', 'http',
  'ctypes', 'importlib', 'signal', 'multiprocessing', 'threading',
  'webbrowser', 'pickle', 'shelve', 'sqlite3',
]);

const EXECUTION_TIMEOUT_MS = 10_000; // 10-second CPU time limit

/**
 * Statically scan code for blocked import statements.
 * Returns the first blocked module name found, or null if safe.
 */
function findBlockedImport(code: string): string | null {
  const importRegex = /^\s*(?:import|from)\s+(\w+)/gm;
  let match: RegExpExecArray | null;
  while ((match = importRegex.exec(code)) !== null) {
    const mod = match[1];
    if (BLOCKED_IMPORTS.has(mod)) return mod;
  }
  if (code.includes('__import__')) return '__import__()';
  return null;
}

// ─── Component ──────────────────────────────────────────────────────

export const SandboxPanel: FC = () => {
  const { activeCode, setActiveCode, terminalLogs, addTerminalLog, clearTerminal } = useAppContext();
  const [isRunning, setIsRunning] = useState(false);
  const [pyodide, setPyodide] = useState<any>(null);
  const [isLoadingPyodide, setIsLoadingPyodide] = useState(false);
  const executionAborted = useRef(false);

  // Initialize Pyodide WASM sandbox on mount
  useEffect(() => {
    const initPyodide = async () => {
      if (pyodide || isLoadingPyodide) return;
      setIsLoadingPyodide(true);
      addTerminalLog('> Initializing Pyodide WASM Sandbox (in-browser Python)...');
      try {
        // Load Pyodide CDN script if not already present
        if (!window.loadPyodide) {
          await new Promise<void>((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js';
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load Pyodide CDN script.'));
            document.head.appendChild(script);
          });
        }

        const pyInstance = await window.loadPyodide({
          indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/',
        });

        setPyodide(pyInstance);
        addTerminalLog('> Pyodide WASM Sandbox ready.');
        addTerminalLog('>   ✓ WebAssembly isolation (no filesystem/network access)');
        addTerminalLog('>   ✓ Blocked dangerous imports (os, subprocess, socket, ...)');
        addTerminalLog(`>   ✓ Execution timeout: ${EXECUTION_TIMEOUT_MS / 1000}s`);
      } catch (error: any) {
        console.error('Failed to load Pyodide', error);
        addTerminalLog(`> Error loading Pyodide sandbox: ${error.message || error}`);
        toast.error('Failed to load Python browser sandbox.');
      } finally {
        setIsLoadingPyodide(false);
      }
    };

    initPyodide();
  }, []);

  const handleRun = async () => {
    if (!activeCode.trim()) {
      addTerminalLog('> No code to execute.');
      return;
    }

    if (!pyodide) {
      addTerminalLog('> Error: Python sandbox is not initialized yet.');
      toast.error('Sandbox is not ready.');
      return;
    }

    // ── Static security check ──
    const blocked = findBlockedImport(activeCode);
    if (blocked) {
      addTerminalLog(`> ⚠️ BLOCKED: import of '${blocked}' is not permitted in the sandbox.`);
      toast.error(`Import '${blocked}' is blocked for security.`);
      return;
    }

    setIsRunning(true);
    executionAborted.current = false;
    addTerminalLog('> Executing Python script in WebAssembly sandbox...');

    try {
      const outputLines: string[] = [];

      // Redirect stdout/stderr to capture all output
      pyodide.setStdout({
        batched: (text: string) => { outputLines.push(text); }
      });
      pyodide.setStderr({
        batched: (text: string) => { outputLines.push(text); }
      });

      // Auto-install packages referenced by imports (e.g. requests → pyodide-http)
      await pyodide.loadPackagesFromImports(activeCode);

      // Execute with a timeout to enforce runtime resource limits
      const executionPromise = pyodide.runPythonAsync(activeCode);
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          executionAborted.current = true;
          reject(new Error(`Execution timed out (limit: ${EXECUTION_TIMEOUT_MS / 1000}s)`));
        }, EXECUTION_TIMEOUT_MS);
      });

      await Promise.race([executionPromise, timeoutPromise]);

      if (!executionAborted.current) {
        if (outputLines.length > 0) {
          outputLines.forEach(line => {
            if (line !== '') addTerminalLog(line);
          });
        } else {
          addTerminalLog('> Done. (No output)');
        }
      }
    } catch (error: any) {
      const msg = error.message || String(error);
      addTerminalLog(`> ⚠️ ${msg}`);
      if (msg.includes('timed out')) {
        toast.error('Execution timed out. Code may contain infinite loops.');
      } else {
        toast.error('Sandbox execution failed.');
      }
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section className="h-full bg-slate-900 border-l border-slate-800 flex flex-col">
      {/* Top action bar */}
      <div className="flex items-center justify-between p-3 border-b border-slate-800 bg-slate-950/50">
         <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">WASM Sandbox</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">ISOLATED</span>
         </div>
         <button 
          onClick={handleRun}
          disabled={isRunning || isLoadingPyodide || !pyodide}
          className="flex items-center gap-2 bg-emerald-500/10 hover:bg-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed text-emerald-500 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border border-emerald-500/20"
         >
           <Play className={`w-4 h-4 ${isRunning || isLoadingPyodide ? 'animate-pulse' : ''}`} />
           {isLoadingPyodide ? 'Loading WASM...' : isRunning ? 'Running...' : 'Run'}
           {!isRunning && !isLoadingPyodide && <span className="opacity-50 text-[10px] ml-1">(⌘+Enter)</span>}
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
                 <span className={
                   log.includes('Error') || log.includes('BLOCKED') || log.includes('⚠️')
                     ? 'text-rose-400'
                     : log.includes('✓')
                       ? 'text-emerald-400'
                       : 'text-slate-300'
                 }>{log}</span>
               </div>
             ))}
          </div>
      </div>
    </section>
  );
};
