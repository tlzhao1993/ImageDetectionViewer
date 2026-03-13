#!/usr/bin/env python3
"""
Auto Agent Runner - Continuous Long-Term Agent Coding
This script continuously runs long-term-agent-coding skill in a loop
"""

import os
import sys
import json
import subprocess
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Configuration
LOG_DIR = Path("./agent_logs")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "100"))
WORKING_DIR = Path.cwd()
CLAUDE_BINARY = "/home/tlzhao/local/node-v24.13.1-linux-x64/bin/claude"

class Logger:
    """Simple logger for the agent runner"""
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Write message to log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Use append mode instead of read-rewrite for better performance
        with self.log_file.open(mode='a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

class AgentRunner:
    """Main agent runner class"""

    def __init__(self):
        self.iteration = 0
        self.stop_requested = False
        self.log_dir = LOG_DIR
        self.log_dir.mkdir(exist_ok=True)

        # Create current log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log = self.log_dir / f"agent_run_{timestamp}.log"
        self.logger = Logger(self.current_log)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self.logger.log("=== Auto Agent Runner Started ===")

    def _handle_signal(self, signum, frame):
        """Handle interrupt signals"""
        self.stop_requested = True
        print()
        self.print_warning("Received interrupt signal, stopping...")
        self.logger.log("Interrupted by user")

    @staticmethod
    def print_header(message: str):
        """Print a header"""
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"{Colors.CYAN}{message}{Colors.END}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    @staticmethod
    def print_success(message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")

    @staticmethod
    def print_error(message: str):
        """Print error message"""
        print(f"{Colors.RED}✗{Colors.END} {message}")

    @staticmethod
    def print_warning(message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

    @staticmethod
    def print_info(message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

    @staticmethod
    def print_stream(message: str):
        """Print stream message"""
        print(f"{Colors.MAGENTA}→{Colors.END} {message}")

    def check_claude(self) -> bool:
        """Check if Claude binary exists"""
        if Path(CLAUDE_BINARY).exists():
            self.print_success(f"Claude CLI found: {CLAUDE_BINARY}")
            self.logger.log(f"Claude CLI found: {CLAUDE_BINARY}")
            return True
        else:
            # Try to find claude in PATH
            try:
                which_result = subprocess.run(['which', 'claude'],
                                           capture_output=True,
                                           text=True)
                if which_result.returncode == 0:
                    self.print_success(f"Claude CLI found: {which_result.stdout.strip()}")
                    self.logger.log(f"Claude CLI found: {which_result.stdout.strip()}")
                    return True
            except Exception:
                pass

            self.print_error("Claude CLI is not installed or not in PATH")
            self.logger.log("ERROR: Claude CLI not found")
            return False

    def check_remaining_tasks(self) -> int:
        """Count remaining tasks in tasks.json"""
        try:
            with open('tasks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            remaining = sum(1 for task in data if not task.get('passes', False))
            return remaining
        except Exception as e:
            self.print_error(f"Could not read tasks.json: {e}")
            return 0

    def get_current_task(self) -> Optional[dict]:
        """Get the highest priority uncompleted task"""
        try:
            with open('tasks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            for task in data:
                if not task.get('passes', False):
                    return task
            return None
        except Exception:
            return None

    def check_git_status(self):
        """Check git status"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'],
                                   capture_output=True,
                                   text=True)
            if result.stdout.strip():
                self.print_warning("Git working directory has uncommitted changes")
                self.logger.log("Git has uncommitted changes")
            else:
                self.print_success("Git working directory is clean")
                self.logger.log("Git working directory is clean")
        except Exception:
            pass

    def run_claude_stream(self, iteration_num: int) -> bool:
        """Run Claude with streaming output including thinking and tool calls"""
        start_time = time.time()

        # Create output files
        claude_output_raw = self.log_dir / f"claude_output_{iteration_num}_raw.txt"

        self.print_header("Running Long-Term Agent Coding Skill")
        self.logger.log(f"Executing Claude with long-term-agent-coding skill")

        print()
        self.print_stream(f"Saving raw output to: {claude_output_raw}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.END}")

        # Prepare Claude command with stream-json format
        cmd = [
            CLAUDE_BINARY,
            '--print',
            '--dangerously-skip-permissions',
            '--output-format', 'stream-json',
            '--verbose',
            '/long-term-agent-coding 请执行下一个任务. CRITICAL: YOU ONLY NEED TO COMPLETE ONE TASK SINCE THERE ARE MORE SESSIONS THAT WILL COMPLETE THE OTHER TASKS, AND DO NOT COVER THE ORIGINAL CONTENTS IN THE PROGRESS.TXT!'
        ]

        # Run Claude and capture raw output
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                cwd=str(WORKING_DIR)
            )

            raw_output = []
            line_count = 0

            print()
            self.print_info("Capturing raw output...")

            # Read output line by line and process in real-time
            for line_bytes in iter(process.stdout.readline, b''):
                line = line_bytes.decode('utf-8', errors='ignore')
                raw_output.append(line)
                line_count += 1

                # Try to parse as JSON and process immediately
                if line.strip():
                    try:
                        data = json.loads(line)
                        self._process_stream_chunk(data)
                        sys.stdout.flush()
                    except json.JSONDecodeError:
                        pass

                # Show progress periodically
                if line_count % 50 == 0:
                    sys.stdout.write(f"\rLines processed: {line_count}")
                    sys.stdout.flush()

            process.wait()

            # Save raw output to file
            print()
            claude_output_raw.write_text(''.join(raw_output), encoding='utf-8')
            self.print_success(f"Saved {line_count} lines to {claude_output_raw}")
            self.logger.log(f"Saved raw output: {line_count} lines to {claude_output_raw}")

            if process.returncode != 0:
                self.print_error(f"Claude exited with code {process.returncode}")
                self.logger.log(f"Claude exited with code {process.returncode}")
                return False

            self.print_success("Claude execution completed")
            self.logger.log("Claude execution completed")

        except Exception as e:
            self.print_error(f"Error running Claude: {e}")
            self.logger.log(f"Error running Claude: {e}")
            return False

        finally:
            print(f"{Colors.CYAN}{'─' * 40}{Colors.END}")

        # Calculate duration
        duration = int(time.time() - start_time)
        minutes = duration // 60
        seconds = duration % 60

        print()
        self.print_info(f"Iteration Duration: {minutes}m {seconds}s")
        self.logger.log(f"Iteration #{iteration_num} completed in {minutes}m {seconds}s")

        return True

    def _process_stream_chunk(self, data: dict):
        """Process a single stream chunk and display it appropriately"""
        chunk_type = data.get('type', 'unknown')

        # Handle the actual JSON format from Claude CLI
        if chunk_type == 'stream_event':
            # Extract the nested event
            event = data.get('event', {})
            event_type = event.get('type', 'unknown')

            # Process the nested event
            self._process_nested_event(event)

        elif chunk_type == 'assistant':
            # Full assistant message
            message = data.get('message', {})
            content = message.get('content', [])
            for item in content:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    if text:
                        sys.stdout.write(text)
                        sys.stdout.flush()
                elif item.get('type') == 'thinking':
                    thinking = item.get('thinking', '')
                    if thinking:
                        sys.stdout.write('\n')
                        sys.stdout.write(f"{Colors.BLUE}💭 Thinking:{Colors.END}\n")
                        sys.stdout.write(thinking)
                        sys.stdout.flush()

        else:
            # Unknown type - log it
            self.logger.log(f"Unknown chunk type: {chunk_type}")

    def _process_nested_event(self, event: dict):
        """Process a nested stream event"""
        event_type = event.get('type', 'unknown')

        if event_type == 'message_start':
            # Message started
            sys.stdout.write('\n')
            sys.stdout.write(f"{Colors.BOLD}→ Claude started{Colors.END}\n")
            sys.stdout.write('\n')
            sys.stdout.flush()

        elif event_type == 'content_block_start':
            # Content block started
            sys.stdout.write('\n')  # Add newline before each new content block
            content_block = event.get('content_block', {})
            content_type = content_block.get('type', '')

            if content_type == 'text':
                # Text content block - show a subtle indicator
                sys.stdout.write('\n')
                sys.stdout.write(f"{Colors.CYAN}▶ Response:{Colors.END}\n")
                sys.stdout.flush()
            elif content_type == 'thinking':
                # Thinking block
                sys.stdout.write('\n')
                sys.stdout.write(f"{Colors.BLUE}💭 Thinking:{Colors.END}\n")
                sys.stdout.flush()
            elif content_type == 'tool_use':
                # Tool call started - extract name and input
                tool_name = content_block.get('name', 'unknown')
                tool_input = content_block.get('input', {})
                self._print_tool_call_start(tool_name, tool_input)

        elif event_type == 'content_block_delta':
            # Content delta
            delta = event.get('delta', {})
            delta_type = delta.get('type', '')

            if delta_type == 'text_delta':
                # Text content
                text = delta.get('text', '')
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
            elif delta_type == 'thinking_delta':
                # Thinking content
                thinking = delta.get('thinking', '')
                if thinking:
                    sys.stdout.write(thinking)
                    sys.stdout.flush()

        elif event_type == 'content_block_stop':
            # Content block stopped
            # Add newline after content block for better separation
            sys.stdout.write('\n')
            sys.stdout.flush()

        elif event_type == 'message_delta':
            # Message delta (stop reason, etc.)
            delta = event.get('delta', {})
            stop_reason = delta.get('stop_reason')
            if stop_reason:
                sys.stdout.write('\n')
                sys.stdout.write(f"{Colors.GREEN}✓ Message completed: {stop_reason}{Colors.END}\n")
                sys.stdout.flush()

        elif event_type == 'message_stop':
            # Message completely stopped
            sys.stdout.write('\n')
            sys.stdout.write(f"{Colors.GREEN}✓ Message stream finished{Colors.END}\n")
            sys.stdout.flush()

    def _print_tool_call_start(self, tool_name: str, tool_input: dict = None):
        """Print formatted tool call start"""
        sys.stdout.write(f"{Colors.MAGENTA}🔧 Tool Call: {Colors.BOLD}{tool_name}{Colors.END}\n")
        if tool_input and isinstance(tool_input, dict):
            # Display tool input parameters in a readable format
            sys.stdout.write(f"{Colors.MAGENTA}   Input:{Colors.END}\n")
            for key, value in tool_input.items():
                # Convert value to string and truncate if too long
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                sys.stdout.write(f"   {Colors.YELLOW}{key}:{Colors.END} {value_str}\n")
        sys.stdout.flush()
        self.logger.log(f"Tool call started: {tool_name}")

    def _print_tool_call_end(self):
        """Print formatted tool call end"""
        sys.stdout.write(f"{Colors.MAGENTA}   → Tool call completed{Colors.END}\n")
        sys.stdout.flush()
        self.logger.log("Tool call completed")

    def _print_tool_result(self, tool_name: str, is_error: bool):
        """Print formatted tool result"""
        status = f"{Colors.RED}✗ FAILED{Colors.END}" if is_error else f"{Colors.GREEN}✓ SUCCESS{Colors.END}"
        sys.stdout.write(f"{Colors.MAGENTA}   → Result: {status}{Colors.END}\n")
        sys.stdout.flush()
        self.logger.log(f"Tool result: {tool_name} - {'error' if is_error else 'success'}")

    def run_iteration(self, iteration_num: int) -> bool:
        """Run a single iteration of the agent"""
        self.print_header(f"Starting Iteration #{iteration_num}")
        self.logger.log(f"=== Starting Iteration #{iteration_num} ===")

        print()
        self.print_info(f"Working Directory: {WORKING_DIR}")
        self.print_info(f"Log File: {self.current_log}")
        self.print_info(f"Max Iterations: {MAX_ITERATIONS}")

        # Check remaining tasks
        remaining = self.check_remaining_tasks()
        self.print_info(f"Remaining Tasks: {remaining}")
        self.logger.log(f"Remaining tasks: {remaining}")

        if remaining == 0:
            self.print_success("All tasks completed!")
            self.logger.log("All tasks completed, stopping execution")
            return False  # Stop the loop

        # Check git status
        self.check_git_status()

        # Print current task info
        print()
        self.print_info("Current Task (highest priority):")
        current_task = self.get_current_task()
        if current_task:
            category = current_task.get('category', 'N/A')
            description = current_task.get('description', 'N/A')
            print(f"  Category: {category}")
            print(f"  Description: {description[:80]}...")
            self.logger.log(f"Current task: {description[:50]}...")

        # Run Claude
        if not self.run_claude_stream(iteration_num):
            # If Claude failed, we might want to continue anyway
            pass

        # Check if tasks were modified
        new_remaining = self.check_remaining_tasks()
        if new_remaining < remaining:
            completed = remaining - new_remaining
            self.print_success(f"Tasks completed this iteration: {completed}")
            self.logger.log(f"Tasks completed this iteration: {completed}")

        return True  # Continue the loop

    def run(self):
        """Main execution loop"""
        self.print_header("Auto Agent Runner Starting")
        self.logger.log("=== Auto Agent Runner Started ===")

        print()
        self.print_info("Configuration:")
        print(f"  - Working Directory: {WORKING_DIR}")
        print(f"  - Log Directory: {self.log_dir}")
        print(f"  - Max Iterations: {MAX_ITERATIONS}")
        print(f"  - Current Log: {self.current_log}")
        print()

        # Check prerequisites
        if not self.check_claude():
            sys.exit(1)

        # Check for tasks.json
        if not Path('tasks.json').exists():
            self.print_error("tasks.json not found in current directory")
            self.logger.log("ERROR: tasks.json not found")
            sys.exit(1)

        self.print_success("Found tasks.json in working directory")
        self.logger.log("Found tasks.json")

        # Show initial task count
        initial_tasks = self.check_remaining_tasks()
        self.print_info(f"Initial tasks remaining: {initial_tasks}")
        self.logger.log(f"Initial tasks remaining: {initial_tasks}")

        if initial_tasks == 0:
            self.print_success("All tasks already completed!")
            self.logger.log("All tasks already completed")
            sys.exit(0)

        print()
        self.print_warning("Press Ctrl+C to stop the execution")
        print()
        self.logger.log("Starting execution loop")

        # Main loop
        while self.iteration < MAX_ITERATIONS and not self.stop_requested:
            self.iteration += 1

            # Run iteration
            if not self.run_iteration(self.iteration):
                break

            # Add delay between iterations
            if self.iteration < MAX_ITERATIONS and not self.stop_requested:
                print()
                self.print_info("Waiting 5 seconds before next iteration...")
                self.logger.log("Waiting before next iteration")
                time.sleep(5)

        # Final summary
        self.print_header("Execution Summary")
        self.logger.log("=== Execution Summary ===")

        print()
        self.print_info(f"Total iterations run: {self.iteration}")
        self.logger.log(f"Total iterations: {self.iteration}")

        final_tasks = self.check_remaining_tasks()
        self.print_info(f"Final tasks remaining: {final_tasks}")
        self.logger.log(f"Final tasks remaining: {final_tasks}")

        if initial_tasks > final_tasks:
            completed = initial_tasks - final_tasks
            self.print_success(f"Total tasks completed: {completed}")
            self.logger.log(f"Total tasks completed: {completed}")

        print()
        self.print_success("Auto Agent Runner finished!")
        self.logger.log("=== Auto Agent Runner Finished ===")

        print()
        self.print_info(f"Logs saved to: {self.log_dir}")
        self.print_info(f"Current log: {self.current_log}")


def main():
    """Main entry point"""
    runner = AgentRunner()
    runner.run()


if __name__ == "__main__":
    main()
