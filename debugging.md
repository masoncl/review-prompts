DEBUGGING  PROTOCOL - ALL TASKS ARE MANDATORY

You're debugging a crash or warning in the linux kernel and were given a crash
message either in a file or in stdin.

If a review prompt directory is not provided, assume it is in the same
directory as this prompt file.

Before creating debug-report.txt, you MUST complete ALL steps below.
Use TodoWrite tool to track each step. Mark as BLOCKED if you cannot complete any step.

TASK 1: EXTRACT CRASH INFORMATION
- [ ] Find all kernel messages in the sources and assume they contributed to
the problem you're debugging.  Try to prove them as either relevant or not,
and report on what you find.
- [ ] Extract ALL timestamps from ALL messages, don't skip any
- [ ] Identify the event sequence
  - Single event crash vs multi-stage failure
  - Enable -> disable -> enable patterns
  - Process/PID changes between events
- [ ] Map each timestamp to a specific operation
- [ ] Extract ALL function names from crash traces

STATUS CHECK: Mark TASK 1 as "COMPLETED" or "BLOCKED(reason)" before proceeding.

TASK 2: FULL REVIEW PROTOCOL

You MUST now follow the ENTIRE review protocol from review-core.md systematically:

REQUIRED ACTIONS:
1. load review-core.md, but use the functions, types, and kernel messages
from TASK 1 as the entry point into the code that you're reviewing.
2. follow review-core.md instructions to Create TodoWrite checklist with ALL patterns
3. Apply EVERY pattern - document as [CLEAR/ISSUE/NOT-APPLICABLE]
4. Complete verification phase following false-positive-guide.md
  - Because we know we have a crash or kernel bug, assume there is a bug instead
  of trusting the author

DO NOT proceed to debug-report.txt until you state:
"REVIEW PROTOCOL COMPLETE: X/X patterns analyzed"

If you skip this step, you have FAILED to follow the debugging protocol.

STATUS CHECK: Mark TASK 2 as "REVIEW PROTOCOL COMPLETE: X/X patterns analyzed" before proceeding.

TASK 3: PROVE THE BUG WITH CONCRETE EVIDENCE

When trying to identify a bug, apply the false-positive-guide.md, but do shift
the assumption to the code being incorrect instead of correct.

- [ ] bugs still must be proven though, with code snippets and call traces

- If you find a race, you must be able to prove both sides of the race exist
  - [ ] identify the EXACT data structure names and definitions
  - [ ] identify the locks that should protect them
  - [ ] prove the race exists with CODE SNIPPETS
- If you find a use after free, you MUST provide:
  - [ ] EXACT data structure names and definitions
  - [ ] EXACT function name that frees the structure
  - [ ] EXACT function name that uses it after free
  - [ ] CODE SNIPPETS showing both free and use
  - [ ] CALL TRACE proving the sequence occurs
- If you find a deadlock, you must be able to show both sides of the deadlock
  - [ ] identify the EXACT locks involved
  - [ ] identify the exact code taking those locks
  - [ ] prove the deadlock exists with CODE SNIPPETS

STATUS CHECK: Mark TASK 3 as "BUG EVIDENCE COMPLETE" or "INSUFFICIENT EVIDENCE - CANNOT PROVE BUG" before proceeding.

TASK 4: IDENTIFY SUSPECT COMMITS

If you're able to identify the bug, try to identify the commit that introduced
the bug and follow the instructions to create review-inline.txt.

- [ ] As you scan suspect commits, your understanding of the bug may change.
Restart analysis as required if you learn new things.
- [ ] If you have a suspect commit, you must be able to prove that commit caused
the bug.  Otherwise just label it as a likely suspect and explain your reasoning
- [ ] If you're not able to identify suspect commits, state "NO SUSPECTS FOUND"
- Unless instructed by additional prompts, don't bother trying to run addr2line
  or inspect binaries in the working directory, it is unlikely the working
  directory object files match the crashing binary.

STATUS CHECK: Mark TASK 4 as "SUSPECT COMMIT ANALYSIS COMPLETE" or "NO SUSPECTS FOUND" before proceeding.

TASK 5 CREATING debug-report.txt:

- [ ] Name the report debug-report.txt
- [ ] include details of the crash in the plain text syntax.
- [ ] put the crash details above the inline quoting of any problematic commit
- [ ] If you're not able to identify the cause of the crash, just put
whatever information you found into debug-report.txt

TASK 5.1 MANDATORY FORMATTING RULES for debug-report.txt:
- Replace any existing debug-report.txt
- Don't mention TASK numbers in the report, they don't mean anything to people
who aren't working on the prompts
- debug-report.txt is plain text only - no markdown formatting allowed (no ```, **, [], etc.)
  - the report should be suitable for mailing to the linux kernel mailing list
    and is meant to be consumed by linux kernel experts.
  - Never use dramatic wording
  - Never say "this is a classic example of..."
  - Just give a factual explanation of what you found.
  - Use plain text indentation, dashes, and spacing for formatting
  - Code snippets should use simple indentation without backticks
  - Don't use UPPERCASE
  - NEVER use line numbers, instead use filename:function_name(), call graphs and code
  snippets to provide context
- [ ] Except for code snippets, wrap long lines at 78 characters
    - [ ] Count characters and insert line breaks before reaching 78
    - [ ] never line wrap code, reproduce it exactly

STATUS CHECK: Mark TASK 5.1 as "COMPLETE" only after you've acknowledged all of these rules

debug-report.txt TEMPLATE:

Summary of crash or warning

Kernel version if available

Machine type if available

Cleaned up copy of oops or stack trace

Any other kernel messages you found relevant

TASK 5.2
- [ ] If you found a suspect commit, follow the review-inline.txt protocol with bug
details

TASK 5.3
- [ ] If you didn't find a suspect commit:
	- [ ] An explanation of the problem
	- [ ] Functions, snippets and call traces of code related to the problem
	- [ ] a list of potential commits related to the problem
	- [ ] Always suggest fixes or include suspect code, with snippets explaining your comments
	- [ ] All code snippets should be long enough to place the code in the function and
	explain the idea you're trying to convey

STATUS CHECK: Mark TASK 5.3 as "COMPLETE" only if code snippets are sufficient to
explain the points you're making.

STATUS CHECK: Mark TASK 5 as "COMPLETE" only after you've created the report,
and completed TASK 5.1 or TASK 5.2 and verified it exists in the filesystem
