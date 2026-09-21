# nfs-utils Patch Review Protocol

## Overview

Systematic review of nfs-utils patches for correctness, regressions, and
security exposure. nfs-utils is userspace C: a set of independent programs
(daemons, CLI tools, kernel upcall handlers) sharing static and shared
libraries under `support/`.

## Pre-Review Setup

1. ALWAYS load `technical-patterns.md` first.
2. Load subsystem files as directed by TASK 1.
3. Consult `false-positive-guide.md` before reporting anything.

## TASK 0: Identify What Changed

- List every changed file, and every function modified within it.
- Note whether each changed file is: a daemon, a one-shot CLI tool, a kernel
  upcall handler, or shared library code under `support/`.
- Note whether any changed code is **generated** — rpcgen output
  (`sm_inter_*.c`, `mount_clnt.c`, `mount_xdr.c`) or YNL uapi headers
  (`support/include/{nfsd,lockd,sunrpc}_netlink.h`). Generated files have their
  own rules; see the relevant subsystem file.
- Check whether the change also touches `configure.ac` or a `Makefile.am`. If
  it adds a symbol, file, or library, it usually must.

## TASK 1: Subsystem Context Loading

Read `subsystem/subsystem.md` and load **every** matching guide, not just the
most specific one. A patch that adds a netlink command to `exportfs` matches
both the Netlink and the Export rows.

## TASK 2: Per-Function Analysis

For each modified function:

### 2.1 Error handling and propagation
- Does the function follow its file's convention — negative errno, `-1`/errno,
  or `NULL`?
- Is a new `xlog_err()`/`xlog_errno()` being added? Both `exit(1)`. In a
  daemon's request path that is a remote-triggerable denial of service.
- Does the code after an `xlog_err()` assume it returned? (It does not.)
- Is `export_errno` still set for conditions that must change `exportfs`'s exit
  status? Only `xlog(L_ERROR, ...)` sets it.

### 2.2 Resource management
- Every acquire/release pair from the table in `technical-patterns.md`, on
  **every** exit path including error branches.
- `freeaddrinfo()` must be `nfs_freeaddrinfo()`.
- A `CLIENT *` from `nfs_get_rpcclient()` needs `CLNT_DESTROY()`.
- Does a new early `return`/`goto` skip a release that the original path did?

### 2.3 Allocation
- Plain `malloc`/`calloc`/`strdup`: NULL-checked?
- `xmalloc`/`xstrdup`: is this a `mount`/`exportfs` path? If it is a daemon or
  daemon-linked library path, the fatal-on-OOM behaviour is a regression.

### 2.4 Buffers and strings
- Destination sizing for every copy; `strlcpy`/`strlcat` preferred for new code.
- `strncpy` without a following NUL unless the buffer was zeroed.
- `snprintf` return value handling: it returns what *would* have been written,
  so `if (ret >= sizeof(buf))` is truncation, and `buf + ret` after a truncated
  write walks off the end.
- Any fixed buffer receiving network, upcall, or netlink data.

### 2.5 Control flow
- **`switch` over `sa_family_t` or any non-enum: check every case for a missing
  `break`.** The build does not enable `-Wimplicit-fallthrough`, so this is
  silent. If a fallthrough is intended, it needs a comment saying so.
- Integer overflow in size arithmetic before an allocation or a copy.
- Sign of comparisons against `read()`/`write()`/`recv()` returns.

### 2.6 Privilege, ordering, and daemon lifecycle
- Any new code between `daemon_init()` and `daemon_ready()` that can return
  early — that is a startup hang.
- Any reordering around a privilege drop. `setgid()` before `setuid()`;
  root-only work before the drop.
- New signal handlers: does one collide with xlog's `SIGUSR1`/`SIGUSR2`?
- Files created by a daemon: correct owner and mode after the drop?

### 2.7 Conditional build correctness
- Does the change compile with the relevant `--enable`/`--disable` inverted?
- New symbol used from a component that can be configured out — is the
  reference guarded, and is the `Makefile.am` link line right? This is a
  recurring breakage (`exportfs: link failure with --disable-nfsdctl`).
- New `#ifdef HAVE_X`: is there an `#else` stub that fails cleanly?

## TASK 3: Integration Analysis

- **Callers.** Who calls the changed function, and does the change alter its
  contract — return convention, ownership of a returned pointer, whether it can
  now return where it previously exited?
- **On-disk and on-wire formats.** `etab`, `rmtab`, `/var/lib/nfs/sm/*`, the
  nfsdcld sqlite schema, and the kernel upcall text formats are all
  compatibility surfaces. A format change needs an upgrade path.
- **Kernel interface compatibility.** Userspace must keep working against older
  kernels. Feature use needs runtime detection, not a build-time assumption.
  See `subsystem/netlink.md`.
- **Cross-tree changes.** If the patch pairs with a kernel change, the kernel
  side's invariants are in `../kernel/subsystem/nfsd.md` and
  `../kernel/subsystem/sunrpc.md` (available when the kernel prompt set is also
  installed).

## Severity Classification

**CRITICAL** — remotely or locally exploitable, or data loss.
- Path traversal from a wire-supplied name (the statd class).
- Buffer overflow from network, upcall, or netlink input.
- Privilege drop that does not actually drop, or ordering that leaves a window.
- Bypass of the `rootdir=` confinement by touching paths outside `nfsd_path_*`.
- Export ACL bypass — skipping the reverse/forward DNS cross-check, wrong
  client-spec match.

**HIGH** — functional breakage or resource exhaustion.
- Leaks in a daemon's per-request path.
- `xlog_err()` reachable from a remote request (daemon dies).
- Startup hang from a missed `daemon_ready()`.
- Build breakage under a supported `--enable`/`--disable` combination.
- On-disk or on-wire format change with no compatibility handling.
- **A control tool's normal path silently misconfiguring a daemon.**
  `exportfs`, `rpc.nfsd` and `nfsdctl` are short-lived, but their output is a
  long-running server's runtime state. A wrong export, a duplicated listener,
  or a removal that reports success without removing anything is HIGH even
  though the tool itself exits cleanly — judge by what the daemon is left in,
  not by the lifetime of the process that got it wrong.

**MEDIUM** — real but bounded.
- Leaks on a one-shot CLI error path.
- Missing runtime feature detection against older kernels.
- Truncation that produces a wrong diagnostic rather than a wrong action.

**LOW** — cosmetic or defensive. Usually not worth reporting. Never report
style alone.

## False Positive Check

Before reporting **anything**:

1. Read `false-positive-guide.md`. Several correct idioms in this tree look
   like bugs.
2. Confirm the path is reachable. Trace it concretely.
3. Confirm the code is actually compiled in a normal configuration.
4. Confirm it is not generated code.
5. For anything in unchanged context lines: legacy code is grandfathered.
   Report idiom violations against `+` lines.

## Output

When issues survive the false-positive check, produce `review-inline.txt`
using `inline-template.md`. For each issue: file and line, severity, what is
wrong, the concrete path that reaches it, and a suggested fix.

If nothing survives, say so plainly. Do not pad a review with LOW findings.
