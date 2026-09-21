# mount.nfs / umount.nfs

Applies to `utils/mount/`.

## It is setuid root

`utils/mount/Makefile.am` installs it that way:

```make
install-exec-hook:
	(cd $(DESTDIR)$(sbindir) && \
	  ln -sf mount.nfs mount.nfs4 && \
	  ln -sf mount.nfs umount.nfs && \
	  ln -sf mount.nfs umount.nfs4 && \
	  chmod 4711 mount.nfs )
```

One binary, four names, mode 4711. Everything reachable from `main()` before
the privilege check is running with the invoking user's argv and environment,
at euid 0. That makes the following a privilege boundary:

- `argv` — the device string, the mountpoint, and the `-o` option list.
- The environment.
- `/etc/fstab` entries the user is allowed to mount (`user`, `users`).
- The server's replies, once a connection is made.

**Review rules for anything on that path:**

- No `system()`, no `popen()`, no `exec` of a name resolved through `PATH`.
- No format string built from argv.
- Bound every copy out of an option or device string. `parse_opt.c`,
  `parse_dev.c` and `token.c` are the tokenisers — a new option that copies
  into a fixed buffer needs the bound checked at the copy, not at the parse.
- Which operations require root, and is the check before them? A patch that
  moves work earlier can move it in front of the check.
- New file access: is it done with the real uid, or the effective one? Opening
  an arbitrary user-named path at euid 0 is a classic escalation.
- `snprintf()` truncation matters here — a truncated device string that still
  parses can mount something other than what the user asked for. Check the
  return value; `ret >= size` means truncation, and `buf + ret` after a
  truncated write is out of bounds. (A recent fix in this tree,
  `mount: fix snprintf return value handling in error formatting`, was exactly
  this class.)

## Two mutually exclusive implementations

`Makefile.am` picks one:

```make
if CONFIG_LIBMOUNT
mount_nfs_SOURCES += mount_libmount.c
mount_nfs_LDADD   += $(LIBMOUNT)
else
mount_nfs_SOURCES += mount.c fstab.c nfsumount.c fstab.h
endif
```

`--enable-libmount-mount` selects the util-linux `libmount` front end;
otherwise the legacy front end with its own `/etc/mtab` and `fstab` handling
is built. **Both must compile and behave the same.** A change to option
handling or to the mount/umount flow that only touches one front end is
half a patch. The shared code is `mount_common`: `stropts.c`, `network.c`,
`nfsmount.c`, `nfs4mount.c`, `parse_opt.c`, `parse_dev.c`, `token.c`,
`error.c`, `utils.c`.

## `MOUNT_CONFIG` swaps real functions for no-ops

`utils/mount/mount_config.h` provides two versions of the same inline API:

```c
#ifdef MOUNT_CONFIG
static inline void mount_config_init(char *program)
{
	xlog_open(program);
	conf_init_file(MOUNTOPTS_CONFFILE);	/* /etc/nfsmount.conf */
}
static inline char *mount_config_opts(char *spec, char *mount_point, char *mount_opts)
{
	return conf_get_mntopts(spec, mount_point, mount_opts);
}
#else
static inline void mount_config_init(__attribute__((unused)) char *program) { }
static inline char *mount_config_opts(..., char *mount_opts)
{
	return mount_opts;	/* unmodified */
}
#endif
```

`--disable-mountconfig` therefore makes `nfsmount.conf` silently do nothing.
When reviewing an option-defaulting change, check the behaviour under both:
code that assumes `mount_config_opts()` returns a *new* string will leak or
double-free under the no-op branch, where it returns its argument.

`conf_get_mntopts()` merges three `nfsmount.conf` scopes (global, per-server,
per-mountpoint). Precedence between those and the command line is a
user-visible contract — see `config.md` for the parser's own gotchas.

## Protocol negotiation and retry

`stropts.c` drives version and transport negotiation: try NFSv4, fall back,
try TCP, fall back, honour `bg`/`retry`. Points to check:

- A negotiation change must still work against a server that only speaks one
  version, and must not add an unbounded retry loop — `mount -o bg` already
  has a defined backoff.
- `rpc_createerr` is global and is how failures propagate out of the RPC
  helpers. Reading it after a second call has overwritten it produces a
  misleading error message.
- Every `getaddrinfo()` released with `nfs_freeaddrinfo()`; every
  `nfs_get_rpcclient()` matched with `CLNT_DESTROY()`. See `sunrpc.md`.

## Exit codes

`support/include/xcommon.h` defines the `EX_*` values (`EX_USAGE`,
`EX_SYSERR`, `EX_SOFTWARE`, `EX_USER`, `EX_FILEIO`, `EX_FAIL`, `EX_SOMEOK`,
`EX_BG`) and notes they are **ORed together**. Scripts and `mount(8)` itself
depend on these. A new error path must return an existing code with the right
meaning rather than inventing one, and must not return a bare `1`.

## Allocation convention

This is `x*` territory: `xmalloc()`, `xstrdup()`, `xstrconcat*()` abort on OOM
and their returns are deliberately unchecked. That is correct here — see the
false-positive guide. Plain `malloc()` still needs a check.

## Review Checklist

- [ ] New argv/option/device parsing is bounded and does not trust length.
- [ ] Nothing privileged happens before the permission check.
- [ ] `snprintf()` returns checked for truncation before the buffer is used
      or advanced.
- [ ] Change applied to both the `CONFIG_LIBMOUNT` and legacy front ends.
- [ ] Behaviour correct with `MOUNT_CONFIG` both on and off, including who
      owns the returned option string.
- [ ] RPC clients destroyed, addrinfo freed with `nfs_freeaddrinfo()`.
- [ ] Exit code is an existing `EX_*` with the right meaning.
- [ ] Man pages (`nfs.man`, `mount.nfs.man`, `nfsmount.conf.man`) updated for
      any new or changed option.
