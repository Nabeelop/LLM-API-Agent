import { AppLayout } from './components/layout/AppLayout';
import { Sidebar } from './components/sidebar/Sidebar';
import { ChatPanel } from './components/chat/ChatPanel';
import { SandboxPanel } from './components/sandbox/SandboxPanel';
import { AppProvider } from './context/AppContext';
import { Toaster } from './components/ui/sonner';

function App() {
  return (
    <AppProvider>
      <AppLayout 
        sidebar={<Sidebar />}
        chat={<ChatPanel />}
        sandbox={<SandboxPanel />}
      />
      <Toaster theme="dark" position="top-center" />
    </AppProvider>
  );
}

export default App;
