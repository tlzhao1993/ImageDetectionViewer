# Auto Agent Runner - 使用说明

这个目录包含两个脚本，用于自动持续运行 `long-term-agent-coding` skill，完成项目中的任务。

## 脚本说明

### 1. `auto_agent_runner.sh` (Bash版本)
Bash脚本，使用子进程调用Claude CLI并处理流式输出。

**特点：**
- 使用Bash编写，简单直接
- 支持彩色输出
- 自动日志记录
- 智能流式JSON解析
- 优雅的Ctrl+C处理

### 2. `auto_agent_runner.py` (Python版本 - 推荐)
Python脚本，提供更强大的功能。

**特点：**
- 使用Python编写，功能更强大
- 更好的流式输出处理
- 实时显示思考过程和工具调用
- 完整的日志记录
- 清晰的彩色输出
- 信号处理和优雅退出
- 更好的错误处理

## 使用方法

### 快速开始（推荐Python版本）

```bash
# 运行Python版本（推荐）
./auto_agent_runner.py

# 或者直接用python运行
python3 auto_agent_runner.py
```

### 运行Bash版本

```bash
# 运行Bash版本
./auto_agent_runner.sh

# 或者用bash运行
bash auto_agent_runner.sh
```

### 配置选项

#### 限制最大迭代次数

```bash
# 设置最多运行10次迭代后停止
MAX_ITERATIONS=10 ./auto_agent_runner.py

# Bash版本
MAX_ITERATIONS=10 ./auto_agent_runner.sh
```

#### 设置无限制运行

```bash
# 设置一个很大的数字
MAX_ITERATIONS=999999 ./auto_agent_runner.py
```

## 工作原理

1. **初始化检查**
   - 检查Claude CLI是否安装
   - 检查tasks.json是否存在
   - 统计剩余任务数量

2. **每次迭代**
   - 打印当前迭代信息
   - 显示最高优先级的未完成任务
   - 调用Claude执行 `long-term-agent-coding` skill
   - 实时流式显示Claude的输出
   - 记录执行日志
   - 检查任务完成情况

3. **迭代间等待**
   - 每次迭代后等待5秒
   - 给系统稳定的时间

4. **日志记录**
   - 所有操作记录到 `agent_logs/` 目录
   - 包含时间戳和详细信息
   - 每次迭代有单独的输出文件

## 停止运行

任何时候按 `Ctrl+C` 即可优雅停止脚本。

## 日志文件

脚本会在 `agent_logs/` 目录下创建以下文件：

- `agent_run_YYYYMMDD_HHMMSS.log` - 主日志文件
- `claude_output_N.json` - 每次迭代的Claude原始流式JSON输出

## 输出说明

### 彩色输出标识

- `✓` (绿色) - 成功消息
- `✗` (红色) - 错误消息
- `⚠` (黄色) - 警告消息
- `ℹ` (蓝色) - 信息消息
- `→` (紫色) - 流式输出/工具调用
- `🔧` (紫色) - 工具调用开始

### 流式输出事件（Python版本）

Python版本使用 `stream-json` 格式，实时显示以下事件：

1. **思考过程**
   - 显示Claude正在思考的文本内容
   - 实时输出，无需等待完整响应

2. **工具调用**
   - `🔧 Tool Call: Read` - 工具调用开始
   - `Input: ...` - 工具输入参数（实时更新）
   - `→ Tool call completed` - 工具调用完成
   - `→ Result: ✓ SUCCESS` - 工具执行结果

3. **消息状态**
   - `→ Claude started` - 开始生成响应
   - `✓ Message completed: end_turn` - 消息完成
   - `✓ Message completed: stop_sequence` - 提前停止

4. **错误信息**
   - `✗ Error: ...` - 错误消息
   - `→ Result: ✗ FAILED` - 工具调用失败

### 输出内容

1. **迭代开始**
   - 迭代编号
   - 工作目录
   - 剩余任务数
   - 当前任务信息

2. **Claude执行**（实时流式输出）
   - 思考过程的实时显示
   - 工具调用和执行状态的实时更新
   - 工具结果的即时反馈
   - 完整的工作进度追踪

3. **迭代结束**
   - 执行时长
   - 完成的任务数

4. **最终摘要**
   - 总迭代次数
   - 初始/剩余任务数
   - 总完成任务数

