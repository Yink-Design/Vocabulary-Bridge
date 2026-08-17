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

### 3. 阅读正文里的词形变化

网页正文经常出现复数、过去式、进行时等形式，而墨墨词库通常按词典原形收录。

Vocabulary Bridge 会先查询你实际划到的拼写；只有原拼写查不到时，才生成少量常见原形候选，再交给墨墨词库确认。例如：

- `lettuces` → `lettuce`
- `strawberries` → `strawberry`
- `studied` → `study`
- `started` → `start`
- `running` → `run`
- `making` → `make`

候选词不会仅凭本地规则直接写入学习计划。必须由墨墨 `/api/v1/vocabulary/query` 返回真实 vocabulary ID 后才会继续。

## 支持范围

- 浏览器网页：Chrome / Edge / Firefox 等，只要选中文字可以复制即可。
- PDF：Adobe Acrobat、Edge PDF、Foxit 等有文本层的 PDF 可用。
- 默认全局快捷键：`F8`。
- 弹窗允许编辑捕获到的单词。
- Token 存入 Windows Credential Manager，不写入源码或配置文件。
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
原拼写 / 常见原形候选
   ↓ 墨墨词库确认 vocabulary ID
查询墨墨学习记录
   ↓
今日学习进度
┌──────────────┴──────────────┐
今日未完成                  今日已完成
   ↓                           ↓
已在规划 → 提前复习      写入本地明日队列
新词 → 加入并今天新学    第二天自动处理
```

## 墨墨 API 实现依据

本项目按墨墨官方 `maimemo/memo-api-cli` 的实际接口实现：

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

第一次运行会要求输入你的墨墨 Open API Token。

## 使用

1. 保持程序在系统托盘运行。
2. 在网页或 PDF 中拖选一个英文生词，例如 `precipitation`。
3. 按 `F8`。
4. 检查弹窗中的单词。
5. 点击 `按规则同步` 或按 Enter。
6. 程序自动返回以下结果之一：
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

### Token 有效期

当前采用个人 Open API Token。收到 HTTP 401 时提示重新配置。后续计划接入 OIDC + refresh token。

### 词形还原范围

当前只处理阅读中最常见的一批英语词形变化，且最终必须由墨墨词库验证。非常规派生词或复杂词形仍可能需要在弹窗中手动改成原形。

## 隐私与安全

- API Token 使用 Python `keyring` 保存，在 Windows 上进入 Credential Manager。
- `.gitignore` 已排除 `.env` 等敏感文件。
- 当前版本不会上传原句、网页地址或 PDF 内容；只向墨墨发送最终确认的单词或其经墨墨词库确认的原形。
- 明日队列只保存在本机 `%APPDATA%`。

## Roadmap

- [x] 网页 / PDF 选中文本捕获
- [x] `F8` 全局快捷键
- [x] 自动判断加入记忆 / 提前复习
- [x] 今日完成后顺延到明日
- [x] 常见复数 / 时态词形回退
- [x] Windows Credential Manager 保存 Token
- [x] 系统托盘
- [ ] OIDC 登录 + refresh token 自动续期
- [ ] IELTS 来源标签（Reading / Listening / Writing / Speaking）
- [ ] 剑雅模拟器直接调用 Bridge
- [ ] 扫描 PDF OCR 捕获
- [ ] GitHub Actions 自动构建 Windows EXE
