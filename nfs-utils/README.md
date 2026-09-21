# nfs-utils Review Prompts

AI-assisted code review prompts for nfs-utils, the Linux NFS userland utility
package.

## Installation

From the root of this repository:

```bash
./setup.sh <agent> nfs-utils
```

Run `./setup.sh --help` for the list of supported agents. This installs the
`nfs-utils` skill to the agent's skill directory and the three slash commands
to its command directory.

## Usage

The skill loads automatically when working in an nfs-utils tree.

| Command | Purpose |
|---|---|
| `/nfs-utils-review` | Deep regression analysis of a patch, commit, or range |
| `/nfs-utils-debug` | Debug a daemon failure, crash, or misbehaviour |
| `/nfs-utils-verify` | Check a reported finding against false-positive patterns |

## File Structure

| File | Purpose | When to load |
|---|---|---|
| `technical-patterns.md` | Cross-cutting conventions | **Always, first** |
| `review-core.md` | Review protocol and checklist | Every review |
| `subsystem/subsystem.md` | Trigger table for the guides below | Every review |
| `false-positive-guide.md` | Deliberate idioms that look like bugs | Before reporting anything |
| `debugging.md` | Debugging protocol | Debug sessions |
| `inline-template.md` | `review-inline.txt` format | When writing findings |
| `patch-submission.md` | List, subject, trailers, pre-send checks | Preparing a patch |

### Subsystem guides

| File | Covers |
|---|---|
| `subsystem/sunrpc.md` | libtirpc dual paths, RPC client lifecycle, rpcbind, rpcgen, XDR |
| `subsystem/netlink.md` | nfsdctl, libnl3, YNL uapi header sync, runtime feature detection |
| `subsystem/export.md` | exportfs, mountd, client matching, qword upcalls, `rootdir=` |
| `subsystem/statd.md` | NSM, hostname sanitisation, privilege drop ordering |
| `subsystem/upcalls.md` | gssd, idmapd, nfsdcld, nfsdcltrack, blkmapd |
| `subsystem/mount.md` | The setuid `mount.nfs` helper and its two front ends |
| `subsystem/config.md` | `nfs.conf` and the conffile parser |
| `subsystem/build.md` | The autoconf feature matrix, Python tools, systemd, tests |

## The Short Version

The eight things most likely to produce a wrong review conclusion in this
tree:

1. **`xlog_err()` and `xlog_errno()` never return** — they `exit(1)`. Code
   after them is unreachable, so the "missing NULL check" is not a bug. But a
   new `xlog_err()` on a remote request path kills the daemon.
2. **Two allocation conventions.** `xmalloc`/`xstrdup` abort on OOM and their
   unchecked returns are correct in `mount`/`exportfs`. Plain `malloc` must be
   checked. Introducing the fatal wrappers into a daemon is a regression.
3. **`nfs_freeaddrinfo()`, never `freeaddrinfo()`** — the wrapper exists
   because some implementations fault on NULL.
4. **`nfs_get_rpcclient()` pairs with `CLNT_DESTROY()`** on every exit path.
5. **`-Wimplicit-fallthrough` is not enabled**, and `-Werror=switch` only
   covers enums. A missing `break` in a `switch` over `sa_family_t` compiles
   silently.
6. **Build gating happens at two levels** — `#ifdef` in the `.c` file and
   `if CONFIG_X` in the `Makefile.am`. Cross-component link failures under
   `--disable-X` are the most common real regression.
7. **`daemon_ready()` must be reached on every success path.** Missing it does
   not fail; it hangs.
8. **There is no coding style document.** Match the surrounding file. Do not
   raise style-only findings.

## About nfs-utils

Userland for Linux NFS: `rpc.mountd`, `rpc.statd`, `rpc.gssd`, `rpc.idmapd`,
`nfsdcld`, `nfsdctl`, `exportfs`, `mount.nfs`, and the libraries under
`support/`. It is a collection of independent programs sharing static and
shared libraries, not one binary — whether a given behaviour is a bug often
depends on whether the code is running in a short-lived CLI tool or a
long-running root daemon.

- Mailing list: `linux-nfs@vger.kernel.org`
- Upstream: `git://git.linux-nfs.org/projects/steved/nfs-utils.git`

## Relationship to the Kernel Prompts

Several changes here pair with a kernel change. When the kernel prompt set is
also installed, `../kernel/subsystem/nfsd.md` and
`../kernel/subsystem/sunrpc.md` hold the kernel-side invariants — useful for
`nfsdctl` netlink work and export cache upcalls. These prompts do not depend
on the kernel set being present.

## Contributing

When updating these files:

1. Keep examples concrete, and cite the file they came from.
2. Verify a claim against the tree before writing it down. A confidently wrong
   guideline is worse than a missing one.
3. Add a new deliberate idiom to `false-positive-guide.md` as soon as it
   produces its first bad finding.
4. Keep `technical-patterns.md` short — it is loaded on every invocation.
