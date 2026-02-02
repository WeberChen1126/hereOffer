import request from '../utils/request';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const auth = {
  login: (data: any) => request.post('/auth/login', data),
  register: (data: any) => request.post('/auth/register', data),
};

export const jobs = {
  list: (params?: any) => request.get('/admin/jobs', { params }),
  get: (id: number) => request.get(`/admin/jobs/${id}`),
  create: (data: any) => request.post('/admin/jobs', data),
  update: (id: number, data: any) => request.put(`/admin/jobs/${id}`, data),
};

export const applications = {
  create: (data: FormData) => request.post('/applications', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: (params?: any) => request.get('/applications', { params }),
  get: (id: number) => request.get(`/applications/${id}`),
  updateStatus: (id: number, status: string) => request.post(`/applications/${id}/status`, { new_status: status }),
  adminUpdateStatus: (id: number, status: string) => request.put(`/admin/applications/${id}/status`, { status }),
  downloadResume: async (id: number) => {
    // 下载简历文件 - 使用 axios 直接请求，处理二进制文件
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/admin/applications/${id}/resume`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          responseType: 'blob', // 重要：设置为 blob 以处理二进制文件
        }
      );
      
      // 从响应头获取文件名，如果没有则使用默认名称
      const contentDisposition = response.headers['content-disposition'];
      let filename = `resume_${id}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
          // 处理 URL 编码的文件名
          try {
            filename = decodeURIComponent(filename);
          } catch (e) {
            // 如果解码失败，使用原始值
          }
        }
      }
      
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // 清理
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error: any) {
      console.error('下载简历失败:', error);
      if (error.response?.status === 401) {
        throw new Error('未授权，请重新登录');
      } else if (error.response?.status === 404) {
        throw new Error('简历文件不存在');
      } else {
        throw new Error(error.response?.data?.detail || '下载失败');
      }
    }
  }
};

export const chat = {
  createSession: (data: any) => request.post('/chat/sessions', data),
  getHistory: (sessionId: number) => request.get(`/chat/sessions/${sessionId}/messages`),
};

export const knowledge = {
  upload: (data: FormData) => request.post('/admin/knowledge/documents', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: () => request.get('/admin/knowledge/documents'),
  get: (id: number) => request.get(`/admin/knowledge/documents/${id}`),
  delete: (id: number) => request.delete(`/admin/knowledge/documents/${id}`),
};
