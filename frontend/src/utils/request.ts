import axios from 'axios';
import { message } from 'antd';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data;
    if (!res) {
      message.error('响应格式错误');
      return Promise.reject(new Error('响应格式错误'));
    }
    if (res.code !== 0) {
      message.error(res.message || '错误');
      // 处理 401 等错误
      if (res.code === 1001) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      return Promise.reject(new Error(res.message || '错误'));
    }
    return res;
  },
  (error) => {
    // HTTP 层面的错误处理
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    console.error('Request Error:', error);
    const errorMessage = error.response?.data?.message || error.message || '请求失败';
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

export default request;
