# Coccinelle Semantic Patch Generation

## Purpose

Generate Coccinelle semantic patches (SmPL) for systematic, pattern-based code
transformations across the kernel tree. Prefer this approach over manual file
edits whenever the change is a repeatable pattern.

## When to Use Coccinelle

Recognize these request patterns as Coccinelle-suitable:

- **Function/macro renames**: "rename foo() to bar()"
- **API signature changes**: "add a parameter to all calls of func()"
- **Pattern replacement**: "replace open-coded pattern X with helper Y"
- **Wrapping calls**: "wrap all calls to X() with lock/unlock"
- **Removing boilerplate**: "remove redundant NULL checks before kfree()"
- **Type changes**: "change type of parameter from X to Y in all callers"
- **Adding error handling**: "add error check after all calls to X()"
- **Argument reordering**: "swap the 2nd and 3rd arguments to func()"

When the user requests a code change that matches these patterns, offer to
generate a Coccinelle semantic patch instead of editing files individually.

## SmPL Quick Reference

### Rule Structure

```
@ rulename @
metavariable declarations
@@

- old code
+ new code
```

### Metavariable Types

| Type         | Matches                              | Example                    |
|--------------|--------------------------------------|----------------------------|
| expression   | Any C expression                     | `expression E;`            |
| identifier   | Variable/function names              | `identifier func;`         |
| type         | C types                              | `type T;`                  |
| statement    | A full statement                     | `statement S;`             |
| constant     | Literal constants                    | `constant C;`              |
| position     | Source positions (for scripts)       | `position p;`              |
| typedef      | Typedef names                        | `typedef T;`               |
| declarer     | Declaration macros                   | `declarer name DEFINE_X;`  |

### Key Syntax

- `- line` : Remove this line
- `+ line` : Add this line (after a `-` line, it replaces)
- `...`    : Match any code between two points
- `... when != expr` : Match any code that does NOT contain expr
- `... when any` : Match even through error paths
- `<... pattern ...>` : Pattern occurs somewhere in matched code (context only)
- `<+... pattern ...+>` : Pattern occurs somewhere, with modifications allowed
- `\(alt1 \| alt2 \)` : Match alternative patterns
- `f(...)` : Match function call with any arguments

### Virtual Modes

Always use `virtual patch` mode for transformation patches:

```
virtual patch

@ depends on patch @
expression E;
@@

- old_func(E)
+ new_func(E)
```

### Identifier Regex Constraints

Identifiers can be constrained with regex:

```
@ rule @
identifier fn =~ "^my_prefix_";
@@

  fn(...)
```

### CRITICAL: Coccinelle Uses POSIX Regex, NOT PCRE

Coccinelle's regex engine does **not** support Perl/PCRE shorthands. Using
unsupported syntax causes a `lexical error: unrecognised symbol` at parse time.

| Do NOT use (PCRE) | Use instead (POSIX)       |
|--------------------|--------------------------|
| `\w`               | `[a-zA-Z0-9_]`          |
| `\d`               | `[0-9]`                 |
| `\s`               | `[ \t\n]`               |
| `\W`, `\D`, `\S`   | Negate the POSIX class   |

**WRONG:**
```
identifier fn =~ "^trace_\w+_enabled$";
```

**CORRECT:**
```
identifier fn =~ "^trace_[a-zA-Z0-9_]+_enabled$";
```

### CRITICAL: `...` (Ellipsis) Cannot Appear in `+` Context

The `...` metavariable means "match any code sequence." It is valid ONLY in
context (unchanged) or `-` (removal) lines.  Placing `...` on a `+` line
causes: `lexical error: invalid in a + context: ...`

**WRONG:**
```
  if (!enabled_fn())
      return
-         ...;
+         ...;
```

**CORRECT** (leave `return ...;` as context — only modify what actually changes):
```
  if (!enabled_fn())
      return ...;
  ...
- call_fn(ES)
+ new_fn(ES)
```

### CRITICAL: `##` Does NOT Work for Matching

SmPL's `##` operator is ONLY for creating **fresh** (new) identifiers on the
replacement side. It CANNOT be used to match related identifiers.

