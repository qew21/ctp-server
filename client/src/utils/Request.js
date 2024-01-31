import axios from 'axios';

// 设置请求头
axios.defaults.timeout = 90000000;

// post请求头
axios.defaults.headers['Content-Type'] = 'application/json';
var host = window.location.hostname; // 获取域名（不包括端口）
var protocol = window.location.protocol; // 获取协议（例如 'http:' 或 'https:'）
var port = "7000"; // 设置新端口
var baseURL = protocol + "//" + host + ":" + port + "/"; // 拼接新的 baseURL
const api = axios.create({
  baseURL: baseURL, // 设置为你的后端服务器地址
});

export default api;
