import axios from 'axios';

// 设置请求头
axios.defaults.timeout = 90000000;

// post请求头
axios.defaults.headers['Content-Type'] = 'application/json';
var baseURL = "http://127.0.0.1:7000/";
const api = axios.create({
  baseURL: baseURL, // 设置为你的后端服务器地址
});

export default api;
