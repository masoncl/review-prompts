# Export Table, mountd, exportfs

Applies to `utils/{exportfs,mountd,exportd,showmount}/`, `support/export/`,
`support/misc/nfsd_path.c`, `support/nfs/{exports,rmtab,cacheio}.c`.

This is the access-control surface of the NFS server. Most CRITICAL findings
in nfs-utils live here.

## Components

| Program | Role |
|---|---|
| `exportfs` | Parses `/etc/exports` and `/etc/exports.d/*.exports`, maintains `/var/lib/nfs/etab`, pushes exports to the kernel (netlink, or `/proc` fallback) |
| `rpc.mountd` | Serves MOUNT v1/v3, and services kernel export/auth cache upcalls |
| `nfsv4.exportd` | NFSv4-only build: the upcall half of mountd without the MOUNT service (`CONFIG_NFSV4SERVER`) |
| `showmount` | MOUNT protocol client |

`libexport.a` (`support/export/`) is shared by all of them plus `mount.nfs`,
`nfsstat` and `nfs-server-generator`.

## Client matching — the ACL

`support/export/client.c`. `client_gettype()` classifies each client spec in
an exports line into one of four kinds, and each has a different matcher:

| Kind | Example | Matcher |
|---|---|---|
| FQDN | `host.example.com` | name comparison after canonicalisation |
| Subnet | `192.0.2.0/24`, `2001:db8::/32` | `init_netmask4()` / `init_netmask6()` |
| Wildcard | `*.example.com` | `wildmat()` |
| Netgroup | `@trusted` | `innetgr()`, gated by `HAVE_INNETGR` |

**The reverse/forward DNS cross-check is a security control, not a
performance bug.** `check_wildcard()` and `check_netgroup()` resolve the
connecting address to a name and then resolve that name back, confirming the
original address is among the results — `host_reliable_addrinfo()` in
`support/export/hostname.c`. Removing or short-circuiting this to avoid a
lookup reintroduces DNS-spoofing of host-based export ACLs. Flag it as
CRITICAL.

**`wildmat()`** (`support/nfs/wildmat.c`) is the INN glob matcher, and its own
header says:

```
**  Might not be robust in face of malformed patterns; e.g., "foo[a-"
**  could cause a segmentation violation.
```

Patterns come from `/etc/exports` (administrator input), so this is not
remotely reachable today. It becomes a finding the moment a patch feeds
`wildmat()` a pattern from any other source.

**Subnet parsing:** both the `a.b.c.d/m.m.m.m` and `/prefixlen` forms are
accepted. Check new parsing for prefix lengths out of range, and for the
IPv4-mapped-IPv6 case — a mismatch between how a client address and an export
spec are normalised is an ACL bypass.

## Kernel cache upcalls (qword protocol)

`support/nfs/cacheio.c` implements the text encoding used on
`/proc/net/rpc/*/channel`. `support/export/cache.c` implements the handlers:
`auth_unix_ip()`, `auth_unix_gid()`, `nfsd_fh()`, `nfsd_export()` and the
netlink equivalents.

Rules for any new or modified handler:

- `qword_get()` returns the decoded length or `< 0`. **Check it.** Existing
  handlers do (`if (len <= 0) return;`). A handler that ignores the return
  uses an uninitialised buffer.
- Size the destination for the worst case, not the expected case. The existing
  buffers are deliberately conservative: `char class[20]`,
  `char ipaddr[INET6_ADDRSTRLEN + 1]`.
- Reply buffers need slack for the encoding, not just the payload.
  `export_test()` in `support/export/export.c` uses
  `char buf[NFS_MAXPATHLEN + 1 + 64]` — the `+64` is headroom for what
  `qword_add()` appends. **Adding a field to an upcall reply means
  re-deriving that slack.** A patch that adds an attribute without touching
  the buffer size is a finding.
- The content is client-influenced: paths and addresses that a remote client
  chose, relayed by nfsd. Treat it as untrusted even though the immediate
  source is the kernel.
- Every upcall must be answered. A handler that returns without writing a
  reply leaves the kernel request to time out, stalling the client.

The netlink path (`cache_nl_process_export()`, `cache_nl_process_expkey()` and
friends in `cache.c`) is the modern equivalent; see `netlink.md`. Both paths
must stay behaviourally identical, and `nfs.conf` can force the `/proc`
fallback (`no-netlink`), so a change to one usually needs the other.

## `rootdir=` confinement

When `exports { rootdir = /some/path }` is set, nfs-utils does **not**
`chroot()` the whole process. `support/misc/nfsd_path.c` dispatches
path-touching work to a dedicated worker thread that has `chroot()`ed itself
(`nfsd_setup_workqueue()` → `xthread_workqueue_chroot()`), and the callers use
wrappers:

`nfsd_path_stat()`, `nfsd_path_lstat()`, `nfsd_path_statfs()`,
`nfsd_path_read()`, `nfsd_path_write()`, `nfsd_realpath()`,
`nfsd_name_to_handle_at()`, `nfsd_cred_openat()` / `nfsd_openat()`, plus
`nfsd_path_strip_root()` and `nfsd_path_prepend_dir()` for path rewriting.

**Review rule:** new code in `mountd`/`exportd`/`exportfs` that calls
`stat(2)`, `lstat(2)`, `open(2)`, `openat(2)`, `statfs(2)`, `realpath(3)` or
`name_to_handle_at(2)` **directly** silently escapes the confinement. Flag as
CRITICAL when `rootdir=` is a supported configuration for that code path.

`nfsd_cred_openat()` additionally swaps effective uid/gid around the `openat()`
via `nfs_ucred_swap_effective()`. Any new early return inside that window must
restore and free the saved credentials.

## On-disk state

| File | Written by | Notes |
|---|---|---|
| `/var/lib/nfs/etab` | `exportfs` | the authoritative expanded export table; `support/export/xtab.c` |
| `/var/lib/nfs/rmtab` | `rpc.mountd` | MOUNT client list; `support/nfs/rmtab.c` |
| `/var/lib/nfs/v4recovery`, sqlite DBs | see `upcalls.md` | |

These are compatibility surfaces read by other tools and by the previous
version of nfs-utils across an upgrade. A format change needs a migration
path, and a field added to `struct exportent` usually needs the
serialiser, the parser, and the version handling updated together.

Concurrent access is real: `exportfs -a` and a running `rpc.mountd` both touch
`etab`. Check that a new writer takes the same lock the existing writers do
and that partial writes are not observable — the atomic pattern is write to a
temporary and `rename()`.

## Review Checklist

- [ ] New client-spec handling: all four kinds still matched correctly, no
      path that skips the reverse/forward DNS check.
- [ ] `qword_get()` return checked; destination buffers sized for the worst
      case; reply buffer slack re-derived if fields were added.
- [ ] Every upcall path writes a reply, including error paths.
- [ ] No direct `stat`/`open`/`realpath` where a `nfsd_path_*` wrapper exists.
- [ ] netlink and `/proc` fallback paths kept in sync.
- [ ] `etab`/`rmtab` format changes have an upgrade story and keep the
      write-temp-then-`rename` discipline.
- [ ] Memory from `getexportent()`/`getrmtabent()` released on all paths;
      `nfs_freeaddrinfo()` not `freeaddrinfo()`.
- [ ] Changes to `libexport.a` checked against **all** its consumers, not just
      the one the patch is about.
