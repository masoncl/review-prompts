#!/usr/bin/env python3
"""
Convert Claude Code custom agent markdown files (e.g. kernel/agent/*.md)
into Antigravity (agy) custom agent markdown definitions (~/.gemini/config/agents/*.md).

Usage:
    ./claude2agy-agent.py [OPTIONS] <input_files_or_dirs...>
"""

import argparse
import os
import re
import sys
from pathlib import Path

TOOL_MAPPING = {
    "Read": ["read_file"],
    "Write": ["write_file", "edit_file"],
    "Edit": ["edit_file"],
    "Glob": ["run_command"],
    "Grep": ["run_command"],
    "Search": ["run_command"],
    "Bash": ["run_command"],
    "Task": ["invoke_subagent", "manage_subagents"],
}

IGNORED_TOOLS = {
    "TodoWrite",
    "TaskOutput",
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
}

MODEL_MAPPING = {
    "sonnet": "flash",
    "opus": None,
}

AGY_TOOL_INSTRUCTIONS = """
## Tool & Execution Mapping (agy)

When executing review or debugging prompts on `agy`, translate canonical
prompt tool names and control-flow idioms to your native environment:

### 1. Concrete Tool Mapping
| Prompt Term | Action | agy Tool |
| :--- | :--- | :--- |
| `Read` | Read file contents | `read_file` |
| `Write` / `Edit` | Create or modify file | `write_file` / `edit_file` (omit `ArtifactMetadata` for workspace/review files) |
| `Grep` / `Search` | Search file contents | `run_command` (`git grep`) |
| `Glob` | Find files by pattern | `run_command` (`git ls-files` / `find`) |
| `Bash` | Run shell command | `run_command` |
| `semcode` MCP | Kernel AST / callgraph lookup | `call_mcp_tool` (`ServerName: "semcode"`, `ToolName: "<fn_name>"`) |

### 2. Control-Flow & Orchestration Idioms
| Prompt Pattern | Intent | agy Execution |
| :--- | :--- | :--- |
| `<prompt_dir>` | Project prompt directory | `{prompt_dir}` |
| `Task` / `Task(run_in_background: true)` | Spawn subagents | Call `invoke_subagent` with `TypeName` set to the target `.md` agent's registered `name` (even if `subagent_type: general-purpose` is shown) and `Role` set to the task label |
| `TaskOutput(block: true)` | Wait for background subagents | Stop calling tools / end turn. `agy` reactively wakes you when subagents complete. |
| `model: sonnet` / `opus` | Subagent model selection | `sonnet` maps to `Model: "flash"`, `opus` maps to `Model: "inherit"` (always use `Model: "inherit"` for orchestrator subagents) |
| `TodoWrite` / `TaskCreate` / `TaskUpdate` / `TaskList` | Track multi-step tasks | Maintain a markdown checklist (`[ ]` / `[x]`) in your turns |
| `ToolSearch` | Load MCP tools | No-op (use `call_mcp_tool` directly for lazy-loaded MCP tools) |
"""


def parse_frontmatter(content: str):
    """Extract YAML frontmatter and markdown body."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if not match:
        return None, content
    fm_text, body = match.group(1), match.group(2)
    metadata = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        metadata[key.strip()] = val.strip()
    return metadata, body


def map_tools(claude_tools_str: str):
    """Map comma-separated Claude tool list to (agy_tools, uses_mcp)."""
    if not claude_tools_str:
        return [], False
    agy_tools = {"read_file", "send_message", "manage_task"}
    uses_mcp = False
    for token in claude_tools_str.split(","):
        tool = token.split("(", 1)[0].strip()
        if not tool:
            continue
        if tool == "ToolSearch" or tool.startswith("mcp__"):
            uses_mcp = True
            continue
        if tool in TOOL_MAPPING:
            agy_tools.update(TOOL_MAPPING[tool])
        elif tool not in IGNORED_TOOLS:
            print(f"Warning: unmapped tool '{tool}', ignoring", file=sys.stderr)
    return sorted(agy_tools), uses_mcp


def convert_agent_file(src_path: Path, dest_dir: Path, prompt_dir: Path):
    content = src_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    if not metadata or "name" not in metadata:
        return None

    agent_name = metadata["name"]
    description = metadata.get("description", "").strip("\"'")
    agy_tools, uses_mcp = map_tools(metadata.get("tools", ""))
    is_orchestrator = "invoke_subagent" in agy_tools
    raw_model = metadata.get("model", "").strip("\"'")
    agy_model = None if is_orchestrator else MODEL_MAPPING.get(raw_model, raw_model)

    lines = ["---"]
    lines.append(f"name: {agent_name}")
    lines.append(f'description: "{description}"')
    if agy_model:
        lines.append(f"model: {agy_model}")
    if agy_tools:
        lines.append("tools:")
        for t in agy_tools:
            lines.append(f"  - {t}")
    lines.append("mainAgent: false")
    lines.append("subagent: true")
    lines.append(f"inheritMcp: {'true' if uses_mcp else 'false'}")
    lines.append("---")
    lines.append("")

    out_body = body.replace("<prompt_dir>/agent/", f"{dest_dir}/").rstrip()
    if "Tool & Execution Mapping (agy)" not in out_body:
        out_body += "\n" + AGY_TOOL_INSTRUCTIONS.format(
            prompt_dir=prompt_dir
        ).rstrip()

    output_content = "\n".join(lines) + out_body + "\n"

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / src_path.name
    dest_path.write_text(output_content, encoding="utf-8")
    return dest_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Claude Code custom agent markdown files to Antigravity (agy) custom agents."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input project prompt directory (containing agent/*.md), agent directory, or .md files",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=os.path.expanduser("~/.gemini/config/agents"),
        help="Output directory for converted agent files (default: ~/.gemini/config/agents)",
    )
    args = parser.parse_args()

    dest_dir = Path(os.path.abspath(args.output_dir))
    converted = []

    for inp in args.inputs:
        p = Path(os.path.abspath(inp))
        if p.is_dir():
            agent_subdir = p / "agent"
            if agent_subdir.is_dir():
                prompt_dir = p
                md_files = sorted(agent_subdir.glob("*.md"))
            else:
                prompt_dir = p.parent if p.name == "agent" else p
                md_files = sorted(p.glob("*.md"))
            targets = [(md_file, prompt_dir) for md_file in md_files]
        elif p.is_file():
            prompt_dir = p.parent.parent if p.parent.name == "agent" else p.parent
            targets = [(p, prompt_dir)]
        else:
            print(f"Error: {inp} not found", file=sys.stderr)
            sys.exit(1)

        for md_file, prompt_dir in targets:
            res = convert_agent_file(md_file, dest_dir, prompt_dir)
            if res:
                converted.append((md_file, res))

    if not converted:
        print("Error: no agent files were converted", file=sys.stderr)
        sys.exit(1)

    print(f"Converted {len(converted)} agent(s) to {dest_dir}:")
    for src, dst in converted:
        print(f"  {src.name} -> {dst.name}")


if __name__ == "__main__":
    main()
