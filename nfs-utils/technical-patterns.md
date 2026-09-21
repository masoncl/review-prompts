# nfs-utils Technical Deep-dive Patterns

## Core Instructions

- Trace full execution flow; gather context from the call chain before judging
  a function in isolation.
- IMPORTANT: never make assumptions based on return types, checks, or comments.
  Verify by tracing concrete execution paths.
- IMPORTANT: never skip a step just because you found a bug in a previous step.
- Never report an error without first checking whether it is reachable on any
  real call path.
- nfs-utils is a **collection of separate programs**, not one binary. The same
  library function is linked into a short-lived CLI tool (`exportfs`,
  `mount.nfs`) and into a long-running root daemon (`rpc.mountd`, `rpc.statd`).
  Whether a given behaviour is a bug often depends on which one you are in.

## Logging: xlog

`support/include/xlog.h`, `support/nfs/xlog.c`.

**Levels** — always logged:

| Constant | Value | syslog priority |
|---|---|---|
| `L_FATAL` | 0x0100 | `LOG_ERR` — **and `exit(1)`** |
| `L_ERROR` | 0x0200 | `LOG_ERR` |
| `L_WARNING` | 0x0400 | `LOG_WARNING` |
| `L_NOTICE` | 0x0800 | `LOG_NOTICE` |

**Debug facilities** — only logged when enabled via `xlog_config()`/
`xlog_sconfig()`/`xlog_set_debug()`: `D_GENERAL`, `D_CALL`, `D_AUTH`,
`D_NETLINK`, `D_FAC4`, `D_FAC5`, `D_PARSE`, `D_FAC7`. These reach syslog at
`LOG_INFO` only when stderr logging is off. Do not OR a `D_` with an `L_`; the
code does not expect it.

**`xlog_err()` and `xlog_errno()` never return.** Both call
`xlog_backend(L_FATAL, ...)`, and `xlog_backend()` ends with
`if (kind == L_FATAL) exit(1);`. Consequences for review:

- Code after `xlog_err()` is unreachable. A missing NULL check there is **not**
  a bug. See the false-positive guide.
- Converting an `xlog_err()` to `xlog_warn()` (or vice versa) silently changes
  control flow for every line after it. Any such change needs the following
  code re-examined.
- `xlog_err()` in a long-running daemon kills the daemon. Flag new
  `xlog_err()` calls added to a request-handling path — a per-request failure
  should almost never terminate `rpc.mountd` or `rpc.statd`.

**`xlog_warn()`** is `L_WARNING` and does return.

**`export_errno`** is a global set by `xlog(kind, ...)` when
`kind & (L_ERROR|D_GENERAL)`. `exportfs` and `mountd` turn it into a non-zero
exit status. Note it is set by `xlog()` only — `xlog_err()`/`xlog_warn()` call
`xlog_backend()` directly and do not touch it. New diagnostics that should
affect the exit code must go through `xlog(L_ERROR, ...)`.

**Format strings** are compile-checked via `XLOG_FORMAT` when
`HAVE_FUNC_ATTRIBUTE_FORMAT` is defined, and the tree builds with
`-Werror=format=2`, so a non-literal format string will not compile.

## Memory Allocation: two conventions

There are two, and mixing them up is a real bug class.

**Fatal wrappers** — `xmalloc()`, `xrealloc()`, `xstrdup()`, `xstrndup()`,
`xstrconcat2/3/4()`, `die()`, declared in `support/include/xcommon.h`
(`support/include/xmalloc.h` is now just a shim that includes it). These
**abort the process on OOM**. Their return values are deliberately unchecked
at call sites.

They came in with the util-linux-derived `mount.nfs` code, but their use is
**not** confined to it: `support/export/export.c`, `utils/mountd/mountd.c`,
`utils/statd/statd.c` and `utils/statd/notlist.c` all call them, and
`libexport.a` carries them into every program that links it. Do not assume
"this is a daemon, so `x*` must be wrong here".

**Plain allocation** — `malloc()`/`calloc()`/`strdup()` with an explicit NULL
check that logs and returns an error. This is the majority convention in
`support/` (e.g. `support/nfs/conffile.c`, `support/export/client.c`,
`support/nsm/file.c`) and in the newer daemons.

