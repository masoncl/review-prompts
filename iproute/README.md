# iproute2 Review Documentation

Review guidelines for iproute2 patches, designed for both human reviewers and AI coding assistants.

## File Structure

| File | Purpose | When to Load |
|------|---------|-------------|
| **review-core.md** | Main entry point with review checklist | Always start here |
| **technical-patterns.md** | Core technical patterns and common bugs | Load first (per review-core.md) |
| **coding-style.md** | Complete style guide | Style questions, new files |
| **argument-parsing.md** | Argument handling patterns | Changes to argument parsing |
| **json.md** | JSON output implementation and validation | Changes to output functions |
| **netlink.md** | Netlink protocol patterns | Netlink request/response code |
| **false-positive-guide.md** | Avoiding incorrect review findings | When uncertain about violations |

## Quick Start

### For AI Assistants

1. Load `review-core.md` (start of every review)
2. Load `technical-patterns.md` (required by review-core.md)
3. Load additional files based on patch content:
   - Argument parsing code → `argument-parsing.md`
   - JSON/output code → `json.md`
   - Netlink code → `netlink.md`
   - Style questions → `coding-style.md`
   - Uncertain findings → `false-positive-guide.md`

### For Human Reviewers

1. Start with `review-core.md` for systematic checklist
2. Consult specific files as needed for details
3. Use `false-positive-guide.md` to avoid incorrect findings

## Critical Anti-Patterns

Watch for these common violations:

1. **matches() in new code** - Use strcmp() instead
2. **Errors to stdout** - Always use stderr
3. **Missing JSON close calls** - Every open needs close
4. **fprintf(fp, ...) for output** - Use print_XXX() helpers
5. **Split user strings** - Must be grep-able
6. **Unchecked malloc** - Always verify allocations
7. **uapi without kernel reference** - Must cite commit hash
8. **Missing NEXT_ARG()** - After accepting keyword

## About iproute2

iproute2 provides Linux networking utilities:
- **ip** - Network interface configuration
- **tc** - Traffic control
- **ss** - Socket statistics
- **bridge** - Bridge management

Website: https://wiki.linuxfoundation.org/networking/iproute2
Mailing list: netdev@vger.kernel.org

## Key Differences from Kernel

- **No Christmas tree** variable ordering (kernel requires it)
- **No docbook** format (use simple C comments)
- **JSON output** required for all commands
- **Userspace focus** (different patterns than kernel)

## Review Process

1. Check coding style compliance
2. Verify argument parsing uses strcmp()
3. Ensure JSON output correctness
4. Check memory safety
5. Validate netlink protocol usage
6. Confirm kernel compatibility handling
7. Review commit message format

## File Sizes

```
Total: ~2300 lines across 7 files
- review-core.md:          ~130 lines  (entry point)
- technical-patterns.md:   ~230 lines  (core patterns)
- coding-style.md:         ~230 lines  (style guide)
- argument-parsing.md:     ~270 lines  (argument handling)
- json.md:                 ~280 lines  (JSON output)
- netlink.md:              ~260 lines  (netlink protocol)
- false-positive-guide.md: ~250 lines  (avoiding mistakes)
```

## Contributing

These guidelines are maintained to ensure consistent code quality in iproute2.
When updating:

1. Keep examples concrete and actionable
2. Test guidelines on actual patches
3. Maintain consistency across files
4. Update false-positive-guide.md for common edge cases
