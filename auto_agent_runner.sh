#!/bin/bash

# Auto Agent Runner - Continuous Long-Term Agent Coding
# This script continuously runs long-term-agent-coding skill in a loop

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
LOG_DIR="./agent_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_LOG="$LOG_DIR/agent_run_$TIMESTAMP.log"
MAX_ITERATIONS=${MAX_ITERATIONS:-100}  # Max iterations, can be overridden via env var
ITERATION=0
WORKING_DIR=$(pwd)

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Print functions
print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${CYAN}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_stream() {
    echo -e "${MAGENTA}→${NC} $1"
}

# Logging function
log_to_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$CURRENT_LOG"
}

# Check if Claude binary exists
check_claude() {
    if ! command -v claude &> /dev/null; then
        print_error "Claude CLI is not installed or not in PATH"
        log_to_file "ERROR: Claude CLI not found"
        exit 1
    fi
    print_success "Claude CLI found: $(which claude)"
    log_to_file "Claude CLI found: $(which claude)"
}

# Check remaining tasks
check_remaining_tasks() {
    local count
    count=$(python3 -c "import json; data = json.load(open('tasks.json')); print(sum(1 for t in data if not t.get('passes', False)))" 2>/dev/null || echo "0")
    echo "$count"
}

# Check git status
check_git_status() {
    local status
    status=$(git status --porcelain 2>/dev/null || echo "")
    if [ -n "$status" ]; then
        print_warning "Git working directory has uncommitted changes"
        log_to_file "Git has uncommitted changes"
    else
        print_success "Git working directory is clean"
        log_to_file "Git working directory is clean"
    fi
}

# Run a single iteration of the agent
run_agent_iteration() {
    local iteration_num=$1
    local start_time=$(date +%s)

    print_header "Starting Iteration #$iteration_num"
    log_to_file "=== Starting Iteration #$iteration_num ==="

    # Print iteration info
    echo ""
    print_info "Working Directory: $WORKING_DIR"
    print_info "Log File: $CURRENT_LOG"
    print_info "Max Iterations: $MAX_ITERATIONS"

    # Check remaining tasks
    local remaining
    remaining=$(check_remaining_tasks)
    print_info "Remaining Tasks: $remaining"
    log_to_file "Remaining tasks: $remaining"

    if [ "$remaining" -eq 0 ]; then
        print_success "All tasks completed!"
        log_to_file "All tasks completed, stopping execution"
        return 1  # Return non-zero to stop the loop
    fi

    # Check git status
    check_git_status

    # Print current task info
    echo ""
    print_info "Current Task (highest priority):"
    python3 -c "
import json
data = json.load(open('tasks.json'))
for task in data:
    if not task.get('passes', False):
        print(f\"  Category: {task.get('category', 'N/A')}\")
        print(f\"  Description: {task.get('description', 'N/A')[:80]}...\")
        break
" 2>/dev/null || print_warning "Could not read tasks.json"

    # Run Claude with streaming output
    echo ""
    print_header "Running Long-Term Agent Coding Skill"
    log_to_file "Executing Claude with long-term-agent-coding skill"

    local claude_output="$LOG_DIR/claude_output_${iteration_num}.txt"
    local claude_log="$LOG_DIR/claude_log_${iteration_num}.txt"

    echo ""
    print_stream "Claude Output (Streaming):"
    echo -e "${CYAN}----------------------------------------${NC}"

    # Run Claude with stream-json output format and capture output
    # Using exec and tee to both display and save output
    {
        claude \
            --print \
            --dangerously-skip-permissions \
            --output-format stream-json \
            --include-partial-messages \
            --verbose \
            "请执行下一个任务" 2>&1
    } | tee "$claude_output" | while IFS= read -r line; do
        # Print each line to console with streaming indicator
        if echo "$line" | jq -e '.type' > /dev/null 2>&1; then
            # It's JSON, try to extract and print content
            local type
            type=$(echo "$line" | jq -r '.type' 2>/dev/null || echo "unknown")
            local content
            content=$(echo "$line" | jq -r '.text // .delta // .content // .' 2>/dev/null | head -c 200)

            case "$type" in
                "text_delta"|"content_block_delta")
                    if [ -n "$content" ] && [ "$content" != "null" ]; then
                        echo -n "$content"
                        log_to_file "Stream: $content"
                    fi
                    ;;
                "content_block_start"|"content_block_stop"|"message_delta")
                    # These are control messages, log but don't print
                    log_to_file "Control message: $type"
                    ;;
                *)
                    # Print unknown JSON types
                    echo ""
                    print_stream "[Stream: $type]"
                    ;;
            esac
        else
            # Non-JSON output, print as-is
            echo "$line"
        fi
    done

    echo ""
    echo -e "${CYAN}----------------------------------------${NC}"

    # Calculate and print iteration duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    echo ""
    print_info "Iteration Duration: ${minutes}m ${seconds}s"
    log_to_file "Iteration #$iteration_num completed in ${minutes}m ${seconds}s"

    # Check if tasks.json was modified
    if [ -f "tasks.json" ]; then
        local new_remaining
        new_remaining=$(check_remaining_tasks)
        if [ "$new_remaining" -lt "$remaining" ]; then
            local completed=$((remaining - new_remaining))
            print_success "Tasks completed this iteration: $completed"
            log_to_file "Tasks completed this iteration: $completed"
        fi
    fi

    return 0
}