**WRONG** -- this does not work:
```
@ rule @
identifier name;
@@

- trace_##name##_enabled()
```

When you need to match a family of related names (e.g., match
`trace_FOO_enabled()` and the corresponding `trace_FOO()` where FOO is the
same), you MUST use a Python script rule to derive the related names.

### CRITICAL: Do Not Declare Unused Metavariables

Every metavariable declared in a rule MUST appear in the `-` or context code.
Unused declarations produce warnings (`metavariable X not used in the - or
context code`) and indicate a rule logic error. Remove any that are not
referenced.

### Python Script Rules for Related Names

When a transformation involves related identifier families (names that share a
common substring), use this three-step pattern:

1. **Match rule**: capture the identifier with a regex constraint
2. **Script rule**: derive related identifiers via Python
3. **Transformation rules**: use both captured and derived identifiers

```
// Step 1: Match the anchor identifier
@r@
identifier anchor_fn =~ "^prefix_[a-zA-Z0-9_]+_suffix$";
position p;
@@

anchor_fn@p(...)

// Step 2: Derive related names
@script:python s@
anchor_fn << r.anchor_fn;
related_fn;
replacement_fn;
@@

import re
m = re.match(r'^prefix_(.+)_suffix$', anchor_fn)
coccinelle.related_fn = "other_prefix_%s" % m.group(1)
coccinelle.replacement_fn = "new_prefix_%s" % m.group(1)

// Step 3: Transform using derived names
@ depends on patch @
identifier r.anchor_fn;
identifier s.related_fn;
identifier s.replacement_fn;
expression list ES;
@@

  if (anchor_fn())
-     related_fn(ES);
+     replacement_fn(ES);
```

Script-generated identifiers work for BOTH matching and replacement in
subsequent rules.  This is the correct way to correlate identifier families.

## Common Patterns

### Simple function rename
```
virtual patch

@ depends on patch @
expression list ES;
@@

- old_name(ES)
+ new_name(ES)
```

### Add a parameter
```
virtual patch

@ depends on patch @
expression E1, E2;
@@

- func(E1, E2)
+ func(E1, E2, NEW_DEFAULT)
```

### Remove a parameter
```
virtual patch

@ depends on patch @
expression E1, E2, E3;
@@

- func(E1, E2, E3)
+ func(E1, E3)
```

### Replace open-coded pattern with helper
```
virtual patch

@ depends on patch @
expression a, b;
identifier tmp;
type T;
@@

- T tmp;
  ...
- tmp = a;
- a = b;
- b = tmp;
+ swap(a, b);
```

### Remove redundant NULL check
```
virtual patch

@ depends on patch @
expression E;
@@

- if (E)
-   kfree(E);
+ kfree(E);
```

### Wrap a call with locking
```
virtual patch

@ depends on patch @
expression E, lock;
@@

+ spin_lock(&lock);
  func(E);
+ spin_unlock(&lock);
```

### Multi-rule: find struct, then transform callers
```
virtual patch

@ r @
identifier fn;
type T;
@@

  T fn(...) { ... }

@ depends on patch && r @
expression E;
@@

- old_api(E)
+ new_api(E, 0)
```

## Guarded Call Site Patterns

When transforming calls that are guarded by an enabled/feature check, you must
handle ALL of the following `if` guard variations.  Failing to cover them all
will silently miss call sites.

### 1. Simple guard (no braces)
```
  if (enabled_fn())
-     call_fn(ES);
+     new_fn(ES);
```

### 2. Guard with extra condition (no braces)
```
  if (enabled_fn() && COND)
-     call_fn(ES);
+     new_fn(ES);
```

### 3. Braced block (with possible setup code)
Uses `<+... ...+>` to match the call at any nesting depth (e.g., inside
loops, conditionals, or other blocks within the guard).  Plain `...` only
matches at the same block level and will miss calls inside nested loops.
```
  if (enabled_fn()) {
    <+...
-   call_fn(ES)
+   new_fn(ES)
    ...+>
  }
```

