- Async copies, superblock path: `nfsd4_cancel_copy_by_sb()` in
  `fs/nfsd/nfs4proc.c` runs before `nfsd4_revoke_states()`. It matches on
  `nf_src` or `nf_dst`, stops the kthread and puts both files.
- A cancelled copy that was still running: its CB_OFFLOAD is still sent, with
  `nfserr_admin_revoked`. `cp_clp` is left set for that reason.
- Async copies, export path: `nfsd_nl_unlock_export_doit()` cancels none.
- Cached files, superblock path: no file-cache purge. Only the references
  that the revoked state and the cancelled copies hold are put.
- Cached files, export path: `nfsd_file_close_export()` in
  `fs/nfsd/filecache.c` runs before the revoke. It closes `NFSD_FILE_GC`
  entries on the same superblock and under the export's dentry.
- `drop_stid_export()`: revocation also puts `sc_export`, so the export is
  not pinned until the stateid is freed.
- NFSv4.0, on next use: `nfsd40_drop_revoked_stid()` frees the stateid as
  `nfserr_admin_revoked` is returned. The next use gets `nfserr_bad_stateid`.
- NFSv4.0, never used again: `nfs40_clean_admin_revoked()` runs from
  `nfs4_laundromat()` one lease period after `nn->nfs40_last_revoke`.
- `cl_admin_revoked`: decremented by the last put, in `nfs4_put_stid()` or
  `put_ol_stateid_locked()`, not by `nfs40_clean_admin_revoked()`.
