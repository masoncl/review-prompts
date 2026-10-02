- This tree signs file handles.
- Enabled per export by `NFSEXP_SIGN_FH` (`sign_fh` in `expflags[]`), plus a
  per-net key in `fh_key` of `struct nfsd_net`.
- Key: 16 bytes in netlink attribute `NFSD_A_SERVER_FH_KEY`, stored by
  `nfsd_nl_fh_key_set()`; `nfsd_nl_threads_set_doit()` returns `-EBUSY` if
  threads are running. Nothing else sets it.
- MAC: 8-byte little-endian SipHash of all handle bytes before it, appended
  by `fh_append_mac()`.
- Signing sites: `_fh_update()`, reached from `fh_compose()` and
  `fh_update()`, and `setup_notify_fhandle()` in `fs/nfsd/nfs4xdr.c`.
- Check: `fh_verify_mac()` in `nfsd_set_fh_dentry()`, after the export lookup
  and credential setup, before `exportfs_decode_fh_raw()`, which is given the
  length without the MAC.
- Exempt: handles with `fh_fileid_type` `FILEID_ROOT`, in both directions,
  and handles of exports without the flag.
- The flag is read from `ex_flags`; it is not in `NFSEXP_SECINFO_FLAGS`, so it
  cannot vary by flavor.
- No key, or no room below `fh_maxsize`: `fh_append_mac()` fails,
  `_fh_update()` sets `FILEID_INVALID`, and `fh_compose()` or `fh_update()`
  returns `nfserr_stale`.
- No key at verification: every signed handle fails.