### 4. Braced block with extra condition
```
  if (enabled_fn() && COND) {
    <+...
-   call_fn(ES)
+   new_fn(ES)
    ...+>
  }
```

### 5. Negated early return (direct)
```
  if (!enabled_fn())
      return ...;
  ...
- call_fn(ES)
+ new_fn(ES)
```

### 5b. Negated early return (nested in loops)
```
  if (!enabled_fn())
      return ...;
  ... when any
  {
    <+...
-   call_fn(ES)
+   new_fn(ES)
    ...+>
  }
```

### 6. `unlikely()` wrapper (no braces)
```
  if (unlikely(enabled_fn()))
-     call_fn(ES);
+     new_fn(ES);
```

### 7. `unlikely()` wrapper (braced block)
```
  if (unlikely(enabled_fn())) {
    <+...
-   call_fn(ES)
+   new_fn(ES)
    ...+>
  }
```

Write a SEPARATE SmPL rule for EACH variation.  Do not try to combine them
into a single rule -- Coccinelle matches structurally and each `if` form is
a distinct AST shape.

## Execution Procedure

After generating the .cocci file, execute the full pipeline automatically:

1. **Write the .cocci file** to the current working directory with a descriptive
   name (e.g., `rename_foo_to_bar.cocci`).

2. **Test for parse errors** by running:

   ```
   make coccicheck COCCI=./script.cocci MODE=patch 2>&1 | head -20
   ```

   If there are parse errors, fix the .cocci file and re-test. Common errors:
   - `unrecognised symbol:\w` → use `[a-zA-Z0-9_]` (POSIX regex)
   - `invalid in a + context: ...` → `...` cannot appear on `+` lines
   - `metavariable X not used` → remove unused declarations

3. **Capture the full patch** and list affected files:

   ```bash
   make coccicheck COCCI=./script.cocci MODE=patch 2>/dev/null > /tmp/full.patch
   grep '^diff -u' /tmp/full.patch | sed 's|diff -u -p a/||; s| b/.*||' | sort
   ```

4. **Generate and run the per-subsystem apply script** (see below) to create
   one git commit per affected subsystem.

5. **Show the final commit log** so the user can review the series.

## Per-Subsystem Apply Script

Generate a shell script (`scripts/<name>_apply.sh`) that splits the coccicheck
output into per-subsystem commits. The script must:

1. Run coccicheck once and capture the full patch to a tempfile
2. Map each affected file to a subsystem name using a `case` statement
3. Group files by subsystem, preserving order of appearance
4. For each subsystem: extract hunks, `git apply`, `git add` specific files,
   and `git commit` with a descriptive message citing the Coccinelle script

### Key implementation details

**File-to-subsystem mapping** — use a case statement with most-specific paths
first. For example, `kernel/sched/*` must come before `kernel/*`, otherwise
sched files get claimed by the broader `kernel` group and the sched patch
fails to apply (the files were already modified by an earlier commit).

**File-based filtering, not directory-based** — when extracting per-subsystem
hunks, filter by exact file membership, not directory prefix. This avoids
the overlap problem where `kernel/sched/ext.c` matches both `kernel/sched/`
and `kernel/`.

**Stage specific files** — use `git add <file>` for each affected file, never
`git add -A`, to avoid accidentally committing unrelated untracked files.

### Commit message format

```
<subsystem>: <short description>

<Explanation of what the transformation does and why.>

Generated with:
  make coccicheck COCCI=./script.cocci MODE=patch

Coccinelle SmPL rule: ./script.cocci
```

### Script template

