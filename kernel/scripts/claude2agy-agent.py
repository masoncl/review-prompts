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
    "Read": ["view_file"],
    "Write": ["write_to_file", "replace_file_content"],
    "Glob": ["find_by_name", "list_dir"],
    "Grep": ["grep_search", "code_search"],
    "Search": ["grep_search", "code_search"],
    "Bash": ["run_command", "manage_task"],
    "Task": ["invoke_subagent", "send_message", "manage_subagents"],
    "ToolSearch": [],
    "TodoWrite": [],
    "TaskOutput": [],
    "TaskCreate": [],
    "TaskUpdate": [],
    "TaskList": [],
}

AGY_TOOL_INSTRUCTIONS = """
## Tool & Execution Mapping (agy)

When executing review or debugging prompts on `agy`, translate canonical
prompt tool names and control-flow idioms to your native environment:

### 1. Concrete Tool Mapping
| Prompt Term | Action | agy Tool |
| :--- | :--- | :--- |
| `Read` | Read file contents | `view_file` |
| `Write` | Create or overwrite file | `write_to_file` / `replace_file_content` |
| `Grep` / `Search` | Search file contents | `grep_search` / `code_search` |
| `Glob` | Find files by pattern | `find_by_name` / `list_dir` |
| `Bash` | Run shell command | `run_command` |
| `semcode` MCP | Kernel AST / callgraph lookup | `call_mcp_tool` (`server_name: "semcode"`, `tool_name: "<fn_name>"`) |

### 2. Control-Flow & Orchestration Idioms
| Prompt Pattern | Intent | agy Execution |
| :--- | :--- | :--- |
| `Task(run_in_background: true)` | Spawn parallel subagents | Call `invoke_subagent` with entries in `Subagents` array |
| `TaskOutput(block: true)` | Wait for background subagents | Stop calling tools / end turn. `agy` reactively wakes you when subagents complete. |
| `model: sonnet` / `opus` | Subagent model selection | `sonnet` maps to `Model: "flash"`, `opus` maps to `Model: "inherit"` |
| `TodoWrite` | Track multi-step tasks | Maintain a markdown checklist (`[ ]` / `[x]`) in your turns |
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
    """Map comma-separated Claude tool list to a list of Antigravity (agy) tools."""
    if not claude_tools_str:
        return []
    agy_tools = []
    seen = set()
    for token in claude_tools_str.split(","):
        tool = token.strip()
        if not tool:
            continue
        mapped = TOOL_MAPPING.get(tool)
        if mapped is not None:
            for t in mapped:
                if t not in seen:
                    agy_tools.append(t)
                    seen.add(t)
        elif tool.startswith("Bash("):
            for t in ("run_command", "manage_task"):
                if t not in seen:
                    agy_tools.append(t)
                    seen.add(t)
        elif tool.startswith("mcp__"):
            if "call_mcp_tool" not in seen:
                agy_tools.append("call_mcp_tool")
                seen.add("call_mcp_tool")
        else:
            if tool not in seen:
                agy_tools.append(tool)
                seen.add(tool)
    return agy_tools


def convert_agent_file(
    src_path: Path,
    dest_dir: Path,
    use_agent_name: bool = False,
    agents_path: str = None,
):
    content = src_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    if not metadata or "name" not in metadata:
        return None

    agent_name = metadata["name"]
    description = metadata.get("description", "").strip("\"'")
    agy_tools = map_tools(metadata.get("tools", ""))

    lines = ["---"]
    lines.append(f"name: {agent_name}")
    lines.append(f'description: "{description}"')
    if agy_tools:
        lines.append("tools:")
        for t in agy_tools:
            lines.append(f"  - {t}")
    lines.append("mainAgent: false")
    lines.append("subagent: true")
    lines.append("commandExecutionPolicy: auto")
    lines.append("---")
    lines.append("")

    target_agents_ref = (agents_path or str(dest_dir.resolve())).rstrip("/")
    out_body = body.rstrip()
    out_body = out_body.replace("<prompt_dir>/agent/", f"{target_agents_ref}/")
    out_body = re.sub(r"\bsonnet\b", "flash", out_body)
    out_body = re.sub(r"\bopus\b", "inherit", out_body)
    if "Tool & Execution Mapping (agy)" not in out_body:
        out_body += "\n" + AGY_TOOL_INSTRUCTIONS

    output_content = "\n".join(lines) + out_body.rstrip() + "\n"

    dest_dir.mkdir(parents=True, exist_ok=True)
    out_filename = f"{agent_name}.md" if use_agent_name else src_path.name
    dest_path = dest_dir / out_filename
    dest_path.write_text(output_content, encoding="utf-8")
    return dest_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Claude Code custom agent markdown files to Antigravity (agy) custom agents."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input .md files or directories containing .md files",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=os.path.expanduser("~/.gemini/config/agents"),
        help="Output directory for converted agent files (default: ~/.gemini/config/agents)",
    )
    parser.add_argument(
        "--agents-path",
        default=None,
        help="Path prefix to substitute for <prompt_dir>/agent/ (default: output-dir)",
    )
    parser.add_argument(
        "--use-agent-name",
        action="store_true",
        help="Rename output files to <agent_name>.md instead of keeping original filenames",
    )
    args = parser.parse_args()

    dest_dir = Path(args.output_dir)
    converted = []

    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            for md_file in sorted(p.glob("*.md")):
                res = convert_agent_file(
                    md_file, dest_dir, args.use_agent_name, args.agents_path
                )
                if res:
                    converted.append((md_file, res))
        elif p.is_file():
            res = convert_agent_file(p, dest_dir, args.use_agent_name, args.agents_path)
            if res:
                converted.append((p, res))
        else:
            print(f"Warning: {inp} not found, skipping", file=sys.stderr)

    print(f"Converted {len(converted)} agent(s) to {dest_dir}:")
    for src, dst in converted:
        print(f"  {src.name} -> {dst.name}")


if __name__ == "__main__":
    main()
