// 配置文件，用于存储API地址和默认配置
// 从环境变量加载后端API地址，默认为localhost开发环境
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default {
  API_BASE_URL
}; 