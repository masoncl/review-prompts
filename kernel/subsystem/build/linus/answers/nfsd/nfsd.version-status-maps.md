- `nfsd_map_status()` in `fs/nfsd/nfsproc.c` differs from `nfsd3_map_status()`:

| Status | NFSv2 result | NFSv3 result |
|---|---|---|
| `nfserr_nofilehandle` | `nfserr_stale` | `nfserr_badhandle` |
| `nfserr_badhandle` | `nfserr_stale` | unchanged |
| `nfserr_xdev` | `nfserr_acces` | unchanged |
| `nfserr_symlink`, `nfserr_wrong_type` | `nfserr_io` | `nfserr_inval` |

- `nfsd_map_status()` and `nfsd3_map_status()` are `static` and are called by
  the procedure itself, on `resp->status`; neither has a caller outside its own
  file, and neither dispatch nor the encoders apply them.
- NFSv4: `nfsd4_map_status()` in `fs/nfsd/nfs4xdr.c`, a switch on the status
  with the minor version as argument; there is no per-minor table.
- `nfsd4_map_status()` has one call site, at the `status:` label of
  `nfsd4_encode_operation()`, and it overwrites `op->status`.
- COMPOUND status: `nfsd4_proc_compound()` copies it from `op->status` after
  `nfsd4_encode_operation()` returns, so it is already mapped.
- `nfserr_wrong_type` is a protocol value, `cpu_to_be32(NFS4ERR_WRONG_TYPE)`;
  `nfsd4_map_status()` changes it to `nfserr_inval` for minor version 0 only.
- Dropping a reply: NFSD procedures return `rpc_success` and set `RQ_DROPME`,
  as `nfsd_proc_read()` does on `nfserr_jukebox`.
- `rpc_drop_reply` is not used in `fs/nfsd`; after `pc_func` returns,
  `nfsd_dispatch()` tests only `RQ_DROPME`.
