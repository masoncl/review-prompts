# nfs-utils False Positive Guide

Several correct, deliberate idioms in this tree look like bugs. Check here
before reporting. Each entry says what the pattern looks like, why it is
correct, and what a *real* violation of the same rule looks like.

## 1. `xlog_err()` never returns

`xlog_err()` and `xlog_errno()` call `xlog_backend(L_FATAL, ...)`, which ends
with `exit(1)`. Code after them is unreachable.

```c
/* NOT A BUG - utils/statd/statd.c, create_pidfile() */
fp = fopen(pidfile, "w");
if (!fp)
	xlog_err("Opening %s failed: %m", pidfile);
fprintf(fp, "%d\n", getpid());	/* unreachable if fp == NULL */
```

Do not report the `fprintf()` as a NULL dereference, and do not "fix" it by
adding a `return`. There are many instances of this shape across the daemons.

**A real finding**, however:

- A patch changes `xlog_err()` to `xlog_warn()` and leaves the following code
  unguarded — now it really can run with `fp == NULL`. Flag that.
- A patch adds `xlog_err()` to a path that handles a *remote request* in a
  long-running daemon. The daemon now exits on attacker-triggerable input.
  Flag that as HIGH or CRITICAL.

## 2. Unchecked `xmalloc()` / `xstrdup()`

```c
/* NOT A BUG - support/export/export.c */
exp->m_export.e_hostname = xstrdup(hname);
```

`xmalloc`, `xrealloc`, `xstrdup`, `xstrndup`, `xstrconcat*` (declared in
`support/include/xcommon.h`) abort on allocation failure. Callers deliberately
do not check.

**This is not confined to the CLI tools.** The convention arrived with the
util-linux-derived `mount.nfs` code, but `support/export/export.c`,
`utils/mountd/mountd.c`, `utils/statd/statd.c` and `utils/statd/notlist.c`
all use it too, and `libexport.a` carries it into everything that links it.
An unchecked `x*` call in a long-running daemon is therefore *not* evidence of
a bug — it is decades-old house style, grandfathered by rule #9.

**A real finding:** a **newly added** fatal allocation on a daemon's
per-request path, where a remote peer controls the size or the rate. Aborting
`rpc.mountd` on OOM is a denial of service. Report the specific new call site
and the input that reaches it — do not report the idiom itself.

Plain `malloc`/`calloc`/`strdup` **must** be checked. Do not confuse the two.

## 3. `strncpy` followed by a forced NUL

```c
/* NOT A BUG - the tree's standard idiom */
strncpy(sock->name, nla_data(a), MAX_CLASS_NAME_LEN);
sock->name[MAX_CLASS_NAME_LEN - 1] = '\0';
```

Correct. Do not report the classic "strncpy may not NUL-terminate" finding
when the termination is right there.

