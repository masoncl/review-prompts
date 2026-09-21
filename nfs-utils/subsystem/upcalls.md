# Kernel Upcall Daemons: gssd, idmapd, nfsdcld, nfsdcltrack, blkmapd

Applies to `utils/{gssd,idmapd,nfsdcld,nfsdcltrack,blkmapd}/` and
`support/nfsidmap/`.

## Three upcall shapes

The tree uses three different mechanisms, and confusing them produces wrong
review conclusions:

| Shape | Programs | Mechanism |
|---|---|---|
| Long-lived pipefs watcher | `rpc.gssd`, `rpc.svcgssd`, `rpc.idmapd`, `nfsdcld` | `inotify` on a directory under `rpc_pipefs`, driven by a `libevent` loop; read/write the per-client pipe |
| Text "qword" channel | `rpc.mountd`, `exportfs`, `nfsv4.exportd` | `/proc/net/rpc/*/channel` — covered in `export.md`, not here |
| Exec-per-upcall | `nfsdcltrack` | kernel usermode helper, invoked fresh with a subcommand (`init`/`create`/`remove`/`check`/`gracedone`) |

The first shape has a common failure mode: **pipes appear and disappear at
runtime**. An inotify watch that is not re-established after a `rpc_pipefs`
remount, or a client entry not removed on `IN_DELETE`, leaks a watch and an fd
per event. Check that every `IN_CREATE` handler has a matching teardown, and
that the libevent event is `event_del()`ed before the fd is closed — freeing
the fd first leaves a dangling event in the loop.

## gssd / svcgssd

`utils/gssd/`. `rpc.gssd` negotiates RPCSEC_GSS contexts for the client;
`rpc.svcgssd` accepts them on the server. They share `COMMON_SRCS`
(`context*.c`, `gss_util.c`, `gss_oids.c`, `gss_names.c`, `err_util.c`).
Gated by `CONFIG_GSS` (`--disable-gss`) and `CONFIG_SVCGSS`
(`--enable-svcgss`, off by default).

**Mechanism dispatch is a security boundary.** `utils/gssd/context.c` selects a
serialiser by explicit OID comparison before handing a context to the kernel:

```c
if (g_OID_equal(&krb5oid, mech))
	return serialize_krb5_ctx(ctx, buf, endtime);
...
return -1;
```

A new mechanism must be added with its own `g_OID_equal()` test. **A default
or fallthrough branch that serialises an unrecognised mechanism as if it were
Kerberos is a CRITICAL finding** — the kernel would install a context it did
not authenticate.

Other gssd points:

- The context blob handed to the kernel has a fixed wire layout. A field
  added on one side without the other silently misparses. Check the kernel
  side (`../../kernel/subsystem/sunrpc.md`, GSS patterns) when the layout
  changes.
- Credential cache selection (`krb5_util.c`) picks a ccache by uid and by
  file mtime. Changes to that selection change *which* principal a mount
  authenticates as — an authorization change, not a refactor.
- gssd is multi-threaded (one upcall thread per client). Reference counting
  on `struct clnt_info` is the recurring bug source: recent fixes cover a
  missing `pthread_attr_destroy()`, a leaked client on an error path, and a
  missed decrement. On any change to an upcall path, trace the refcount for
  each early return.
- Keytab and credential file handling: check that fds are `O_CLOEXEC` where
  the process forks, and that nothing privileged leaks into a child.

## idmapd and libnfsidmap

`utils/idmapd/idmapd.c` maps NFSv4 `name@domain` strings to uid/gid via
`libnfsidmap`. `utils/nfsidmap/` is the one-shot keyring equivalent.
Gated by `CONFIG_NFSV4`.

`support/nfsidmap/` is the bundled `libnfsidmap`: a core (`libnfsidmap.c`)
plus `dlopen()`ed plugins (`nss.c`, `static.c`, `regex.c`, `umich_ldap.c`
gated by `ENABLE_LDAP`, `gums.c` gated by `ENABLE_GUMS`).

- The plugin ABI is a public interface. A change to the `struct
  trans_func` / plugin entry points breaks out-of-tree plugins; it needs a
  version bump and a note.
- Domain handling: an empty or mismatched NFSv4 domain silently maps
  everything to `nobody`. A patch changing domain derivation should say what
  happens on the mismatch path.
- idmapd runs one child per `rpc_pipefs` client directory. Same
  create/teardown symmetry rules as above.

## nfsdcld and nfsdcltrack

Both persist NFSv4 client identities so the server can enforce a correct grace
period after a reboot. `nfsdcld` is a long-lived pipefs daemon
(`CONFIG_NFSDCLD`, on by default); `nfsdcltrack` is exec'd per upcall
(`CONFIG_NFSDCLTRACK`, off by default). Both are sqlite-backed
(`utils/nfsdcld/sqlite.c`, `utils/nfsdcltrack/sqlite.c`), and `nfsdcld` also
has `legacy.c` for importing the old `v4recovery` directory format.

- **Schema version handling.** The DB outlives the package. A schema change
  needs a version bump plus an upgrade path in the `sqlite.c` init routine,
  and the tool must still open an older DB. A patch that adds a column
  without touching the version is a finding.
- Check `sqlite3_finalize()` on every prepared statement, on error paths too;
  and that transactions are committed or rolled back on every branch.
- The upcall wire format is `support/include/cld.h` and is shared with the
  kernel. It is versioned (`Cld_v2` and later message structs) — a new field
  goes in a new version, never in an existing one.
- `nfsdcltrack` runs as a usermode helper with no controlling terminal;
  diagnostics must go to syslog. It gets no chance to retry, so a transient
  DB lock must be handled inside the single invocation.
- The client identifier stored in the DB is client-supplied opaque data. It is
  used as a blob, not a path — keep it that way.

## blkmapd

`utils/blkmapd/` services pNFS block-layout device discovery
(`CONFIG_BLKMAPD`, off by default, requires NFSv4). It parses device
signatures off disks (`device-inq.c`, `device-process.c`) and drives
`libdevmapper` (`dm-device.c`).

Signature data comes from block devices that may be attacker-controlled in a
multi-tenant SAN. Bounds-check every field read out of a device signature
before using it as a length or an offset.

## Common Review Checklist

- [ ] inotify watch and libevent event torn down in the right order
      (`event_del()` before `close()`), on every client removal path.
- [ ] No fd or watch leak per upcall — trace the failure branches, not the
      success path.
- [ ] gssd: new mechanism has an explicit OID test; no fallthrough default.
- [ ] gssd: refcount balanced on every early return in an upcall thread.
- [ ] sqlite: statements finalised, transactions closed, schema version
      bumped with an upgrade path.
- [ ] Upcall wire structs (`cld.h`, gss context blob) versioned, not extended
      in place.
- [ ] `daemon_ready()` reached on every success path for the long-lived
      daemons.
- [ ] Component is gated — check the `Makefile.am` and that the build still
      works with the feature disabled (`build.md`).
