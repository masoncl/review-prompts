# iproute2 Patch Review Protocol

## Pre-Review Setup

Before beginning review:
1. ALWAYS load `technical-patterns.md` first
2. Load additional files based on patch content (see triggers below)

## Review Checklist

### Coding Style
- [ ] Tabs (8 chars) for indentation, no spaces except continuations
- [ ] Line length: prefer 80 cols, max 100 cols for readability
- [ ] K&R braces: functions on new line, control structures on same line
- [ ] Pointer `*` adjacent to variable name, not type
- [ ] SPDX license identifier in new files
- [ ] No "Christmas tree" variable declarations (ordering not required)
- [ ] User-visible strings never broken across lines (must be grep-able)

### Argument Parsing
- [ ] **CRITICAL**: New code uses `strcmp()`, NOT `matches()`
- [ ] Proper use of `NEXT_ARG()`, `NEXT_ARG_OK()`, `PREV_ARG()`
- [ ] Error helpers used correctly: `invarg()`, `duparg()`, `missarg()`
- [ ] `usage()` function present and calls `exit(-1)`

### JSON Output
- [ ] All display output uses `print_XXX()` helpers, not `fprintf(fp, ...)`
- [ ] **CRITICAL**: Error messages to stderr, never stdout
- [ ] `open_json_object()` paired with `close_json_object()`
- [ ] `open_json_array()` paired with `close_json_array()`
- [ ] Uses `PRINT_ANY` for unified output, not separate JSON/text branches
- [ ] Valid JSON output (see json.md for validation)

### Memory Safety
- [ ] All malloc/calloc/realloc return values checked for NULL
- [ ] No buffer overflows (check array bounds, string lengths)
- [ ] Memory freed on all error paths
- [ ] Use goto for centralized cleanup when multiple exit points

### Netlink Protocol
- [ ] Request structures use designated initializers
- [ ] Correct use of `addattr_l()`, `addattr32()`, `addattr_nest()`
- [ ] Nested attributes closed with `addattr_nest_end()`
- [ ] Return values from `rtnl_talk()` and similar checked
- [ ] Handles `EOPNOTSUPP` and other errors gracefully

### Kernel Compatibility
- [ ] uapi header updates in **separate patch** from functionality
- [ ] uapi patches reference upstream kernel commit hash
- [ ] No patches depending on unmerged kernel changes
- [ ] Code handles older kernels gracefully (feature detection)
- [ ] **No** `#ifdef KERNEL_VERSION` checks

### Commit Quality
- [ ] Subject: `[PATCH iproute2]` or `[PATCH iproute2-next]`
- [ ] Subject: `component: brief description` (≤50 chars after prefix)
- [ ] Body wrapped at 72 characters
- [ ] `Signed-off-by:` line present (DCO compliance)
- [ ] References kernel commit for new features

## Conditional Context Loading

Load additional files based on what the patch touches:

| Patch touches... | Load file |
|-----------------|-----------|
| Coding style questions | `coding-style.md` |
| Argument parsing code | `argument-parsing.md` |
| JSON/output functions | `json.md` |
| Netlink protocol code | `netlink.md` |

## Critical Anti-Patterns

### 1. Using matches() in New Code
```c
/* WRONG - allows unwanted abbreviations */
if (matches(*argv, "device") == 0) { }

/* CORRECT - exact match only */
if (strcmp(*argv, "device") == 0) { }
```

### 2. Errors to stdout
```c
/* WRONG - corrupts JSON output */
printf("Error: invalid argument\n");

/* CORRECT - errors always to stderr */
fprintf(stderr, "Error: invalid argument\n");
```

### 3. Missing JSON close calls
```c
open_json_object("link");
print_string(PRINT_ANY, "name", "%s", name);
/* WRONG - missing close_json_object(); */
```
See json.md for complete JSON validation.

## Review Output Format

Structure feedback as email suitable for netdev@vger.kernel.org:

```
On [date], [author] wrote:
> [quoted relevant patch section]

[Specific issue description]

[Corrected code example if applicable]

[Explanation of why this matters]
```

Be specific with line references. Explain the "why" behind requirements.

## Common Regression Patterns

1. **matches() in new code** - Most frequent violation
2. **Missing close_json_object/array** - Breaks JSON output
3. **Errors to stdout** - Corrupts JSON mode
4. **Split user strings** - Breaks grep-ability
5. **Unchecked malloc** - Potential null dereference
6. **uapi without kernel reference** - Missing upstream citation
7. **Using fprintf(fp, ...)** - Should use print_XXX() helpers
8. **Missing NEXT_ARG()** - Incorrect argument consumption

## Security Considerations

When reviewing patches, also check:
- Input validation on all user-provided data
- Buffer sizes and potential overflows
- Return value checking for system/library calls
- Integer overflows in size calculations
- Format string vulnerabilities
