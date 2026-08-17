# IELTS Vocabulary Bridge

一个面向 IELTS 阅读 / 听力复盘 / 写作 / 口语复盘的 Windows 生词捕获器。

核心目标只有一条：

> 在网页或 PDF 中选中生词 → 按快捷键 → 选择加入墨墨学习规划。

## 当前 MVP

- 浏览器网页：Chrome / Edge / Firefox 等，只要选中文字可以复制即可。
- PDF：Adobe Acrobat、Edge PDF、Foxit 等有文本层的 PDF 可用。
- 默认全局快捷键：`Ctrl + Alt + M`。
- 弹窗允许编辑捕获到的单词。
- 两种同步动作：
  - **加入学习规划**：调用墨墨 `study/add_words`，`advance=false`。
  - **加入并提前复习**：调用同一接口，`advance=true`。
- Token 存入 Windows Credential Manager，不写入源码或配置文件。
- 右下角系统托盘常驻，可手动捕获、更新 Token 或退出。

## 工作流程

```text
网页 / PDF
   ↓ 选中单词
Ctrl + Alt + M
   ↓
读取当前选中文字（临时 Ctrl+C）
   ↓
Vocabulary Bridge 小弹窗
   ├─ 加入学习规划
   ├─ 加入并提前复习
   └─ 取消
   ↓
墨墨 Open API
   ↓
墨墨学习规划
```

## 墨墨 API 实现依据

本项目按墨墨官方 `maimemo/memo-api-cli` 的实际接口实现：

1. `POST /api/v1/vocabulary/query`
   - 输入 `spellings`
   - 解析对应 vocabulary ID
2. `POST /api/v1/study/add_words`
   - `words: [{ id: ... }]`
   - `advance: false/true`
3. API Base URL：`https://open.maimemo.com/open/`
4. Bearer Token 放在 `Authorization` Header。

参考：
- 墨墨开放平台：`https://memodocs.maimemo.com/docs/open/`
- 官方 CLI：`https://github.com/maimemo/memo-api-cli`

## 安装（开发版）

建议 Windows 10/11 + Python 3.10 以上。

```powershell
git clone https://github.com/Yink-Design/Vocabulary-Bridge.git
cd Vocabulary-Bridge
git switch feature/v0.1-mvp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m vocab_bridge
```

第一次运行会要求输入你的墨墨 Open API Token。

## 使用

1. 保持程序在系统托盘运行。
2. 在网页或 PDF 中拖选一个英文生词，比如 `precipitation`。
3. 按 `Ctrl + Alt + M`。
4. 检查弹窗里的词是否正确。
5. 点击：
   - `加入学习规划`；或
   - `加入并提前复习`。
6. 成功后弹窗会自动关闭。

### 多选了句子怎么办？

弹窗里的内容是可编辑的。例如误选：

```text
annual precipitation levels
```

可以直接改成：

```text
precipitation
```

再提交。

## 打包成 EXE

PowerShell：

```powershell
.\build.ps1
```

生成：

```text
dist/IELTS-Vocabulary-Bridge.exe
```

以后可以把这个 EXE 放进 Windows 启动项，让它开机后直接常驻。

## 当前限制

### 1. 扫描型 PDF

如果 PDF 只是图片、没有文本层，就无法直接“选中并复制”单词。本 MVP 不内置 OCR。后续可以增加截图 OCR 捕获模式。

### 2. Token 有效期

当前版本采用已经申请到的个人 Open API Token。收到 HTTP 401 时会提示重新配置 Token。

后续版本计划接入墨墨开放平台 OIDC，实现浏览器登录和 refresh token 自动续期。

### 3. 词形还原

MVP 不擅自把 `inhabitants` 改成 `inhabitant`，也不自动猜 lemma。这样可以避免程序把正确词形改错。查不到时可以直接在弹窗中修改。

## 隐私与安全

- API Token 使用 Python `keyring` 保存，在 Windows 上进入 Credential Manager。
- `.gitignore` 已排除 `.env` 等敏感文件。
- 项目不会记录 Token。
- 当前版本不会上传原句、网页地址或 PDF 内容；只向墨墨发送最终确认提交的单词。

## Roadmap

- [x] 网页 / PDF 选中文本捕获
- [x] Windows 全局快捷键
- [x] 加入墨墨学习规划
- [x] 可选提前复习
- [x] Windows Credential Manager 保存 Token
- [x] 系统托盘
- [ ] OIDC 登录 + refresh token 自动续期
- [ ] 可配置快捷键
- [ ] 本地捕获历史 / 撤销
- [ ] IELTS 来源标签（Reading / Listening / Writing / Speaking）
- [ ] 剑雅模拟器直接调用 Bridge
- [ ] 扫描 PDF OCR 捕获
- [ ] GitHub Actions 自动构建 Windows EXE
