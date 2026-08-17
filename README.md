# IELTS Vocabulary Bridge

一个面向 IELTS 阅读 / 听力复盘 / 写作 / 口语复盘的 Windows 生词捕获器。

核心目标：

> 在网页或 PDF 中选中生词 → 按 `F8` → 确认 → 程序自动判断该加入记忆、提前复习，还是顺延到明天。

## 当前逻辑

### 1. 已经在记忆规划中的词

- 今日学习任务尚未完成 → 调用 `advance_study`，提前到今天复习。
- 今日学习任务已经完成 → 暂存到本地“明日队列”，第二天在今日任务尚未完成时自动提前复习。

### 2. 还没有加入记忆规划的词

- 今日学习任务尚未完成 → 加入学习规划，并用 `advance=true` 安排今天新学。
- 今日学习任务已经完成 → 暂存到本地“明日队列”，第二天在今日任务尚未完成时自动加入并安排新学。

程序不做词书归属判定。只要墨墨开放词库能够解析该单词，就按上述规则处理。

### 3. 词形回退与二次确认

墨墨开放 API 的 vocabulary 接口按 `spelling` 查询，公开接口没有提供 lemma / 词形还原字段。因此 Vocabulary Bridge 在原拼写查不到时，才会生成少量常见原形候选，并交给墨墨词库再次验证。

示例：

```text
lettuces → lettuce
strawberries → strawberry
studied → study
running → run
```

如果启用了词形回退，程序不会直接加入，而是弹出二次确认：

```text
您想加入的词是不是：lettuce？

是  → 按 lettuce 继续智能同步
否  → 回到输入框，手动修改正确拼写后再次同步
```

如果原拼写本身就能被墨墨识别，不增加这一步。

## Token 管理

当前版本支持手动 Open API Token：

- Token 保存到 Windows Credential Manager，不写入源码或配置文件。
- 程序启动时自动发送一次只读 vocabulary 请求验证当前 Token。
- 收到 `401` 时判定 Token 已失效，弹出 Token 窗口，并自动打开墨墨官方 Token 领取页：
  `https://open.maimemo.com/open/api/v1/tokens/openapi`
- 用户在浏览器登录、复制新 Token，粘贴到窗口后点击“保存并验证”即可。
- 网络故障或服务器错误不会被误判成 Token 失效。

墨墨官方另有 OIDC 授权方式。官方 `memo-api-cli` 已实现 PKCE 登录、`offline_access`、refresh token 和 access token 自动刷新。Vocabulary Bridge 后续会优先接入这一路径，从而取消周期性手动复制 Token。

## 支持范围

- 浏览器网页：Chrome / Edge / Firefox 等，只要选中文字可以复制即可。
- PDF：Adobe Acrobat、Edge PDF、Foxit 等有文本层的 PDF 可用。
- 默认全局快捷键：`F8`。
- 弹窗允许编辑捕获到的单词。
- 右下角系统托盘常驻，可手动捕获、更新 Token 或退出。

## 工作流程

```text
网页 / PDF
   ↓ 选中单词
F8
   ↓
读取当前选中文字（临时 Ctrl+C）
   ↓
Vocabulary Bridge 小弹窗
   ↓ 确认
原拼写能否被墨墨识别？
   ├─ 能 → 直接继续
   └─ 不能 → 尝试常见原形 → 墨墨验证 → 用户二次确认
                                      ↓
                              查询墨墨学习记录
                                      ↓
                                今日学习进度
                         ┌────────────┴────────────┐
                       今日未完成               今日已完成
                           ↓                       ↓
                  已在规划 → 提前复习       写入本地明日队列
                  新词 → 加入并今天新学     第二天自动处理
```

## 墨墨 API 实现依据

本项目按墨墨官方 `maimemo/memo-api-cli` 与开放平台文档实现：

1. `POST /api/v1/vocabulary/query`
   - 单词拼写 → vocabulary ID
2. `POST /api/v1/study/query_study_records`
   - 判断单词是否已经存在学习记录 / 记忆规划
3. `POST /api/v1/study/get_study_progress`
   - 获取今日 `finished / total`
4. `POST /api/v1/study/add_words`
   - 新词加入记忆
   - `advance=true` 时带入当前学习流程
5. `POST /api/v1/study/advance_study`
   - 已在记忆规划的词提前复习
6. API Base URL：`https://open.maimemo.com/open/`
7. Bearer Token 放在 `Authorization` Header。

参考：
- 墨墨开放平台：`https://memodocs.maimemo.com/docs/open/`
- 官方 CLI：`https://github.com/maimemo/memo-api-cli`

## 安装（开发版）

建议 Windows 10/11 + Python 3.10 以上。

```powershell
git clone https://github.com/Yink-Design/Vocabulary-Bridge.git
cd Vocabulary-Bridge
git switch fix/f8-smart-routing
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m vocab_bridge
```

第一次运行会要求输入墨墨 Open API Token。

## 使用

1. 保持程序在系统托盘运行。
2. 在网页或 PDF 中拖选一个英文生词，例如 `precipitation`。
3. 按 `F8`。
4. 检查弹窗中的单词。
5. 点击 `按规则同步` 或按 Enter。
6. 若触发词形回退，先确认程序找到的原形。
7. 程序自动返回以下结果之一：
   - `✓ 已在记忆规划，已提前到今天复习`
   - `✓ 新词，已加入记忆并安排今天新学`
   - `✓ …今日任务已完成，已顺延到明日…`

### 明日队列

队列保存在：

```text
%APPDATA%\IELTSVocabularyBridge\pending_words.json
```

第二天程序启动时会尝试同步。如果当天任务已经完成，则继续保留，等下一次符合“今日未完成”条件时处理。

### 多选了句子怎么办？

弹窗内容可编辑。例如误选：

```text
annual precipitation levels
```

直接改成：

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

## 当前限制

### 扫描型 PDF

如果 PDF 只有图片、没有文本层，就无法直接选中复制。本版本暂不内置 OCR。

### Token 自动续期

当前分支会自动检测 Token 是否失效并打开官方领取页，但仍需要用户复制粘贴新的手动 Token。真正的无感续期需要切换到墨墨官方 OIDC + refresh token 认证流程。

## 隐私与安全

- API Token 使用 Python `keyring` 保存，在 Windows 上进入 Credential Manager。
- `.gitignore` 已排除 `.env` 等敏感文件。
- 当前版本不会上传原句、网页地址或 PDF 内容；只向墨墨发送最终确认的单词。
- 明日队列只保存在本机 `%APPDATA%`。

## Roadmap

- [x] 网页 / PDF 选中文本捕获
- [x] `F8` 全局快捷键
- [x] 自动判断加入记忆 / 提前复习
- [x] 今日完成后顺延到明日
- [x] 常见词形回退 + 二次确认
- [x] 启动时自动验证手动 Token
- [x] Token 失效时打开官方领取页
- [x] Windows Credential Manager 保存 Token
- [x] 系统托盘
- [ ] OIDC 登录 + refresh token 自动续期
- [ ] IELTS 来源标签（Reading / Listening / Writing / Speaking）
- [ ] 剑雅模拟器直接调用 Bridge
- [ ] 扫描 PDF OCR 捕获
- [ ] GitHub Actions 自动构建 Windows EXE