Review rules:
- An unchecked `x*` call is correct by contract. Do **not** flag it, wherever
  it appears. Existing use throughout the daemons is grandfathered.
- Flag an unchecked plain `malloc()`/`calloc()`/`strdup()` anywhere.
- The one case worth raising is a **newly added** fatal allocation on a
  daemon's per-request path — a remote client that can drive `rpc.mountd` to
  `xmalloc()` an attacker-sized buffer can abort it on OOM. That is a denial
  of service. Frame it as "this specific new call site", not as "`x*` does not
  belong in a daemon".

## Resource Pairing

The recurring leak shapes in this tree:

| Acquire | Release | Notes |
|---|---|---|
| `getaddrinfo()` | **`nfs_freeaddrinfo()`** | see below |
| `nfs_get_rpcclient()`, `nfs_get_priv_rpcclient()` | `CLNT_DESTROY()` | on every exit path, including errors |
| `conf_get_list()` | `conf_free_list()` | |
| `opendir()` | `closedir()` | `support/nsm/file.c` |
| `nl_socket_alloc()` / `nlmsg_alloc()` | `nl_socket_free()` / `nlmsg_free()` | see `subsystem/netlink.md` |

**Never call `freeaddrinfo()` directly.** `support/include/nfslib.h` defines:

```c
/*
 * Some versions of freeaddrinfo(3) do not tolerate being
 * passed a NULL pointer.
 */
static inline void nfs_freeaddrinfo(struct addrinfo *ai)
{
	if (ai)
		freeaddrinfo(ai);
}
```

A new direct `freeaddrinfo()` call is a portability regression. Existing
callers are consistent — `support/export/hostname.c`, `support/nfs/getport.c`,
`support/export/client.c`, `utils/statd/sm-notify.c`.

## String and Buffer Handling

- **Use the bundled `strlcpy()`/`strlcat()`** (`support/nfs/strlcpy.c`,
  `strlcat.c`, declared in `nfslib.h`) for new truncating copies.
- The tree's existing idiom is `strncpy(dst, src, N); dst[N-1] = '\0';`. That
  is correct; do not flag it. Flag `strncpy()` with **no** following
  termination, unless the destination was demonstrably zeroed first.
- `strncpy(buf, s, buflen - 1)` onto a buffer that was just `memset()` to zero
  (the `host_ntop()` idiom in `support/export/hostname.c`) is correct only
  because of the `memset`. Copying that idiom to a non-zeroed buffer is a bug.
- Fixed-size path buffers are sized `NFS_MAXPATHLEN + 1`
  (`struct exportent.e_path`, `struct rmtabent.r_path` in `nfslib.h`). Upcall
  buffers add explicit slack for the encoded protocol text — see
  `export_test()` in `support/export/export.c`, `char buf[NFS_MAXPATHLEN+1+64]`.
  Adding a field to an upcall format means re-deriving that slack.
- `streq(s, t)` (`xcommon.h`) is the `strcmp(...) == 0` shorthand used in
  `mount`/`exportfs` code.

## Conditional Compilation

Two mechanisms, and you must check both:

1. `#ifdef HAVE_*` / `#ifdef ENABLE_*` / `#ifdef IPV6_SUPPORTED` inside `.c`
   files, driven by autoconf-generated `config.h`. Every file starts with:
   ```c
   #ifdef HAVE_CONFIG_H
   #include <config.h>
   #endif
   ```
2. Whole files and whole directories selected in `Makefile.am` under
   `if CONFIG_X ... endif`.

So "is this code compiled?" cannot be answered from the `.c` file alone.
See `subsystem/build.md`.

Every `#ifdef HAVE_X` needs an `#else` stub that **compiles cleanly and
returns a real error** — the pattern is `errno = ENOSYS; return -1;`
(`nfsd_name_to_handle_at()` in `support/misc/nfsd_path.c`). A stub that
silently succeeds is a bug. Unused parameters in stubs use the `UNUSED()`
macro from `nfslib.h`:

```c
#define UNUSED(x) UNUSED_ ## x __attribute__((unused))
```

which also renames the parameter, so accidental use will not compile.

