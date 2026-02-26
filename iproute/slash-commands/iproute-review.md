# /iproute-review - iproute2 Patch Review

Using the prompt `review-core.md` and the review prompt directory, do a deep
dive regression analysis of the top commit, or the provided patch/commit.

## Instructions

1. Load `review-core.md` for the core checklist
2. Identify what subsystems the patch touches (ip, tc, bridge, lib, etc.)
3. Load relevant context files:
   - `json-output.md` for JSON output changes
   - `argument-parsing.md` for CLI parsing changes
   - `kernel-compat.md` for new kernel feature support
   - `coding-style.md` for style questions
4. Review against the checklist
5. If issues found, create review output in email format

## Key Areas for iproute2

- **matches() vs strcmp()**: New code must use strcmp(), not matches()
- **JSON output**: All display output must use print_XXX() helpers
- **Error handling**: stderr for errors, proper cleanup on failures
- **Netlink**: Proper attribute handling and error checking

## Output

If regressions are found, create `review-inline.txt` with email-style feedback
suitable for the netdev mailing list.