## 注意事项

1. **权限设置**
   - 脚本使用 `--dangerously-skip-permissions` 标志
   - 仅在受信任的环境中运行
   - 建议在隔离的Docker容器中运行

2. **Claude CLI路径**
   - Python版本默认路径：`/home/tlzhao/local/node-v24.13.1-linux-x64/bin/claude`
   - 如需修改，编辑脚本中的 `CLAUDE_BINARY` 变量

3. **tasks.json格式**
   - 必须存在 `tasks.json` 文件
   - 任务必须有 `passes` 字段
   - 任务按优先级排序（数组顺序）

4. **磁盘空间**
   - 日志文件会不断增长
   - 定期清理 `agent_logs/` 目录

## 故障排除

### Claude CLI未找到

```
✗ Claude CLI is not installed or not in PATH
```

**解决方法：**
1. 检查Claude CLI是否已安装
2. 检查脚本中的路径是否正确
3. 将Claude添加到PATH

### tasks.json未找到

```
✗ tasks.json not found in current directory
```

**解决方法：**
1. 确认在正确的项目目录下运行
2. 确认 `tasks.json` 文件存在

### 权限错误

**解决方法：**
```bash
chmod +x auto_agent_runner.py
chmod +x auto_agent_runner.sh
```

### 流式输出不工作

**解决方法：**
1. 使用Python版本（更稳定的流式输出）
2. 确保终端支持ANSI颜色代码

## 示例输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Auto Agent Runner Starting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ Configuration:
  - Working Directory: /home/tlzhao/detection_viewer
  - Log Directory: ./agent_logs
  - Max Iterations: 100

✓ Claude CLI found: /home/tlzhao/local/node-v24.13.1-linux-x64/bin/claude
✓ Found tasks.json in working directory
ℹ Initial tasks remaining: 47

⚠ Press Ctrl+C to stop the execution

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Starting Iteration #1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ Working Directory: /home/tlzhao/detection_viewer
ℹ Remaining Tasks: 47
ℹ Current Task (highest priority):
  Category: functional
  Description: Implement JSON parsing for prediction files...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running Long-Term Agent Coding Skill
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ Claude Output (Streaming):
────────────────────────────────────────

→ Claude started

I'll start by examining the project structure to understand the current state...

🔧 Tool Call: Bash
  Input: pwd
/home/tlzhao/detection_viewer
  → Tool call completed
  → Result: ✓ SUCCESS

🔧 Tool Call: Read
  Input: {"file_path": "tasks.json"}
[content displayed...]
  → Tool call completed
  → Result: ✓ SUCCESS

Based on the analysis, I'll implement the JSON parsing feature...

🔧 Tool Call: Write
  Input: {"file_path": "app/parsers/json_parser.py", "content": "..."}
  → Tool call completed
  → Result: ✓ SUCCESS

✓ Message completed: end_turn

────────────────────────────────────────

✓ Claude execution completed

ℹ Iteration Duration: 2m 15s
✓ Tasks completed this iteration: 1
```

## 技术细节

### Claude CLI参数

**Python版本（使用stream-json）：**
- `--print` - 非交互式模式，输出到stdout
- `--dangerously-skip-permissions` - 跳过权限检查
- `--output-format stream-json` - 流式JSON输出格式
- `--verbose` - 启用详细输出（stream-json需要）
- `请执行下一个任务` - 触发long-term-agent-coding skill的提示

**Bash版本（使用stream-json）：**
- `--print` - 非交互式模式，输出到stdout
- `--dangerously-skip-permissions` - 跳过权限检查
- `--output-format stream-json` - 流式JSON输出格式
- `--include-partial-messages` - 包含部分消息块
- `--verbose` - 启用详细输出（stream-json需要）
- `请执行下一个任务` - 触发long-term-agent-coding skill的提示

### 日志格式

```
[YYYY-MM-DD HH:MM:SS] Log message
```

## 开发说明

如需修改脚本：

1. **Bash版本**：编辑 `auto_agent_runner.sh`
2. **Python版本**：编辑 `auto_agent_runner.py`

主要配置变量：
- `MAX_ITERATIONS` - 最大迭代次数
- `CLAUDE_BINARY` - Claude CLI路径
- `LOG_DIR` - 日志目录

## 许可证

与主项目相同。