## Compiler Warnings Already Enforced

`configure.ac` sets, among others: `-Wall -Wextra -Werror=missing-prototypes
-Werror=missing-declarations -Werror=format=2 -Werror=undef
-Werror=missing-include-dirs -Werror=strict-aliasing=2 -Werror=init-self
-Werror=implicit-function-declaration -Werror=return-type -Werror=switch
-Werror=overflow -Werror=parentheses -Werror=aggregate-return
-Werror=unused-result`, plus `-Werror=format-overflow=2`,
`-Werror=int-conversion`, `-Werror=incompatible-pointer-types`,
`-Werror=misleading-indentation` when the compiler supports them.

Two implications:

- Do not report a class of defect the build already rejects. An unchecked
  return from a `warn_unused_result` function, a missing prototype, or a
  missing `return` will not have compiled.
- **`-Wimplicit-fallthrough` is NOT enabled.** A `switch` case that falls
  through to the next without `break` compiles silently. `-Werror=switch` only
  catches unhandled *enum* values, which does not apply to `sa_family_t`
  switches. Missing-`break` in a `switch` over an address family is therefore
  a live, unguarded bug class in this tree — check every such switch.

## Daemon Skeleton

`support/nfs/mydaemon.c`, `support/nfs/closeall.c`.

`daemon_init(bool fg)` is a `daemon()` replacement that keeps the parent alive
until the child is genuinely ready: it creates a pipe, forks, and the parent
blocks in `read()` on that pipe, exiting with whatever status the child writes.
The child `setsid()`s, `chdir("/")`s, redirects stdio to `/dev/null`, forces the
status pipe to fd 3, and calls `closeall(4)`.

**Every success path after `daemon_init()` must reach `daemon_ready()`**, or
the foreground parent — and whatever `systemd` unit is waiting on it — hangs
forever. A new early-return between `daemon_init()` and `daemon_ready()` is a
startup hang. `daemon_ready()` is idempotent-safe (it clears `pipefds[1]`).

Standard startup order in the daemons: `getopt_long()` with a static
`struct option longopts[]` → `xlog_open()` → `conf_init_file(NFS_CONFFILE)` →
`daemon_init()` → subsystem setup → `daemon_ready()`.

**Signal trap:** `xlog_open()` installs its own `SIGUSR1`/`SIGUSR2` handlers to
toggle debug verbosity at runtime. A daemon that later installs its own
`SIGUSR1` handler silently replaces that facility — `rpc.statd` does exactly
this. When reviewing new signal wiring, note whether it collides with xlog's.

## Privilege and Ordering

Root-privileged daemons that drop privileges have order-sensitive startup, and
the ordering is a security property. `utils/statd/statd.c` carries explicit
`/* ORDER */` comments; `nsm_drop_privileges()` in `support/nsm/file.c` is the
canonical drop sequence. Details in `subsystem/statd.md`. The general rules:

- `setgid()` **before** `setuid()`. The reverse silently fails to drop the
  group.
- `setgroups(0, NULL)` to clear supplementary groups.
- Anything requiring root — unregistering an rpcbind listener, binding a
  reserved port — happens before the drop, not after.
- File descriptors that must survive the drop are opened and `fchown()`ed
  first (the pidfile fd pattern).

## Coding Style

There is no `CodingStyle` document in this tree and the code is not internally
consistent. It is broadly kernel-like: tabs, 8-column indent, K&R braces.

**Do not raise style-only findings.** Match the surrounding file. Style is
worth a comment only when it obscures a real defect (misleading indentation
around a missing brace, for example).

## Untrusted Input

Treat as attacker-influenced, even when it arrives via the kernel:

- MOUNT and NSM/NLM RPC arguments (`rpc.mountd`, `rpc.statd`) — off the network.
- Kernel cache upcall text on `/proc/net/rpc/*/channel` — the content is
  client-supplied paths and addresses relayed by nfsd.
- Netlink attribute payloads — bound by `nla_len()`, not only by the
  destination buffer size.
- `mount.nfs` argv and option strings — it is a setuid helper.
- `/etc/exports` and `nfs.conf` are administrator input: not hostile, but
  malformed input must produce a diagnostic, not a crash.