**A real finding:** `strncpy()` with no following termination and no evidence
the destination was zeroed; or a copy whose *length bound* comes from the
destination size when the source length is separately known and unvalidated
(see #4).

## 4. `strncpy` into a pre-zeroed buffer

```c
/* NOT A BUG - support/export/hostname.c, host_ntop() */
memset(buf, 0, buflen);
...
strncpy(buf, "bad family", buflen - 1);
```

Safe, because of the `memset`. Do not report it.

**A real finding:** the same idiom copy-pasted onto a buffer that was *not*
zeroed first. Check for the `memset`.

## 5. Generated code

Do not review these as hand-written source:

- rpcgen output: `support/nsm/sm_inter_{clnt,svc,xdr}.c`,
  `support/export/mount_{clnt,xdr}.c`, `tests/nsm_client/nlm_sm_inter_*.c`.
  Odd prototypes, unchecked `xdr_*` idioms, and non-conforming style are
  artifacts of the generator.
- YNL uapi headers: `support/include/{nfsd,lockd,sunrpc}_netlink.h`. These
  carry a `Do not edit directly, auto-generated from:` banner.

**A real finding:** a *hand edit* to any of the above. A generated file must be
regenerated, never patched in place. For the netlink headers see
`subsystem/netlink.md`; for rpcgen output, the `.x` file is the source.

## 6. `UNUSED()` parameters in conditional stubs

```c
/* NOT A BUG - support/export/client.c, the !IPV6_SUPPORTED variant */
static void init_netmask6(nfs_client *UNUSED(clp), const char *slash)
```

`UNUSED(x)` (`support/include/nfslib.h`) applies
`__attribute__((unused))` and renames the parameter so accidental use will not
compile. This is the required form for `#ifdef`-selected stubs, not dead code.

## 7. Duplicated `socklen_t` compatibility shim

```c
#if SIZEOF_SOCKLEN_T - 0 == 0
#define socklen_t int
#endif
```

This appears independently in `support/include/sockaddr.h`,
`support/nfs/rpcmisc.c`, `utils/statd/rmtcall.c` and elsewhere. The
duplication is intentional — each translation unit needs it before including
system headers. Do not report it as copy-paste.

**A real finding:** a fix applied to one copy but not the others.

## 8. Dual `#ifdef HAVE_LIBTIRPC` implementations

Large blocks of near-duplicate RPC code under `#ifdef HAVE_LIBTIRPC` / `#else`
(e.g. `support/nfs/rpc_socket.c`, `support/nfs/getport.c`) are not redundancy
to be refactored away. Both branches must exist and must build.

**A real finding:** new RPC code added to only one branch, so the other stops
compiling or silently loses the feature.

## 9. Legacy code is grandfathered

Only judge idiom compliance against added lines. In a unified diff, that means
lines with a `+` prefix.

```c
/* DO NOT flag - unchanged context */
 	freeaddrinfo(ai);

/* FLAG - newly added */
+	freeaddrinfo(ai);	/* should be nfs_freeaddrinfo() */
```

The same applies to plain `malloc` without a check, hand-rolled `strncpy`, and
missing `nfsd_path_*` wrappers: existing instances are known debt.

**The exception that matters most.** Grandfathering covers the *idiom*, not
its consequences. When an added line is harmless in isolation but produces
new, concrete breakage by executing through a pre-existing defect on unchanged
lines, that **is** a finding — the new line is the proximate cause of new
behaviour, and the patch is the right place to fix it.

Typical shape: a new condition is ORed into a `switch` arm that a
grandfathered missing `break` already falls into, so the new condition now
also governs the preceding case. The fallthrough is old; the wrong answer is
new. Report it, attribute it accurately ("pre-existing fallthrough, made
deterministic by this patch"), and suggest the `break`.

Do not use grandfathering to wave away a real regression just because the
defective line has no `+`.

## 10. Warnings the build already rejects

`configure.ac` enables `-Werror=` for missing prototypes, missing declarations,
`format=2`, `undef`, `implicit-function-declaration`, `return-type`, `switch`,
`overflow`, `parentheses`, `aggregate-return`, `unused-result`, and (when
supported) `format-overflow=2`, `int-conversion`,
`incompatible-pointer-types`, `misleading-indentation`.

Do not report a defect in any of those classes — the patch would not have
compiled. In particular, do not report "return value of `write()` ignored"
when the code casts to `(void)` or assigns, since `-Werror=unused-result`
already forces the issue.

**The important exception:** `-Wimplicit-fallthrough` is **not** enabled, and
`-Werror=switch` only covers unhandled *enum* values. A missing `break` in a
`switch` over `sa_family_t`, an `int`, or a `char` compiles silently and **is**
a real finding.

## 11. `exit(1)` in a one-shot tool

`exportfs`, `mount.nfs`, `showmount`, `nfsdcltrack`, `sm-notify` and the other
short-lived programs legitimately `exit()` on error rather than unwinding.
Do not report "should propagate the error to the caller" for these.

Long-running daemons are the opposite case — see #1.

## 12. `nfsd_path_*` wrappers look like pointless indirection

`nfsd_path_stat()`, `nfsd_path_lstat()`, `nfsd_path_read()`,
`nfsd_cred_openat()` and friends (`support/misc/nfsd_path.c`) dispatch to a
dedicated `chroot()`ed worker thread when `exports { rootdir = }` is
configured. They are not wrappers to be inlined away.

**A real finding:** new path-touching code in `mountd`/`exportfs` calling
`stat(2)`/`open(2)` directly — that silently bypasses the confinement.

## Verification Checklist

Before reporting, confirm all of:

- [ ] The path is reachable — you traced it, you did not infer it.
- [ ] The code is compiled in a default configuration (checked the
      `Makefile.am`, not only the `#ifdef`s).
- [ ] It is not generated code.
- [ ] The line is added by this patch, not pre-existing context.
- [ ] It is not one of the twelve patterns above.
- [ ] The build would not already have rejected it.
- [ ] You can state a concrete input or sequence that produces the wrong
      outcome.

If you cannot state the concrete failure, you do not have a finding.
