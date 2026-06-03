import axios from 'axios';

// The centralized axios client pointing to the FastAPI backend running on localhost:8000
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000, 
});

export interface AskResponse {
  answer: string;
  executable: boolean;
  code: string | null;
}

export const BackendAPI = {
  askPrompt: async (query: string): Promise<AskResponse> => {
    const { data } = await apiClient.post<AskResponse>('/ask', { query });
    return data;
  },

  uploadDocument: async (
    file: File,
    onUploadProgress?: (progressEvent: any) => void
  ) => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return data;
  },

  executeCode: async (code: string): Promise<{ output: string }> => {
    const { data } = await apiClient.post<{ output: string }>('/execute', { code });
    return data;
  },
};
