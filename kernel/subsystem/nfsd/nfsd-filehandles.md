# NFSD File Handle Lifecycle

Using a file handle before `fh_verify()` completes, or failing to call
`fh_put()` on all exit paths, causes permission bypasses (accessing
dentries without access checks), use-after-free (dentry/export
references not released), or NULL dereferences (accessing `fh_dentry`
before it is set).

## struct svc_fh Fields

The `struct svc_fh` (defined in `fs/nfsd/nfsfh.h`) contains:

- `fh_handle` — the on-wire NFS file handle data (`struct knfsd_fh`).
- `fh_dentry` — the validated dentry, set by `nfsd_set_fh_dentry()`
  during `fh_verify()`. NULL until verification succeeds.
- `fh_export` — the export entry, also set during `fh_verify()`.
- `fh_maxsize` — maximum handle size, set at initialization.

## Initialization

File handles must be zero-initialized before use. Two patterns:

- `fh_init(fhp, maxsize)` — calls `memset(fhp, 0, sizeof(*fhp))` and
  sets `fh_maxsize`. Used when allocating response file handles; see
  `fs/nfsd/nfsfh.h`.
- `fh_copy(dst, src)` — copies the raw handle data from `src` to `dst`.
  Asserts with `WARN_ON(src->fh_dentry)` — the source must not have
  been verified yet (no dentry reference to duplicate).

## Verification

`fh_verify(rqstp, fhp, type, access)` in `fs/nfsd/nfsfh.c` performs:

1. If `fh_dentry` is NULL, calls `nfsd_set_fh_dentry()` to look up the
   dentry from the wire handle and set `fh_dentry` and `fh_export`.
2. Validates the file type matches `type` (e.g., `S_IFDIR`, `S_IFREG`,
   or `0` for any).
3. Checks access permissions using the `access` flags.

Access flags are defined in `fs/nfsd/vfs.h`:

| Flag | Meaning |
|------|---------|
| `NFSD_MAY_NOP` | No permission check |
| `NFSD_MAY_EXEC` | Execute/search permission |
| `NFSD_MAY_WRITE` | Write permission |
| `NFSD_MAY_READ` | Read permission |
| `NFSD_MAY_SATTR` | Set attributes |
| `NFSD_MAY_TRUNC` | Truncate |
| `NFSD_MAY_CREATE` | `EXEC|WRITE` — create in directory |
| `NFSD_MAY_REMOVE` | `EXEC|WRITE|TRUNC` — remove from directory |
| `NFSD_MAY_OWNER_OVERRIDE` | Allow owner to bypass checks |
| `NFSD_MAY_BYPASS_GSS` | Skip GSS requirement |

**REPORT as bugs**: Code that accesses `fh_dentry`, `fh_export`, or
the inode through a file handle that has not been verified with
`fh_verify()` or where `fh_verify()` return value is not checked.

## Cleanup

`fh_put(fhp)` in `fs/nfsd/nfsfh.c` releases all resources:

- Calls `dput()` on `fh_dentry` and sets it to NULL.
- Calls `exp_put()` on `fh_export` and sets it to NULL.
- Calls `fh_drop_write()` if write access was taken.

`fh_put()` is safe to call on an unverified handle (it checks for
NULL dentry/export before releasing).

**REPORT as bugs**: Exit paths (including error paths) that skip
`fh_put()` for a file handle that was verified or had `fh_compose()`
called on it.

## Quick Checks

- **fh_copy source state**: `fh_copy()` warns if `src->fh_dentry` is
  set — do not copy an already-verified handle.
- **Type parameter correctness**: verify that `fh_verify()` type
  argument matches the operation (e.g., `S_IFDIR` for directory
  operations, `S_IFREG` for file I/O, `0` when any type is valid).
- **Access flag completeness**: verify the access flags include all
  needed permissions for the operation, not just the minimum.
