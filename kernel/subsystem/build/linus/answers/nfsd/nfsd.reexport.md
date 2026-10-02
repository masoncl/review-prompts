- `nfs_export_ops` in `fs/nfs/export.c` sets `EXPORT_OP_NOWCC`,
  `EXPORT_OP_NOSUBTREECHK`, `EXPORT_OP_CLOSE_BEFORE_UNLINK`,
  `EXPORT_OP_REMOTE_FS`, `EXPORT_OP_NOATOMIC_ATTR`,
  `EXPORT_OP_FLUSH_ON_CLOSE` and `EXPORT_OP_NOLOCKS`.
- There is no EXPORT_OP_ASYNC_LOCK here.
- Tests that are easy to miss:

| Flag | Tested in |
|---|---|
| `EXPORT_OP_REMOTE_FS` | `nfsd_vfs_write()`: no `PF_LOCAL_THROTTLE` |
| `EXPORT_OP_CLOSE_BEFORE_UNLINK` | `nfsd_unlink()` and `nfsd_rename()` |
| `EXPORT_OP_FLUSH_ON_CLOSE` | `nfsd_file_check_writeback()` |
| `EXPORT_OP_NOSUBTREECHK` | `check_export()`: `-EINVAL` without `NFSEXP_NOSUBTREECHECK` |
| `EXPORT_OP_NOLOCKS` | through `exportfs_cannot_lock()` |

- `exportfs_cannot_lock()`: `nfsd4_lock()` and `nfsd4_locku()` return
  `nfserr_notsupp`; `nfs4_set_delegation()` returns `-EOPNOTSUPP`; lockd
  tests it through `nlmsvc_file_cannot_lock()`. `nlm_fopen()` does not.
- fsid: `check_export()` returns `-EINVAL` unless the filesystem has
  `FS_REQUIRES_DEV`, or the export has `NFSEXP_FSID` or a uuid; `nfs_fs_type`
  and `nfs4_fs_type` lack `FS_REQUIRES_DEV`.
- `Documentation/filesystems/nfs/reexport.rst` lists exactly four
  limitations:
  - `fsid=` is required and `crossmnt` does not propagate it; each NFS mount
    below needs its own export and `fsid=`.
  - Reboot recovery does not work; clients cannot get locks or delegations at
    all, attempts fail with operation not supported.
  - Handle size: an X-byte original handle becomes X+22 bytes rounded up to a
    multiple of four, and must fit 32, 64 or 128 bytes.
  - OPEN deny bits are not passed to the original server.
- The document does not list WCC, cache coherency or unlink of open files.
