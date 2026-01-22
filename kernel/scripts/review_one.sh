#!/bin/bash
#
# usage: review_one.sh <sha>
#
# Sets up a git worktree for the given SHA and runs claude review on it.
#
# Before running this, you need to have indexed the SHA range with semcode:
#   cd linux ; semcode-index -s . --git base..last_sha

set -e

usage() {
    echo "usage: review_one.sh [--linux <linux_dir>] [--prompt <prompt_file>] [--series <end_sha>] [--working-dir <dir>] [--model <model>] <sha>"
    echo "  --linux: path to the base linux directory (default: \$PWD/linux)"
    echo "  --prompt: path to the review prompt file (default: <script_dir>/../review-core.md)"
    echo "  sha: the git commit SHA to review"
    echo "  --series: optional SHA of the last commit in the series"
    echo "  --range: optional git range base..last_sha"
    echo "  --working-dir: working directory (default: current directory or WORKING_DIR env)"
    echo "  --model: Claude model to use (default: sonnet or CLAUDE_MODEL env)"
    echo "  --cli: which CLI to use (default: claude)"
    echo "  --help: show this help message"
}

if [ $# -lt 1 ]; then
    usage
    exit 1
fi

# Get script directory early so we can use it for defaults
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"

# Parse arguments
SERIES_SHA=""
ARG_WORKING_DIR=""
ARG_MODEL=""
REVIEW_PROMPT=""
BASE_LINUX=""
CLI="claude"
while [[ $# -gt 1 ]]; do
    case "$1" in
        --help)
            usage
            exit 0
            ;;
        --series)
            SERIES_SHA="$2"
            shift 2
            ;;
        --range)
            RANGE_SHA="$2"
            shift 2
            ;;
        --working-dir)
            ARG_WORKING_DIR="$2"
            shift 2
            ;;
        --model)
            ARG_MODEL="$2"
            shift 2
            ;;
        --cli)
            CLI="$2"
            shift 2
            ;;
        --prompt)
            REVIEW_PROMPT="$2"
            shift 2
            ;;
        --linux)
            BASE_LINUX="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

SHA="$1"

# Set defaults for optional arguments
if [ -z "$REVIEW_PROMPT" ]; then
    REVIEW_PROMPT="$SCRIPT_DIR/../review-core.md"
fi

if [ -z "$BASE_LINUX" ]; then
    BASE_LINUX="$(pwd -P)/linux"
fi

# Validate paths exist
if [ ! -f "$REVIEW_PROMPT" ]; then
    echo "Error: prompt file does not exist: $REVIEW_PROMPT" >&2
    exit 1
fi

if [ ! -d "$BASE_LINUX" ]; then
    echo "Error: linux directory does not exist: $BASE_LINUX" >&2
    exit 1
fi

# Use command line args first, then environment variables, then defaults
if [ -n "$ARG_WORKING_DIR" ]; then
    WORKING_DIR="$ARG_WORKING_DIR"
elif [ -z "$WORKING_DIR" ]; then
    WORKING_DIR="$(pwd -P)"
fi

if [ -n "$ARG_MODEL" ]; then
    CLAUDE_MODEL="$ARG_MODEL"
fi

export WORKING_DIR
export CLAUDE_MODEL

DIR="$BASE_LINUX.$SHA"

#MCP_STRING="$WORKING_DIR/mcp-config.json"
MCP_STRING='{"mcpServers":{"semcode":{"command":"semcode-mcp"}}}'
export MCP_STRING

SEMCODE_ALLOWED="--allowedTools mcp__plugin_semcode_semcode__find_function,mcp__plugin_semcode_semcode__find_type,mcp__plugin_semcode_semcode__find_callers,mcp__plugin_semcode_semcode__find_calls,mcp__plugin_semcode_semcode__find_callchain,mcp__plugin_semcode_semcode__diff_functions,mcp__plugin_semcode_semcode__grep_functions,mcp__plugin_semcode_semcode__vgrep_functions,mcp__plugin_semcode_semcode__find_commit,mcp__plugin_semcode_semcode__vcommit_similar_commits,mcp__plugin_semcode_semcode__lore_search,mcp__plugin_semcode_semcode__dig,mcp__plugin_semcode_semcode__vlore_similar_emails,mcp__plugin_semcode_semcode__indexing_status,mcp__plugin_semcode_semcode__list_branches,mcp__plugin_semcode_semcode__compare_branches"
export SEMCODE_ALLOWED

export TERM=xterm
export FORCE_COLOR=0

echo "Linux directory: $BASE_LINUX" >&2
echo "Working directory: $WORKING_DIR" >&2
echo "Prompt file: $REVIEW_PROMPT" >&2
echo "Processing $SHA"

if [ ! -d "$DIR" ]; then
    (cd "$BASE_LINUX" && git worktree add -d "$DIR" "$SHA")
    while true; do
        if [ -d "$DIR" ]; then
            break
        fi
        echo "waiting for $DIR to exist"
        sleep 1
    done
    if [ -d "$BASE_LINUX/.semcode.db" ]; then
        cp -al "$BASE_LINUX/.semcode.db" "$DIR/.semcode.db"
    else
        echo "Warning: $BASE_LINUX/.semcode.db not found, skipping MCP configuration" >&2
        unset MCP_STRING
        unset SEMCODE_ALLOWED
    fi
fi

cd "$DIR"

nowstr=$(date +"%Y-%m-%d-%H:%M")

# Clean up old review files
rm -f review.json
rm -f check.md
rm -f check.json
rm -f review.duration.txt

if [ -f review-inline.txt ]; then
    mv review-inline.txt "review-inline.$nowstr.txt"
fi

echo "Worktree ready at $DIR"
echo "SHA: $SHA"

# Build the prompt, optionally including series info
PROMPT="read prompt $REVIEW_PROMPT and run regression analysis of commit $SHA"
if [ -n "$SERIES_SHA" ]; then
    PROMPT+=", which is part of a series ending with $SERIES_SHA"
elif [ -n "$RANGE_SHA" ]; then
    PROMPT+=", which is part of a series with git range $RANGE_SHA"
fi

MCP_ARGS=""

set_claude_opts() {
	if [ -z "$CLAUDE_MODEL" ]; then
		CLAUDE_MODEL="opus"
	fi

	JSONPROG="$SCRIPT_DIR/claude-json.py"
	OUTFILE="review.json"

	CLI_OPTS="--verbose"
	CLI_OUT="--output-format=stream-json | tee $OUTFILE | $JSONPROG"
}

case "$CLI" in
    claude)
	    set_claude_opts
	    ;;
    *)
	echo "Error: Unknown CLI: $CLI" >&2
	exit 1
	;;
esac


# Build the full command
FULL_CMD="$CLI"
FULL_CMD+=" -p '$PROMPT'"
FULL_CMD+=" $MCP_ARGS"
FULL_CMD+=" --model $CLAUDE_MODEL"
FULL_CMD+=" $CLI_OPTS"
FULL_CMD+=" $CLI_OUT"
#echo "Would run: $FULL_CMD"

start=$(date +%s)

for x in $(seq 1 5); do
    eval "$FULL_CMD"
    if [ -s "$OUTFILE" ]; then
        break
    fi
    echo "$CLI failed $SHA try $x"
    sleep 5
done

end=$(date +%s)
echo "Elapsed time: $((end - start)) seconds (sha $SHA)" | tee review.duration.txt

if [ -v JSONPROG ]; then
	$JSONPROG -i review.json -o review.md
fi

# Exit with failure if output file is empty after all retries
if [ -s "$OUTFILE" ]; then
    exit 0
else
    exit 1
fi
