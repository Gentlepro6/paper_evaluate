import axios from 'axios';

// 创建 axios 实例
const instance = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器
instance.interceptors.request.use(
  config => {
    console.log('发送请求:', {
      url: config.url,
      method: config.method,
      params: config.params,
      data: config.data
    });
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器
instance.interceptors.response.use(
  response => {
    console.log('响应数据:', response.data);
    return response;
  },
  error => {
    console.error('响应错误:', error.response || error);
    return Promise.reject(error);
  }
);

export default instance;
