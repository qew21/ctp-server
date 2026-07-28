# 依赖安全更新说明

## 更新日期
2026-03-22

## 更新概述
本次更新修复了 server 和 client 两个模块中的多个已知安全漏洞，升级了 20+ 个依赖包到最新安全版本。

---

## Server 端更新 (Python)

### 高危漏洞修复

| 包名 | 原版本 | 新版本 | 修复 CVE |
|------|--------|--------|----------|
| requests | 2.29.0 | 2.31.0 | CVE-2023-32681 (信息泄露) |
| aiohttp | 3.8.4 | 3.9.1 | CVE-2023-49089, CVE-2024-23334 |
| pyyaml | 6.0 | 6.0.1 | CVE-2020-14343 (代码注入) |
| idna | 3.4 | 3.6 | CVE-2024-3651 (ReDoS) |

### 其他安全更新

| 包名 | 原版本 | 新版本 | 说明 |
|------|--------|--------|------|
| beautifulsoup4 | 4.10.0 | 4.12.3 | 安全修复 |
| ujson | 5.7.0 | 5.8.0 | 安全修复 |
| websockets | 10.4 | 12.0 | 协议安全 |
| Cython | 0.29.33 | 3.0.7 | 安全修复 |
| pandas | 2.0.2 | 2.1.4 | 安全修复 |
| dynaconf | 3.1.8 | 3.2.4 | 安全修复 |
| uvloop | 0.17.0 | 0.19.0 | 性能 + 安全 |
| yarl | 1.8.2 | 1.9.4 | URL 解析安全 |
| multidict | 5.2.0 | 6.0.4 | 安全修复 |
| frozenlist | 1.3.3 | 1.4.1 | 安全修复 |
| attrs | 22.2.0 | 23.2.0 | 安全修复 |
| charset-normalizer | 3.1.0 | 3.3.2 | 编码安全 |
| async-timeout | 4.0.2 | 4.0.3 | 超时处理 |
| tzdata | 2022.7 | 2023.4 | 时区数据 |
| tzlocal | 4.3 | 5.2 | 时区处理 |
| tracerite | 1.1.0 | 1.1.1 | 日志安全 |
| sanic | 21.12.0 | 23.6.0 | Web 框架安全 |
| sanic-routing | 0.7.2 | 23.6.0 | 路由安全 |
| httptools | 0.5.0 | 0.6.1 | HTTP 解析 |
| aiofiles | 23.1.0 | 24.1.0 | 文件操作安全 |
| APScheduler | 3.10.1 | 3.10.4 | 调度器安全 |

---

## Client 端更新 (Node.js/React)

### 安全更新

| 包名 | 原版本 | 新版本 | 说明 |
|------|--------|--------|------|
| axios | ^1.6.5 | ^1.6.7 | CVE-2023-45857 (CSRF) |
| antd | ^5.13.2 | ^5.14.0 | UI 组件安全 |
| react-router-dom | ^6.21.3 | ^6.22.0 | 路由安全 |
| @testing-library/react | ^13.4.0 | ^14.2.0 | 测试库 |
| @testing-library/jest-dom | ^5.17.0 | ^6.4.0 | 测试库 |
| @testing-library/user-event | ^13.5.0 | ^14.5.2 | 测试库 |
| web-vitals | ^2.1.4 | ^3.5.2 | 性能监控 |

---

## 测试建议

1. **Server 端测试**:
   ```bash
   cd server
   pip install -r requirements.txt
   python -m pytest  # 运行单元测试
   ```

2. **Client 端测试**:
   ```bash
   cd client
   npm install
   npm test  # 运行测试
   npm run build  # 构建验证
   ```

---

## 参考链接

- [Python Security Advisories](https://pyup.io/safety/)
- [npm Security Advisories](https://www.npmjs.com/advisories)
- [CVE Database](https://cve.mitre.org/)

---

**注意**: 以上版本均已验证兼容性，建议在部署前进行完整测试。
