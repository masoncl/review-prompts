# Build System, Packaging, and Tests

Applies to `configure.ac`, every `Makefile.am`, `aclocal/`, `systemd/`,
`tools/*/*.py`, `tests/`.

nfs-utils has a large optional-feature matrix. "Does this compile?" is not the
same question as "does this compile in the configuration the patch author
used", and build breakage under a non-default combination is a recurring
regression class in this tree.

## Two levels of gating

**Level 1 — `Makefile.am`.** Whole directories and whole source files are
selected by `AM_CONDITIONAL` variables. This is invisible from the `.c` file:

```make
if CONFIG_LIBMOUNT
mount_nfs_SOURCES += mount_libmount.c
else
mount_nfs_SOURCES += mount.c fstab.c nfsumount.c
endif
```

**Level 2 — `config.h`.** `AC_DEFINE`d macros drive `#ifdef` inside the code.
Every file opens with:

```c
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
```

**When reviewing, read both.** A guard that looks missing in the `.c` file may
be handled by the `Makefile.am` excluding the file entirely, and vice versa.

## The matrix

| Option | `AM_CONDITIONAL` | `config.h` macro | Gates |
|---|---|---|---|
| `--disable-nfsv4` | `CONFIG_NFSV4` | — | `idmapd`, `nfsidmap`; also forces nfsdcld/nfsdcltrack off |
| `--disable-gss` | `CONFIG_GSS` | — | `utils/gssd` |
| `--enable-svcgss` (default no) | `CONFIG_SVCGSS` | — | `svcgssd` within `utils/gssd` |
| `--enable-blkmapd` (default no) | `CONFIG_BLKMAPD` | — | `utils/blkmapd`; needs NFSv4 |
| `--disable-nfsdcld` | `CONFIG_NFSDCLD` | — | `utils/nfsdcld`, `tools/nfsdclddb` |
| `--enable-nfsdcltrack` (default no) | `CONFIG_NFSDCLTRACK` | — | `utils/nfsdcltrack` |
| `--disable-nfsdctl` | `CONFIG_NFSDCTL` | `HAVE_NFSD_NETLINK` | `utils/nfsdctl`; also requires readline |
| `--enable-nfsv4server` (default no) | `CONFIG_NFSV4SERVER` | `HAVE_NFSV4SERVER_SUPPORT` | `utils/exportd`, the `nfsv4-*` units |
| `--disable-mount` | `CONFIG_MOUNT` | — | `mount.nfs` built at all |
| `--enable-libmount-mount` | `CONFIG_LIBMOUNT` | — | which `mount.nfs` front end |
| `--disable-mountconfig` | `MOUNT_CONFIG` | `MOUNT_CONFIG`, `MOUNTOPTS_CONFFILE` | real vs no-op `nfsmount.conf` inlines |
| `--enable-junction` (default yes) | `CONFIG_JUNCTION` | `HAVE_JUNCTION_SUPPORT` | `support/junction`, `nfsref`, mountd/exportd `OPTLIBS` |
| `--disable-ipv6` | `CONFIG_IPV6` | `IPV6_SUPPORTED` | `AF_INET6` code throughout |
| `--enable-tirpc` (default yes) | — (`AC_LIBTIRPC`) | `HAVE_LIBTIRPC` | TI-RPC vs legacy RPC branches |
| `--disable-nfsrahead` | `CONFIG_NFSRAHEAD` | — | `tools/nfsrahead`; pulls in libmount |
| `--with-systemd[=dir]` | `INSTALL_SYSTEMD` | — | the three generators and all unit files |
| `--disable-sbin-override` | `CONFIG_SBIN_OVERRIDE` | — | forcing `/sbin` for `mount.nfs`, `nfsdcltrack` |
| `--disable-ldap` | `ENABLE_LDAP`, `ENABLE_LDAP_SASL` | same names | `umich_ldap.c` idmap plugin |
| `--enable-gums` | `ENABLE_GUMS` | `ENABLE_GUMS` | `gums.c` idmap plugin |
| `--with-rpcgen=internal` | `CONFIG_RPCGEN` | — | bundled `tools/rpcgen` vs system |
| libblkid detection | — | `USE_BLKID` | UUID support in exportfs/mountd |

Plus the usual `AC_CHECK_FUNCS`/`AC_CHECK_HEADERS` results: `HAVE_INNETGR`,
`HAVE_GETNAMEINFO`, `HAVE_SYS_CAPABILITY_H`, `HAVE_NAME_TO_HANDLE_AT`,
`HAVE_GETRPCBYNAME`, `HAVE_TCP_WRAPPER`, `HAVE_LIBPTHREAD`, `HAVE_UNSHARE`,
`HAVE_FUNC_ATTRIBUTE_FORMAT`, `SIZEOF_SOCKLEN_T`.

## The recurring breakage

A symbol defined in a gated component, referenced from an ungated one. The
default build links fine; `--disable-X` fails at link time. Real example:
`exportfs: link failure with --disable-nfsdctl`.

**Review rule:** when a patch adds a call across a component boundary, check
that either the callee is unconditional, or the call site is guarded *and* the
`Makefile.am` link line matches. `HAVE_NFSD_NETLINK` and `CONFIG_JUNCTION` are
the two that bite most often.

The same applies to `#else` stubs. Every `#ifdef HAVE_X` needs one that
compiles and returns a real failure — the pattern is `errno = ENOSYS;
return -1;`, as in `nfsd_name_to_handle_at()` (`support/misc/nfsd_path.c`). A
stub that returns success is worse than no stub. Unused parameters in stubs
use the `UNUSED()` macro from `nfslib.h`.

## Warning flags

