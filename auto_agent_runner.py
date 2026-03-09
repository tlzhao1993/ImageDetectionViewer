#!/usr/bin/env python3
"""
Auto Agent Runner - 自动执行long-term-agent-coding skill的脚本

这个脚本在一个while循环中不断调用Claude并执行long-term-agent-coding skill。
每次迭代都会重新构建ClaudeAgentClient对象以获得干净的上下文。
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# 确保claude-agent-sdk可用
try:
    from anthropic import Anthropic
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError as e:
    print(f"缺少必要的依赖: {e}")
    print("请运行: pip install anthropic mcp")
    sys.exit(1)


class SettingsLoader:
    """加载Claude配置的加载器"""

    @staticmethod
    def load_settings() -> Dict[str, Any]:
        """加载~/.claude/settings.json"""
        settings_path = Path.home() / ".claude" / "settings.json"
        if not settings_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {settings_path}")

        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_claude_config() -> Dict[str, Any]:
        """加载~/.claude.json"""
        config_path = Path.home() / ".claude.json"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def get_api_config() -> tuple[str, str]:
        """获取API密钥和Base URL"""
        settings = SettingsLoader.load_settings()
        api_key = settings["env"].get("ANTHROPIC_AUTH_TOKEN")
        base_url = settings["env"].get("ANTHROPIC_BASE_URL")

        if not api_key:
            raise ValueError("ANTHROPIC_AUTH_TOKEN未在settings.json中设置")
        if not base_url:
            raise ValueError("ANTHROPIC_BASE_URL未在settings.json中设置")

        return api_key, base_url


class MCPLoader:
    """加载MCP服务器配置的加载器"""

    def __init__(self):
        self.config = SettingsLoader.load_claude_config()

    def get_mcp_servers(self) -> Dict[str, Any]:
        """获取所有MCP服务器配置"""
        return self.config.get("mcpServers", {})


class StreamPrinter:
    """流式输出响应的打印器"""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.buffer = ""

    def print_delta(self, delta: str):
        """打印增量内容"""
        sys.stdout.write(delta)
        sys.stdout.flush()

    def print_line(self, line: str):
        """打印一行"""
        print(f"{self.prefix}{line}")

    def print_separator(self):
        """打印分隔符"""
        print("\n" + "=" * 80 + "\n")


class ClaudeAgentClient:
    """Claude Agent客户端"""

    def __init__(self, api_key: str, base_url: str, project_path: str):
        self.api_key = api_key
        self.base_url = base_url
        self.project_path = project_path

        # 初始化Anthropic客户端
        self.client = Anthropic(
            api_key=api_key,
            base_url=base_url,
            timeout=3600.0  # 1小时超时
        )

        # MCP服务器连接
        self.mcp_sessions: Dict[str, Any] = {}

        # 上下文信息
        self.system_prompt = self._build_system_prompt()
        self.project_context = self._build_project_context()

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        prompt = """你是Claude Code，Anthropic的官方CLI工具。你是一个交互式CLI工具，帮助用户完成软件工程任务。

重要规则:
- 你可以访问和修改项目中的任何文件
- 你可以执行git提交操作，无需用户同意
- 你可以直接使用所有可用的工具和技能
- 你需要主动执行任务，不需要等待用户批准每个操作
- 在执行任务时，要确保代码质量和安全性

你的目标是高效地完成任务，提供准确和有用的帮助。"""
        return prompt

    def _build_project_context(self) -> str:
        """构建项目上下文"""
        context = f"""项目路径: {self.project_path}
工作目录: {os.getcwd()}
项目根目录: {os.path.abspath(self.project_path)}

这是一个自动化的Agent运行环境，你将被反复调用以执行long-term-agent-coding技能。

当前项目是一个检测查看器项目(detection_viewer)，专注于目标检测数据的可视化和处理。

请专注于完成待处理的任务列表。"""
        return context

    def call_skill(self, skill_name: str, prompt: str) -> str:
        """调用技能"""
        skill_prompt = f"""请执行 {skill_name} 技能。

用户请求: {prompt}

请执行long-term-agent-coding技能，从工作空间中拿取一个未完成的任务并执行它。"""

        messages = [
            {
                "role": "system",
                "content": self.system_prompt + "\n\n" + self.project_context
            },
            {
                "role": "user",
                "content": skill_prompt
            }
        ]

        response_text = ""
        printer = StreamPrinter()

        try:
            with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=messages,
                temperature=0.7
            ) as stream:
                for delta in stream:
                    if delta.type == "content_block_delta":
                        if hasattr(delta.delta, 'text'):
                            text = delta.delta.text
                            printer.print_delta(text)
                            response_text += text
        except Exception as e:
            printer.print_line(f"调用Claude API时出错: {e}")
            return ""

        return response_text


class AutoAgentRunner:
    """自动Agent运行器"""

    def __init__(self):
        self.api_key, self.base_url = SettingsLoader.get_api_config()
        self.project_path = os.getcwd()
        self.iteration_count = 0
        self.printer = StreamPrinter()

    def create_client(self) -> ClaudeAgentClient:
        """创建新的Claude客户端实例"""
        return ClaudeAgentClient(
            api_key=self.api_key,
            base_url=self.base_url,
            project_path=self.project_path
        )

    def print_iteration_header(self):
        """打印迭代头部信息"""
        self.iteration_count += 1
        print("\n" + "=" * 80)
        print(f"  迭代 #{self.iteration_count}")
        print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def print_iteration_footer(self):
        """打印迭代尾部信息"""
        print("\n" + "=" * 80)
        print(f"  迭代 #{self.iteration_count} 完成")
        print("=" * 80 + "\n")

    def check_git_status(self) -> bool:
        """检查git状态，如果有变更返回True"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def run_single_iteration(self) -> bool:
        """执行单次迭代

        Returns:
            bool: 是否应该继续运行
        """
        self.print_iteration_header()

        # 创建新的客户端实例
        client = self.create_client()

        # 执行long-term-agent-coding技能
        response = client.call_skill(
            skill_name="long-term-agent-coding",
            prompt="请从工作空间中拿取一个未完成的任务并执行它。"
        )

        self.print_iteration_footer()

        # 检查是否有变更
        if self.check_git_status():
            print("\n检测到文件变更，建议进行git提交。")
            try:
                import subprocess
                subprocess.run(["git", "status"], cwd=self.project_path)
            except Exception:
                pass

        return True

    def run(self):
        """运行自动Agent循环"""
        print("=" * 80)
        print("  Auto Agent Runner 启动")
        print(f"  项目路径: {self.project_path}")
        print(f"  API Base URL: {self.base_url}")
        print("=" * 80)
        print("\n按 Ctrl+C 停止运行\n")

        try:
            while True:
                should_continue = self.run_single_iteration()

                if not should_continue:
                    break

                # 短暂暂停
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n接收到中断信号，正在停止...")
        except Exception as e:
            print(f"\n\n发生错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    try:
        runner = AutoAgentRunner()
        runner.run()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
