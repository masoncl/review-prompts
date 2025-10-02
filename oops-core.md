You're debugging a crash or warning in the linux kernel and were given a crash
message either in a file or in stdin.

Read the oops and extract all the function names from it, then load the
review-core.md.  Instead of reviewing a diff, have review-core.md load all the
functions from the kernel crash as context, and follow the review protocol as
though those functions had recently changed.

Change the review protocol to assume the code is incorrect based on the evidence
in the crash.

If you're able to identify the bug, try to identify the commit that introduced
the bug and follow the instructions to create review-inline.txt.
- Name the report debug-report.txt instead
- include details of the crash in the plain text syntax.
- put the crash details above the inline quoting of the problematic commit

If you're not able to identify the cause of the crash, just make a report
with whatever information you found into debug-report.txt
