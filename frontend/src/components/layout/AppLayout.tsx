import { FC, ReactNode } from 'react';
import { motion } from 'framer-motion';

interface AppLayoutProps {
  sidebar: ReactNode;
  chat: ReactNode;
  sandbox: ReactNode;
}

export const AppLayout: FC<AppLayoutProps> = ({ sidebar, chat, sandbox }) => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="h-screen w-screen bg-slate-950 text-slate-200 overflow-hidden flex"
    >
      {/* Sidebar: Fixed width */}
      <motion.div 
        initial={{ width: 0, opacity: 0 }}
        animate={{ width: 280, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeInOut', delay: 0.2 }}
        className="flex-shrink-0 border-r border-slate-800 bg-slate-900"
      >
        {sidebar}
      </motion.div>

      {/* Main Chat Area: Flexible width */}
      <main className="flex-1 min-w-[320px] bg-slate-950 flex flex-col relative">
        {chat}
      </main>

      {/* Right Sandbox Panel: Fixed width */}
      <motion.aside 
        initial={{ x: 50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.3 }}
        className="w-[500px] xl:w-[600px] flex-shrink-0 border-l border-slate-800 bg-slate-900"
      >
        {sandbox}
      </motion.aside>
    </motion.div>
  );
};
