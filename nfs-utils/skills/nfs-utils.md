---
name: nfs-utils
description: Load anytime the working directory is an nfs-utils tree. nfs-utils specific knowledge, per-daemon details, code review, and debugging protocols. Read this anytime you're in the nfs-utils tree.
invocation_policy: automatic
---

# nfs-utils Skill

AI-assisted code review for nfs-utils, the Linux NFS userland utility package:
`rpc.mountd`, `rpc.statd`, `rpc.gssd`, `rpc.idmapd`, `nfsdcld`, `nfsdctl`,
`exportfs`, `mount.nfs`, and the shared libraries under `support/`.

## ALWAYS READ

1. Load `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/technical-patterns.md`

This file is MANDATORY. This skill is a framework for loading additional
nfs-utils prompts; it is not a substitute for them.

## Activation

This skill applies when working in an nfs-utils source tree, recognisable by:

- `utils/mountd/`, `utils/statd/`, `utils/exportfs/` directories
- `support/nfs/xlog.c` and `support/include/nfslib.h`
- `configure.ac` whose `AC_INIT` names `linux nfs-utils`

## Configuration

The review prompts directory is set at installation time:

- **NFS-UTILS_REVIEW_PROMPTS_DIR**: {{NFS-UTILS_REVIEW_PROMPTS_DIR}}

## Capabilities

### Patch Review

When asked to review an nfs-utils patch, commit, or series:

1. Load `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/review-core.md`
2. Follow the review protocol defined there
3. Load subsystem files as directed
4. Check every candidate finding against
   `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/false-positive-guide.md` before reporting

### Debugging

When asked to debug an nfs-utils failure — a daemon that exits, a mount that
fails, locks that do not recover, a config option with no effect:

1. Load `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/debugging.md`
2. Follow the protocol there
3. Use logs, `/proc` and `/sys` state, and the wire as entry points before
   reading code

### Subsystem Context

Read `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/subsystem/subsystem.md` and load every
matching guide:

| Subsystem | Trigger | File |
|---|---|---|
| SunRPC / libtirpc | `CLIENT *`, `svc_`, `clnt_`, `xdr_`, `.x`, `HAVE_LIBTIRPC` | subsystem/sunrpc.md |
| Netlink | `utils/nfsdctl/`, `nfsdnl.c`, `*_netlink.h`, `nla_`, `NFSD_A_` | subsystem/netlink.md |
| Export / mountd | `utils/{exportfs,mountd,exportd}/`, `support/export/`, `qword_`, etab | subsystem/export.md |
| NSM / statd | `utils/statd/`, `support/nsm/`, `SM_MON`, sm-notify | subsystem/statd.md |
| Upcall daemons | `utils/{gssd,idmapd,nfsdcld,nfsdcltrack,blkmapd}/`, `rpc_pipefs` | subsystem/upcalls.md |
| Mount helper | `utils/mount/`, `CONFIG_LIBMOUNT`, `MOUNT_CONFIG` | subsystem/mount.md |
| nfs.conf | `support/nfs/conffile.c`, `conf_get_` | subsystem/config.md |
| Build | `configure.ac`, `Makefile.am`, `systemd/`, `tools/*.py`, `tests/` | subsystem/build.md |

### Patch Submission

For commit message format, trailers, series structure, and pre-send checks:
`{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/patch-submission.md`.

## Semcode Integration

When available, use semcode MCP tools for code navigation:

- `find_function` / `find_type`: definitions
- `find_callchain`: trace call relationships up and down
- `find_callers` / `find_calls`: explore call graphs
- `grep_functions`: search function bodies with regex
- `diff_functions`: identify functions changed by a patch
- `find_commit` / `vcommit_similar_commits`: search history

The [semcode repository](https://github.com/facebookexperimental/semcode)
documents indexing and MCP server setup.

## Output

- Patch reviews produce `review-inline.txt` when findings survive verification,
  formatted per `{{NFS-UTILS_REVIEW_PROMPTS_DIR}}/inline-template.md`
- Debug sessions produce `debug-report.txt`
- Both are plain text wrapped for `linux-nfs@vger.kernel.org`

## Key nfs-utils Conventions

These are the ones that most often produce wrong conclusions. Full detail is
in `technical-patterns.md`.

- **`xlog_err()` and `xlog_errno()` never return** — they `exit(1)`. Code after
  them is unreachable, so a "missing NULL check" there is not a bug. Adding one
  to a daemon's request path is a denial of service.
- **Two allocation conventions.** `xmalloc`/`xstrdup` abort on OOM and belong
  to `mount`/`exportfs`; their unchecked returns are correct. Plain `malloc`
  must be checked.
- **`nfs_freeaddrinfo()`, never `freeaddrinfo()`.**
- **`nfs_get_rpcclient()` pairs with `CLNT_DESTROY()`** on every exit path.
- **`-Wimplicit-fallthrough` is not enabled.** Missing `break` in a `switch`
  over `sa_family_t` compiles silently and is a live bug class.
- **Two levels of build gating** — `#ifdef` in the `.c` file *and*
  `if CONFIG_X` in the `Makefile.am`. Read both before concluding what is
  compiled.
- **`daemon_ready()` must be reached on every success path**, or startup hangs.
- **`setgid()` before `setuid()`**, always.
- **No formal coding style document exists.** Match the surrounding file; do
  not raise style-only findings.

## Available Commands

- `/nfs-utils-review` — deep regression analysis of a patch or commit
- `/nfs-utils-debug` — debug a daemon failure, crash, or misbehaviour
- `/nfs-utils-verify` — check a reported finding against false-positive patterns