```bash
#!/bin/bash
set -e

COCCI=./script.cocci
FULL_PATCH=$(mktemp)
trap "rm -f $FULL_PATCH" EXIT

echo "==> Generating full patch..."
make coccicheck COCCI="$COCCI" MODE=patch 2>/dev/null > "$FULL_PATCH"

if [ ! -s "$FULL_PATCH" ]; then
	echo "No changes produced."
	exit 0
fi

# Map each file to a subsystem name.
# More specific paths MUST come before less specific ones.
file_to_subsystem() {
	local f="$1"
	case "$f" in
		# Add subsystem mappings here, e.g.:
		# kernel/sched/*)  echo "sched" ;;
		# kernel/*)        echo "kernel" ;;
		*)                 echo "misc" ;;
	esac
}

# Build per-subsystem file lists
ALL_FILES=$(grep '^diff -u' "$FULL_PATCH" | sed 's|diff -u -p a/||; s| b/.*||')

declare -a SUBSYSTEM_ORDER=()
declare -A SUBSYSTEM_FILES=()
declare -A SEEN=()

while IFS= read -r file; do
	subsys=$(file_to_subsystem "$file")
	if [ -z "${SEEN[$subsys]}" ]; then
		SUBSYSTEM_ORDER+=("$subsys")
		SEEN[$subsys]=1
	fi
	if [ -n "${SUBSYSTEM_FILES[$subsys]}" ]; then
		SUBSYSTEM_FILES[$subsys]+=$'\n'"$file"
	else
		SUBSYSTEM_FILES[$subsys]="$file"
	fi
done <<< "$ALL_FILES"

echo "==> Found ${#SUBSYSTEM_ORDER[@]} subsystems with changes."

for subsys in "${SUBSYSTEM_ORDER[@]}"; do
	echo "==> Applying to $subsys..."

	TMP_PATCH=$(mktemp)
	FILE_LIST="${SUBSYSTEM_FILES[$subsys]}"

	# Extract only the diffs for this subsystem's files
	awk '
		/^diff -u/ {
			match($0, /a\/([^ ]+)/, m)
			file = m[1]
			printing = 0
		}
		{ if (!printing && /^diff -u/) {
			n = split(files, arr, "\n")
			for (i = 1; i <= n; i++) {
				if (file == arr[i]) {
					printing = 1
					break
				}
			}
		}}
		printing { print }
	' files="$FILE_LIST" "$FULL_PATCH" > "$TMP_PATCH"

	if [ ! -s "$TMP_PATCH" ]; then
		rm -f "$TMP_PATCH"
		echo "    (no changes, skipping)"
		continue
	fi

	git apply "$TMP_PATCH"

	while IFS= read -r f; do
		git add "$f"
	done <<< "$FILE_LIST"

	git commit -m "$(cat <<EOF
${subsys}: <short description>

<Explanation of the transformation.>

Generated with:
  make coccicheck COCCI=${COCCI} MODE=patch

Coccinelle SmPL rule: ${COCCI}
EOF
)"

	rm -f "$TMP_PATCH"
	echo "    committed."
done

echo "==> Done. $(git log --oneline HEAD~${#SUBSYSTEM_ORDER[@]}..HEAD | wc -l) commits created."
```

Populate the `file_to_subsystem()` case statement based on the actual affected
file paths from step 3, and fill in the commit message template with the
appropriate description for the transformation.

## Guidelines

- Keep rules minimal. Do not add `context`, `org`, or `report` virtual modes
  unless asked -- the user wants a transformation, not a linting tool.
- Use `expression list ES;` with `f(ES)` for matching all arguments when you
  do not care about specific arguments.
- Use `expression E1, E2;` when you need to reference specific arguments.
- Use `identifier` for names that must match literally (struct field names,
  function names in declarations).
- Use `type T;` when the type itself varies and must be preserved.
- Use `...` (ellipsis) sparingly -- it can make matches very broad.
- `...` is ONLY valid in context or `-` lines, NEVER in `+` lines.
- Prefer multiple focused rules over one complex rule.
- Write a separate rule for each structural `if` variation (see Guarded Call
  Site Patterns above).  Do NOT assume one rule handles them all.
- Use POSIX character classes in regex (`[a-zA-Z0-9_]`), never PCRE (`\w`).
- Do not declare metavariables that are not used in `-` or context code.
- Test with `MODE=report` or `MODE=context` before `MODE=patch` when the
  pattern is complex.
- Reference existing scripts in `scripts/coccinelle/` for idiom examples.
- NEVER use `##` for matching -- it only works for fresh identifier creation.
  Use Python script rules to derive related identifiers (see above).