# Main execution
main() {
    print_header "Auto Agent Runner Starting"
    log_to_file "=== Auto Agent Runner Started ==="

    echo ""
    print_info "Configuration:"
    echo "  - Working Directory: $WORKING_DIR"
    echo "  - Log Directory: $LOG_DIR"
    echo "  - Max Iterations: $MAX_ITERATIONS"
    echo "  - Current Log: $CURRENT_LOG"
    echo ""

    # Check prerequisites
    check_claude

    # Check if we're in the correct directory
    if [ ! -f "tasks.json" ]; then
        print_error "tasks.json not found in current directory"
        log_to_file "ERROR: tasks.json not found"
        exit 1
    fi
    print_success "Found tasks.json in working directory"
    log_to_file "Found tasks.json"

    # Show initial task count
    local initial_tasks
    initial_tasks=$(check_remaining_tasks)
    print_info "Initial tasks remaining: $initial_tasks"
    log_to_file "Initial tasks remaining: $initial_tasks"

    if [ "$initial_tasks" -eq 0 ]; then
        print_success "All tasks already completed!"
        log_to_file "All tasks already completed"
        exit 0
    fi

    echo ""
    print_warning "Press Ctrl+C to stop the execution"
    echo ""
    log_to_file "Starting execution loop"

    # Trap Ctrl+C to exit gracefully
    trap 'echo ""; print_warning "Received interrupt signal, stopping..."; log_to_file "Interrupted by user"; exit 0' INT TERM

    # Main loop
    while [ $ITERATION -lt $MAX_ITERATIONS ]; do
        ITERATION=$((ITERATION + 1))

        # Run the iteration
        if ! run_agent_iteration "$ITERATION"; then
            # If iteration returns non-zero, stop the loop
            break
        fi

        # Add a delay between iterations for stability
        if [ $ITERATION -lt $MAX_ITERATIONS ]; then
            echo ""
            print_info "Waiting 5 seconds before next iteration..."
            log_to_file "Waiting before next iteration"
            sleep 5
        fi
    done

    # Final summary
    print_header "Execution Summary"
    log_to_file "=== Execution Summary ==="

    echo ""
    print_info "Total iterations run: $ITERATION"
    log_to_file "Total iterations: $ITERATION"

    local final_tasks
    final_tasks=$(check_remaining_tasks)
    print_info "Final tasks remaining: $final_tasks"
    log_to_file "Final tasks remaining: $final_tasks"

    if [ "$initial_tasks" -gt "$final_tasks" ]; then
        local completed=$((initial_tasks - final_tasks))
        print_success "Total tasks completed: $completed"
        log_to_file "Total tasks completed: $completed"
    fi

    echo ""
    print_success "Auto Agent Runner finished!"
    log_to_file "=== Auto Agent Runner Finished ==="

    echo ""
    print_info "Logs saved to: $LOG_DIR"
    print_info "Current log: $CURRENT_LOG"
}

# Run main function
main
