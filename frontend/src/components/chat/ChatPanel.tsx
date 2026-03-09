import { FC, useState, KeyboardEvent, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';
import { Copy, RefreshCw, Send, MessageSquare } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';
import { BackendAPI } from '../../api/client';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';

export const ChatPanel: FC = () => {
  const { messages, addMessage, isGenerating, setIsGenerating, setActiveCode, addTerminalLog } = useAppContext();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSend = async () => {
    if (!input.trim() || isGenerating) return;

    const query = input.trim();
    setInput('');
    addMessage({ role: 'user', content: query });
    setIsGenerating(true);

    try {
      const response = await BackendAPI.askPrompt(query);
      
      addMessage({ role: 'ai', content: response.answer });
      
      if (response.executable && response.code) {
        setActiveCode(response.code);
        addTerminalLog('> Code generated from AI response');
        toast.info('New executable code generated');
      }

    } catch (error) {
      toast.error('Failed to get response from AI');
      addMessage({ role: 'ai', content: '*Error: Could not reach the backend API.*' });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <section className="h-full bg-slate-950 flex flex-col p-4">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-4 mb-4">
        <MessageSquare className="w-5 h-5 text-primary" />
        <h2 className="text-sm font-semibold text-slate-200">Chat</h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-3">
            <MessageSquare className="w-8 h-8 opacity-50" />
            <p className="text-sm">How can I help you today?</p>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div 
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start group'}`}
          >
            {msg.role === 'user' ? (
              <div className="bg-slate-800 text-slate-300 rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] text-sm">
                {msg.content}
              </div>
            ) : (
              <div className="flex gap-3 max-w-[80%]">
                 <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 border border-primary/30">
                   <span className="text-primary text-xs font-bold">AI</span>
                 </div>
                 <div className="space-y-2 relative">
                   <div className="bg-slate-800/50 border border-slate-700/50 text-slate-300 rounded-2xl rounded-tl-sm px-4 py-3 text-sm prose prose-invert max-w-none">
                     <ReactMarkdown remarkPlugins={[remarkGfm]}>
                       {msg.content}
                     </ReactMarkdown>
                   </div>
                   
                   {/* Hover Actions */}
                   <TooltipProvider delayDuration={200}>
                     <div className="absolute -bottom-6 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                       <Tooltip>
                         <TooltipTrigger asChild>
                           <button 
                             onClick={() => handleCopy(msg.content)}
                             className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
                           >
                             <Copy className="w-3 h-3" /> Copy
                           </button>
                         </TooltipTrigger>
                         <TooltipContent side="bottom" className="text-xs">
                           <p>Copy text</p>
                         </TooltipContent>
                       </Tooltip>

                       <Tooltip>
                         <TooltipTrigger asChild>
                           <button className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors">
                             <RefreshCw className="w-3 h-3" /> Regenerate
                           </button>
                         </TooltipTrigger>
                         <TooltipContent side="bottom" className="text-xs">
                           <p>Retry message</p>
                         </TooltipContent>
                       </Tooltip>
                     </div>
                   </TooltipProvider>
                 </div>
              </div>
            )}
          </motion.div>
        ))}

        {/* Typing Indicator */}
        {isGenerating && (
          <div className="flex justify-start">
             <div className="flex gap-3">
               <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 border border-primary/30">
                 <span className="text-primary text-xs font-bold">AI</span>
               </div>
               <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1 h-[42px]">
                 <motion.div animate={{ y: [0, -3, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} className="w-1.5 h-1.5 bg-slate-400 rounded-full" />
                 <motion.div animate={{ y: [0, -3, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} className="w-1.5 h-1.5 bg-slate-400 rounded-full" />
                 <motion.div animate={{ y: [0, -3, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} className="w-1.5 h-1.5 bg-slate-400 rounded-full" />
               </div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-6 pt-2">
        <div className="relative group">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
            placeholder="Type a message..." 
            className="w-full bg-slate-900 border border-slate-700/50 rounded-xl py-3 pl-4 pr-12 text-sm text-slate-200 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-slate-500 disabled:opacity-50"
          />
          <button 
            onClick={handleSend}
            disabled={isGenerating || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-primary hover:bg-primary/90 disabled:bg-primary/50 disabled:cursor-not-allowed text-white transition-colors flex items-center justify-center group-focus-within:bg-primary"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <div className="text-center mt-2">
             <span className="text-[10px] text-slate-600">AI can make mistakes. Verify important information.</span>
        </div>
      </div>
    </section>
  );
};
