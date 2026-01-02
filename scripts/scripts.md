# Review Scripts Documentation

These scripts automate the process of reviewing a series of git commits using Claude.

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `review_one.sh` | Reviews a single commit SHA |
| `claude_xargs.py` | Runs multiple reviews in parallel |
| `claude-json.py` | Parses Claude's stream-json output to markdown |

---

## review_one.sh

Reviews a single git commit by setting up a worktree and running Claude's review.

### Usage

```bash
review_one.sh [options] <sha>
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--linux <path>` | Path to the base linux directory | `./linux` |
| `--prompt <file>` | Path to the review prompt file | `<script_dir>/../review-core.md` |
| `--series <sha>` | SHA of the last commit in the series (optional) | - |
| `--working-dir <dir>` | Directory where worktrees are created | Current directory or `$WORKING_DIR` |
| `--model <model>` | Claude model to use | `sonnet` or `$CLAUDE_MODEL` |

### What it does

1. Creates a git worktree at `linux.<sha>` for the specified commit
2. If the base linux directory has `.semcode.db`, hard-links it into the worktree and configures MCP
3. Runs Claude with the review prompt
4. Outputs results to:
   - `review.json` - Raw Claude output (stream-json format)
   - `review.md` - Parsed markdown review
   - `review.duration.txt` - Elapsed time
5. Retries up to 5 times if Claude exits without output

### Directory Structure Assumptions

`review_one.sh` uses its install location to find related files:

| Path | Description |
|------|-------------|
| `$SCRIPT_DIR/claude-json.py` | JSON parser script (must be in same directory) |
| `$SCRIPT_DIR/../review-core.md` | Default review prompt (parent directory of scripts/) |

Where `$SCRIPT_DIR` is the directory containing `review_one.sh`.

### Prerequisites

- The SHA range must be indexed with semcode first:
  ```bash
  cd linux && semcode-index -s . --git base..last_sha
  ```
- `semcode-mcp` must be in your PATH if using semcode integration

---

## claude_xargs.py

Runs multiple `claude -p` commands in parallel, similar to xargs but with timeout support and proper signal handling.

### Usage

```bash
claude_xargs.py -c <command> -f <sha_file> [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-c, --command` | The claude command template to run (required) | - |
| `-f, --sha-file` | File containing list of SHAs, one per line (required) | - |
| `-n, --parallel` | Number of parallel instances | 24 |
| `--series <sha>` | SHA of the last commit in the series | - |
| `--timeout <seconds>` | Timeout for each command | - |
| `-v, --verbose` | Print stderr output from commands | - |

### Features

- Runs commands in parallel using a thread pool
- Handles Ctrl-C gracefully, killing all spawned processes
- Supports per-command timeout
- Reports progress and failure counts

### Example

```bash
/path/claude_xargs.py -n 5 -f shas.txt -c '/path/review_one.sh'
```

---

## claude-json.py

Parses Claude's stream-json output format and converts it to plain text/markdown.

### Usage

```bash
# Pipe from claude
claude -p "prompt" --output-format=stream-json | python claude-json.py

# From file
python claude-json.py -i input.json -o output.txt

# Debug mode
python claude-json.py -d < input.json
```

### Options

| Option | Description |
|--------|-------------|
| `-i, --input` | Input file (default: stdin) |
| `-o, --output` | Output file (default: stdout) |
| `-d, --debug` | Enable debug output to stderr |

### Why it exists

When using `claude -p` (non-interactive mode), normal output is disabled. The only way to capture output is with `--output-format=stream-json` and `--verbose`. This script parses that JSON stream back into readable markdown.

---

## Complete Workflow Example

Review a patch series applied to linux:

```bash
# 1. Prepare the linux tree
cd linux
git reset --hard v6.19
git am -s patches/*.patch
git rev-list v6.19..HEAD > ../series

# 2. Index with semcode (optional but recommended)
semcode-index -s . --git v6.19..HEAD

# 3. Run parallel reviews
cd ..
/path/to/scripts/claude_xargs.py \
    -n 10 \
    -f series \
    -c "/path/to/scripts/review_one.sh" \
    --series $(git -C linux rev-parse HEAD)
```

### Output

After completion, you'll have:
- `linux.<sha>/` directories for each commit
- `linux.<sha>/review.md` - The review for each commit
- `linux.<sha>/review-inline.txt` - Any bugs found (if applicable)
- `linux.<sha>/review.duration.txt` - Time taken for each review
