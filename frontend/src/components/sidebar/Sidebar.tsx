import { FC, useRef } from 'react';
import { Search, UploadCloud, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { Progress } from '../ui/progress';
import { useAppContext } from '../../context/AppContext';
import { BackendAPI } from '../../api/client';
import { toast } from 'sonner';

export const Sidebar: FC = () => {
  const { uploads, addUpload, updateUpload } = useAppContext();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input
    e.target.value = '';

    // Optimistically add upload state
    addUpload({ filename: file.name, progress: 0, status: 'uploading' });

    try {
      await BackendAPI.uploadDocument(file, (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          updateUpload(file.name, percentCompleted, percentCompleted === 100 ? 'completed' : 'uploading');
        }
      });
      toast.success('Document uploaded and indexed successfully!', {
        description: file.name
      });
    } catch (error) {
      updateUpload(file.name, 0, 'error');
      toast.error('Failed to upload document', {
        description: file.name
      });
    }
  };

  return (
    <aside className="h-full bg-slate-900 border-r border-slate-800 flex flex-col p-4 w-full">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-slate-200">Context & Files</h2>
      </div>
      
      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input 
          type="text" 
          placeholder="Search context..." 
          className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-9 pr-3 text-sm text-slate-300 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-slate-600"
        />
      </div>

      {/* Upload Section */}
      <div className="mb-6 space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Documents</div>
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1 font-medium"
          >
            <UploadCloud className="w-3.5 h-3.5" /> Upload File
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".pdf,.txt,.md"
          />
        </div>
        
        <div className="space-y-2">
          {uploads.length === 0 && (
            <div className="text-xs text-slate-600 text-center py-4 border border-dashed border-slate-800 rounded-lg">
              No documents uploaded yet
            </div>
          )}
          {uploads.map((upload) => (
            <div key={upload.filename} className="bg-slate-800/30 border border-slate-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm text-slate-300 overflow-hidden pr-2">
                  <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span className="truncate">{upload.filename}</span>
                </div>
                {upload.status === 'uploading' ? (
                  <span className="text-xs text-primary font-medium">{upload.progress}%</span>
                ) : upload.status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
                )}
              </div>
              {upload.status === 'uploading' && (
                <Progress value={upload.progress} className="h-1" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* History Section */}
      <div className="flex-1 overflow-y-auto min-h-0 space-y-1">
         <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider sticky top-0 bg-slate-900 py-2 mb-2">Recent Chats</div>
         <div className="text-xs text-slate-600 italic px-2">History empty</div>
      </div>
    </aside>
  );
};
