---
name: process-failed-reviews
description: Batch process review-failed.md files across multiple directories, updating subsystem guides and committing after each
tools: Read, Write, Glob, Bash, Task, TaskCreate, TaskUpdate, TaskList
---

# Process Failed Reviews Agent

This agent batch processes `review-failed.md` files across multiple commit
directories, running the failed-review agent on each one sequentially and
committing subsystem guide changes after each directory completes.

## Input

You will be given:
1. Working directory containing `linux.<sha>/` subdirectories
2. The prompt directory path (contains `agent/`, `subsystem/`, and pattern files)

Each `linux.<sha>` subdirectory contains a `review-failed.md` file to process.

## Workflow

### Step 1: Discover Directories

Find all directories matching `linux.*/review-failed.md`:

```bash
find . -maxdepth 2 -name "review-failed.md" -path "./linux.*/*" 2>/dev/null | \
  sed 's|^\./||; s|/review-failed.md||' | sort
```

### Step 2: Create Task List

Create a task for each directory using TaskCreate:

```
Subject: Process linux.<sha> review-failed.md
Description: Run failed-review agent on linux.<sha>/review-failed.md, output to linux.<sha>/failed-review-report.md
ActiveForm: Processing linux.<sha>
```

### Step 3: Process Each Directory Sequentially

For each directory, in order:

1. **Mark task in_progress**

2. **Run failed-review subagent**:
   ```
   Task(
     description: "Failed-review linux.<sha>",
     subagent_type: "general-purpose",
     prompt: """
       You are the failed-review agent. Follow the instructions in
       <prompt_dir>/agent/failed-review.md

       Working directory: <work_dir>/linux.<sha>
       Prompt directory: <prompt_dir>

       Read ./review-failed.md and process it according to the failed-review.md
       instructions. Write your report to ./failed-review-report.md

       You may need to add or sharpen questions in <prompt_dir>/subsystem/questions/
       based on the classification of missed bugs. Never edit a guide in
       <prompt_dir>/subsystem/*.md: those are build output.
     """
   )
   ```

3. **Check for changes and commit if needed**:

   Check git status for both modified and untracked files:
   ```bash
   cd <prompt_dir>/.. && git status
   ```

   Look for **modified files** under `kernel/subsystem/questions/`. If a guide
   itself (`kernel/subsystem/build/linus/<guide>.md`) or anything else under
   `kernel/subsystem/build/` shows as modified, the agent edited build output:
   restore it with `git checkout --` and do not commit it.

   If there are changes in `kernel/subsystem/questions/`:
   ```bash
   cd <prompt_dir>/.. && \
     git add kernel/subsystem/questions/ && \
     git commit -s -m "$(cat <<'EOF'
   questions[/<guide>]: <brief description of changes>

   <1-2 sentence explanation of what is now asked, and that <guide> needs rebuilding>

   Learned from: <sha> ("<commit subject>")
   EOF
   )"
   ```

   Common scenarios:
   - **Question added**: e.g., `kernel/subsystem/questions/drm.md` gains a question
   - **Question sharpened**: an existing question's text changes, its id does not

   The guides change only when the maintainer rebuilds them with
   `kernel/scripts/rebuild-guides.sh`; keep a list of the guides that need it and
   give it at the end.

4. **Mark task completed**

5. **Continue to next directory**

## Commit Message Format

```
questions[/<guide>]: <brief description>

<What is now asked and why it matters; <guide> needs rebuilding>

Learned from: <sha> ("<commit subject>")
```

Examples:
- `questions/drm: ask which commit callbacks run in atomic context`
- `questions/drm: ask what system PM and runtime PM callbacks may do`
- `questions/btrfs: ask how the active zone limit is enforced`

## Important Notes

- **Sequential processing required**: Agents must run one at a time to avoid
  conflicts when updating shared question files
- **Commit after each directory**: Do not batch commits; commit immediately
  after each directory that produces changes
- **Skip commits when no changes**: If the failed-review agent classifies all
  bugs as `process error` or `other`, there will be no question changes to commit
- **Use signed commits**: Always use `git commit -s`

## Reference

**Directory layout**:
```
<prompt_dir>/
├── agent/
│   ├── failed-review.md
│   ├── process-failed-reviews.md  (this file)
│   └── ...
├── subsystem/
│   ├── subsystem.md
│   ├── questions/            (what the guides are built from; the only thing edited here)
│   └── build/linus/          (the built guides; the build writes all of it)
│       ├── subsystem-guide-index.txt   (the index a review searches)
│       ├── kernel-version.yaml
│       ├── networking-core.md
│       ├── networking-drivers.md
│       ├── drm.md
│       ├── locking.md
│       ├── races.md
│       └── ...
├── technical-patterns.md
└── ...

<work_dir>/
├── linux.<sha1>/
│   ├── review-failed.md        (input)
│   └── failed-review-report.md (output)
├── linux.<sha2>/
│   ├── review-failed.md
│   └── failed-review-report.md
└── ...
```

## Final Output

After all directories are processed, report:
```
================================================================================
PROCESS-FAILED-REVIEWS COMPLETE
================================================================================

Directories processed: <count>
Commits made: <count>

Code no guide covers (needs a new build set):
  - <path>: <description>

Question files changed (their guides need rebuilding):
  - <path>: <question id added or sharpened>

Classifications summary:
  missing subsystem knowledge: <count> (questions added or sharpened)
  process error: <count> (no changes)
  other: <count> (no changes)
================================================================================
```
