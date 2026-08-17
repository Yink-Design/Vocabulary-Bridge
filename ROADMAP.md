# Roadmap

## v0.1 — Selection → MaiMemo

- Windows 全局快捷键捕获浏览器/PDF选中文本
- 弹窗确认/编辑
- 加入学习规划
- 可选 `advance=true`
- Token 存 Windows Credential Manager

## v0.2 — IELTS workflow

- 捕获历史
- 来源字段：Reading / Listening / Writing / Speaking
- 手动输入模式
- 单词重复状态提示
- 失败重试队列

## v0.3 — Authentication

- 在墨墨开放平台注册 Vocabulary Bridge 应用
- OIDC Authorization Code + PKCE（桌面应用）
- refresh token 自动续期
- 不在客户端内分发 client_secret

## v0.4 — Simulator integration

- 本地 IPC / localhost API
- IELTS Emulator 中选词直接调用 Vocabulary Bridge
- 自动记录 Cambridge book / test / passage 来源

## v0.5 — OCR

- 屏幕矩形框选
- OCR 单词识别
- 支持纯扫描 PDF
