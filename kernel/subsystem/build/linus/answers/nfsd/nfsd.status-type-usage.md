- **Potentially unsafe usage**: passing the return value of a VFS call
  straight to `nfserrno()`.
  - Unsafe: when the callee can return an errno with no entry in `nfs_errtbl`,
    for example `-ENODATA` or `-ERANGE`; `nfserrno()` warns once and the client
    gets `nfserr_io`.
  - Safe: when those values are translated first, as `nfsd_xattr_errno()` in
    `fs/nfsd/vfs.c` does before it falls back to `nfserrno()`.
- **Unsafe usage**: returning an NFS status from a `pc_func`.
  - Unsafe: sparse does not flag it, because the RPC accept status is `__be32`
    too; `svc_process_common()` then truncates the reply and sends the value as
    the accept status.
  - Safe: store the status in `resp->status` and return `rpc_success`, as
    `nfsd3_proc_getattr()` does.
  - Safe: for NFSv4, store it in `cstate->status`, as `nfsd4_proc_compound()`
    does.
- Internal status codes: `nfserr_eof`, `nfserr_replay_me`,
  `nfserr_replay_cache` and `nfserr_symlink_not_dir`, in the enum that starts
  at `NFSERR_EOF` in `fs/nfsd/nfsd.h`; there is no nfserr_dropit.
- Code that keeps an `int host_err` apart from the `__be32` status and
  converts once with `nfserrno()`: `nfsd_lookup_dentry()`, `nfsd_setattr()`,
  `nfsd_create_locked()` and `nfsd_vfs_write()` in `fs/nfsd/vfs.c`.
- `nfsd_lookup()` holds only a `__be32`.
- `nfserrno(-EINVAL)` on a constant: see `nfsd4_clone_file_range()`;
  `nfsd_setattr()` has no such call.
