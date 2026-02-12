# /iproute-debug - iproute2 Debug

Debug iproute2 issues using the context files in the review prompt directory.

## Instructions

1. Load relevant context files based on the issue:
   - `json-output.md` for JSON output problems
   - `argument-parsing.md` for CLI parsing issues
   - `kernel-compat.md` for kernel compatibility problems
   - `coding-style.md` for style questions
2. Analyze the problem description
3. Search the codebase for relevant code paths
4. Identify potential causes
5. Suggest fixes with code examples

## Common Debug Scenarios

### JSON Output Issues
- Missing or malformed JSON output
- JSON object/array not properly closed
- Human-readable values appearing in JSON (should be raw)

### Argument Parsing
- Abbreviations causing conflicts (matches() vs strcmp())
- Missing or incorrect error messages
- NEXT_ARG() missing when required

### Kernel Compatibility
- Feature not working on older kernels
- Missing runtime detection
- uapi header mismatches

### Memory Issues
- Use valgrind to check for leaks
- Check all error paths for proper cleanup
- Verify buffer sizes
