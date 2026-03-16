#!/usr/bin/env python3
"""
claude-json: Parse Claude stream-json output and convert to plain text

Based on patterns from:
- claude-code-log (MIT License) - https://github.com/daaain/claude-code-log
- claude-code-sdk-python (MIT License) - https://github.com/anthropics/claude-code-sdk-python

Usage:
    claude -p "your prompt" --output-format=stream-json | python scripts/claude-json.py
    python scripts/claude-json.py -i input.json -o output.txt
    python scripts/claude-json.py -d < input.json  # debug mode
    python scripts/claude-json.py -i input.json -a agents.json  # extract agent map
"""

import json
import sys
import argparse


def parse_stream(stream, debug=False):
    """Parse Claude's stream-json format, extracting text and agent info.

    Returns (text, agents) where:
      - text: concatenated plain text from assistant messages
      - agents: list of agent info dicts (from toolUseResult fields)
    """
    text_parts = []
    agents = []
    line_count = 0
    parsed_count = 0

    for line in stream:
        line_count += 1
        line = line.strip()

        if not line:
            continue

        if debug:
            print(f"Processing line {line_count}: {line[:100]}...", file=sys.stderr)

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            if debug:
                print(f"JSON decode error on line {line_count}: {e}", file=sys.stderr)
                print(f"Raw line: {line}", file=sys.stderr)
            continue
        except Exception as e:
            if debug:
                print(f"Unexpected error on line {line_count}: {e}", file=sys.stderr)
            continue

        msg_type = data.get('type')

        # Extract text from assistant messages
        if msg_type == 'assistant' and 'message' in data:
            for content_item in data['message'].get('content', []):
                if content_item.get('type') == 'text':
                    text = content_item.get('text', '')
                    if text:
                        parsed_count += 1
                        text_parts.append(text)
                        # The output always needs a trailing newline
                        # Otherwise we risk breaking markdown formatting
                        text_parts.append('\n')
                        if debug:
                            print(f"Extracted text {parsed_count}: {len(text)} chars",
                                  file=sys.stderr)

        # Handle streaming deltas
        elif msg_type == 'content_block_delta':
            delta_text = data.get('delta', {}).get('text', '')
            if delta_text:
                parsed_count += 1
                text_parts.append(delta_text)
                if debug:
                    print(f"Extracted delta {parsed_count}: {len(delta_text)} chars",
                          file=sys.stderr)

        # Extract agent info from tool_use_result on user messages
        elif msg_type == 'user':
            tur = data.get('tool_use_result') or data.get('toolUseResult')
            if isinstance(tur, dict) and tur.get('agentId'):
                agent = {}
                for key in ('agentId', 'description', 'prompt',
                            'outputFile', 'status'):
                    if key in tur:
                        agent[key] = tur[key]
                agents.append(agent)
                if debug:
                    print(f"Found agent {tur['agentId']}: "
                          f"{tur.get('description', '?')}", file=sys.stderr)

    if debug:
        print(f"Processed {line_count} lines, extracted {parsed_count} text parts, "
              f"total {len(''.join(text_parts))} chars, {len(agents)} agents",
              file=sys.stderr)

    return ''.join(text_parts), agents


def collect_agent_text(agents, debug=False):
    """Parse each agent's outputFile and return concatenated text with headers."""
    parts = []
    for agent in agents:
        description = agent.get('description', 'unknown')
        output_file = agent.get('outputFile')
        if not output_file:
            if debug:
                print(f"Agent '{description}' has no outputFile, skipping",
                      file=sys.stderr)
            continue

        try:
            with open(output_file, 'r') as f:
                agent_text, sub_agents = parse_stream(f, debug=debug)
        except FileNotFoundError:
            if debug:
                print(f"Agent output file not found: {output_file}",
                      file=sys.stderr)
            continue

        if not agent_text.strip():
            continue

        header = f'Agent: {description}'
        separator = '=' * len(header)
        parts.append('\n\n')
        parts.append(separator + '\n')
        parts.append(header + '\n')
        parts.append(separator + '\n')
        parts.append('\n')
        parts.append(agent_text)

        # Recurse into sub-agents
        if sub_agents:
            sub_text = collect_agent_text(sub_agents, debug=debug)
            if sub_text:
                parts.append(sub_text)

    return ''.join(parts)


def main():
    parser = argparse.ArgumentParser(
        description='Parse Claude stream-json output and convert to plain text',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('-i', '--input', type=str,
                        help='Input file (default: stdin)')
    parser.add_argument('-o', '--output', type=str,
                        help='Output file (default: stdout)')
    parser.add_argument('-a', '--agents', type=str,
                        help='Write agent mapping JSON to this file')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug output to stderr')
    parser.add_argument('--no-agents', action='store_true',
                        help='Do not append subagent outputs')

    args = parser.parse_args()

    # Handle input
    if args.input:
        try:
            with open(args.input, 'r') as f:
                text, agents = parse_stream(f, debug=args.debug)
        except FileNotFoundError:
            print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            return 1
    else:
        text, agents = parse_stream(sys.stdin, debug=args.debug)

    # Write agent mapping
    if args.agents:
        try:
            with open(args.agents, 'w') as f:
                json.dump(agents, f, indent=2)
                f.write('\n')
        except Exception as e:
            print(f"Error writing agents file: {e}", file=sys.stderr)
            return 1

    # Collect agent outputs unless suppressed
    agent_text = ''
    if agents and not args.no_agents:
        agent_text = collect_agent_text(agents, debug=args.debug)

    # Handle output
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(text)
                if agent_text:
                    f.write(agent_text)
                f.write('\n')
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print("\n")
        print(text, end='')
        if agent_text:
            print(agent_text, end='')
        print("\n\n=================\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
