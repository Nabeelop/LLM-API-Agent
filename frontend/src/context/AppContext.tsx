import React, { createContext, useContext, useState, ReactNode } from 'react';

export type MessageRole = 'user' | 'ai';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface UploadState {
  filename: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
}

interface AppContextType {
  // Chat State
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  isGenerating: boolean;
  setIsGenerating: (val: boolean) => void;

  // Sandbox State
  activeCode: string;
  setActiveCode: (code: string) => void;
  terminalLogs: string[];
  addTerminalLog: (log: string) => void;
  clearTerminal: () => void;

  // Sidebar Upload State
  uploads: UploadState[];
  addUpload: (upload: UploadState) => void;
  updateUpload: (filename: string, progress: number, status: UploadState['status']) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [activeCode, setActiveCode] = useState<string>('');
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [uploads, setUploads] = useState<UploadState[]>([]);

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages((prev) => [
      ...prev,
      { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
    ]);
  };

  const addTerminalLog = (log: string) => {
    setTerminalLogs((prev) => [...prev, log]);
  };

  const clearTerminal = () => setTerminalLogs([]);

  const addUpload = (upload: UploadState) => {
    setUploads((prev) => [upload, ...prev]);
  };

  const updateUpload = (filename: string, progress: number, status: UploadState['status']) => {
    setUploads((prev) => 
      prev.map(u => u.filename === filename ? { ...u, progress, status } : u)
    );
  };

  return (
    <AppContext.Provider
      value={{
        messages,
        addMessage,
        isGenerating,
        setIsGenerating,
        activeCode,
        setActiveCode,
        terminalLogs,
        addTerminalLog,
        clearTerminal,
        uploads,
        addUpload,
        updateUpload,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
