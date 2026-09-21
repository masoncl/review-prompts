---
name: nfs-utils-debug
description: Debug nfs-utils daemon failures and crashes
---

Using the prompt {{REVIEW_DIR}}/debugging.md, analyse the provided failure.

Load {{REVIEW_DIR}}/technical-patterns.md first, then follow the debugging
protocol in debugging.md.

Useful input:

- journalctl or syslog output from the daemon
- a coredump or stack trace
- the exact command and its error message
- `nfsconf --dump`, `exportfs -v`, `rpcinfo -p`, `nfsstat`, `rpcctl` output
- a packet capture
- reproduction steps

The protocol will:

1. Classify the failure and identify the component.
2. Enable the daemon's own xlog debug facilities, which are off by default and
   usually more informative than strace.
3. Inspect the state the daemon exposes under /proc, /sys and /var/lib/nfs.
4. Establish which boundary the failure is on: the wire, the kernel/userspace
   upcall, the configuration, or the build.
5. Read the implicated code with {{REVIEW_DIR}}/subsystem/ loaded for that
   component.
6. Produce debug-report.txt separating what was observed from what was
   inferred.

Two things to rule out early, because they explain a large share of reports:

- A daemon that exits with no crash: look for `xlog_err()` on the path. It
  calls `exit(1)`.
- A daemon that appears to hang at startup and times out under systemd: a
  success path that never reached `daemon_ready()`, leaving the parent blocked
  on the status pipe.