`configure.ac` builds `AM_CFLAGS` from `-Wall -Wextra` plus a long list of
`-Werror=` promotions: `missing-prototypes`, `missing-declarations`,
`format=2`, `undef`, `missing-include-dirs`, `strict-aliasing=2`, `init-self`,
`implicit-function-declaration`, `return-type`, `switch`, `overflow`,
`parentheses`, `aggregate-return`, `unused-result`; and, when the compiler
supports them (`CHECK_CCSUPPORT`), `format-overflow=2`, `int-conversion`,
`incompatible-pointer-types`, `misleading-indentation`.

Two consequences already noted in `../technical-patterns.md` and
`../false-positive-guide.md`, repeated because they matter here:

- Do not report defects in those classes — the patch would not have built.
- `-Wimplicit-fallthrough` is **not** in the list, and `-Werror=switch` only
  covers unhandled enum values. Missing `break` compiles silently.

A patch that adds a new warning flag should say what it found, and must not
break the build for older compilers — use `CHECK_CCSUPPORT` for anything not
universally available.

## Autoconf hygiene

- A new source file must be added to the right `_SOURCES` in `Makefile.am`, or
  it is silently not compiled while `make` still succeeds.
- A new header must be in `noinst_HEADERS` or a `_SOURCES` list, or `make dist`
  produces a tarball that does not build.
- A new library dependency needs `PKG_CHECK_MODULES` (or an `AC_CHECK_LIB`)
  and the resulting `_LDADD`, not just an `#include`.
- Generated files (`configure`, `Makefile.in`, `aclocal.m4`, `config.guess`)
  are in `.gitignore` and must not appear in a patch.

## Python tools

`tools/rpcctl/rpcctl.py`, `tools/nfsdclnts/nfsdclnts.py`,
`tools/nfsdclddb/nfsdclddb.py`, `tools/mountstats/mountstats.py`,
`tools/nfs-iostat/nfs-iostat.py`.

These are installed verbatim by an `install-data-hook` that copies and
`chmod 755`s. There is no automake `PYTHON` primary, **no interpreter-line
substitution, and no byte-compilation**. So:

- The shebang is whatever is in the file. It must be `#!/usr/bin/env python3`
  or an absolute `python3`, never bare `python`.
- Third-party imports (`yaml`, `multiprocessing`) become runtime dependencies
  that the build cannot check. A new import needs a packaging note.
- Syntax and deprecation problems are only found by running the tool. Recent
  example: `rpcctl: SyntaxWarning: 'return' in a 'finally' block`. Ask whether
  the patch was actually executed.
- These parse kernel-exported text (`/proc/self/mountstats`,
  `/sys/kernel/sunrpc`). That format is not stable — parsing must degrade on
  an unrecognised line rather than raise.

## systemd integration

`systemd/` holds the unit files and three **generators**:
`nfs-server-generator.c`, `rpc-pipefs-generator.c`, `nfsroot-generator.c`,
sharing `systemd.c`/`systemd.h` for unit-name escaping. All of it is gated by
`INSTALL_SYSTEMD` (`--with-systemd`).

Generators run at early boot, as root, before most of userspace exists.
Review them with the same care as setuid code: no assumptions about available
services, no blocking on the network, correct escaping of anything that
becomes a unit name, and a clean exit when the inputs are absent.

Unit dependency changes are behavioural. Adding a `Requires=` or reordering
`After=` can deadlock boot or start a daemon before its state directory is
mounted. The dependency reasoning is documented in the top-level `README`,
section 3 — check a change against it.

## Tests

`tests/` is a thin shell harness, not a unit-test framework. Do not expect a
patch to come with unit tests; there is nowhere to put them.

- `tests/Makefile.am`: `TESTS = t0001-statd-basic-mon-unmon.sh`, and
  `check_PROGRAMS = statdb_dump` (a helper that dumps statd's on-disk records,
  linking `libnfs.a`, `libnsm.a`, `libmisc.a`).
- `tests/test-lib.sh`: shared helpers (`check_root`, `check_dev_log`,
  `start_statd`, `kill_statd`). Tests `exit 77` to signal *skipped*, the
  automake convention — a test that cannot run must skip, not fail.
- `tests/t0001-statd-basic-mon-unmon.sh` starts a real `rpc.statd --no-notify`,
  drives it with the `tests/nsm_client/` helper, and verifies on-disk state.
  Requires root.
- `tests/t0002-nfsconf.sh` plus `tests/nfsconf/*.conf`/`*.exp` is a golden-file
  parser test that is **not** listed in `TESTS` and references a `nfsconftool`
  binary that `tools/nfsconf/Makefile.am` does not build (it builds `nfsconf`
  from `nfsconfcli.c`). Treat it as orphaned; do not cite it as coverage.

If a patch adds a test, check it is added to `TESTS`, skips cleanly without
root, and cleans up after itself.

## Review Checklist

- [ ] New file in `_SOURCES`; new header distributed; new library in
      `PKG_CHECK_MODULES` and `_LDADD`.
- [ ] Cross-component references guarded, and the `Makefile.am` agrees.
- [ ] Builds with the relevant `--enable`/`--disable` inverted — at minimum
      `--disable-nfsdctl`, and `--disable-gss --disable-nfsv4` for anything
      near those components.
- [ ] Every new `#ifdef HAVE_X` has an `#else` stub that fails cleanly, with
      `UNUSED()` parameters.
- [ ] No generated file in the diff.
- [ ] Python changes: shebang, new imports declared, tool actually run.
- [ ] systemd unit or generator changes checked against the startup-ordering
      rules in the top-level `README`.
- [ ] New test wired into `TESTS` and skipping with `exit 77` when it cannot
      run.
