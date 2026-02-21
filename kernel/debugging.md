# Kernel Crash Debugging

You are debugging a crash or warning in the linux kernel. You were given a
crash message, oops, warning, or stack trace either in a file or in stdin.

Read and execute `kernel/agent/debug.md`. It is a multi-agent orchestrator
that will dispatch specialized agents (code analysis, reproducer analysis,
commit search) to investigate the bug.

Pass through all input (crash reports, reproducers, syzbot URLs, etc.)
to the orchestrator unchanged.
