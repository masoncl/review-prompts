- `struct nfsd4_async_copy` (`fs/nfsd/xdr4.h`): the async copy object; it
  embeds `cp_stid` (`struct nfs4_stid`) and `cp_copy` (`struct nfsd4_copy`,
  a snapshot of the request and the result).
- `refcount`, `copy_task`, `copies`, `cp_ttl`, `cp_cb_offload`: fields of
  `struct nfsd4_async_copy`, not of `struct nfsd4_copy`.
- `nfs4_alloc_copy_stid()` in `fs/nfsd/nfs4state.c`: allocates the whole
  object from `async_copy_slab` through `nfs4_alloc_stid()`; it is freed by
  the `sc_free` hook `nfsd4_free_async_copy_stid()`, not by `kfree()`.
- Stateid kind: an ordinary `struct nfs4_stid` with `sc_type` set to
  `SC_TYPE_COPY`; the value sent to the client is `cp_stid.sc_stateid`.
- `so_clid` of that stateid: the client's own `cl_clientid`;
  `si_generation` is fixed at 1.
- Not in this tree: NFS4_COPY_STID, nfs4_init_copy_state(),
  nfs4_free_copy_state(); `struct nfsd4_copy` has no `cp_stateid` field.
- `copy_stateid_t` and `nn->s2s_cp_stateids`: used only for COPY_NOTIFY
  (`struct nfs4_cpntf_state`, `NFS4_COPYNOTIFY_STID`); a copy offload
  stateid is never in that idr.
- Registered in: the client's `cl_stateids` idr, by `nfs4_alloc_stid()`,
  before the cap check and before the kthread exists.
- `find_stateid_locked()`: finds the entry and returns NULL because
  `sc_type == SC_TYPE_COPY`; no clientid comparison is involved.
- TEST_STATEID: `nfsd4_validate_stateid()` returns `nfserr_bad_stateid`,
  which `nfsd4_test_stateid()` stores in `ts_id_status`; the operation
  itself returns `nfs_ok`.
- FREE_STATEID: `nfsd4_free_stateid()` returns `nfserr_bad_stateid`.
- `container_of()` from `cp_stid` to the copy: the supported way to get the
  copy from its stateid, as in `nfsd4_free_async_copy_stid()`.
- **Potentially unsafe usage**: walking `cl_stateids` directly instead of
  going through `find_stateid_locked()`.
  - Unsafe: dereferencing `sc_file` or `sc_export` of an entry before testing
    `sc_type`; both are NULL in a `SC_TYPE_COPY` entry.
  - Safe: test `sc_type` against a mask without `SC_TYPE_COPY` first, as
    `find_one_sb_stid()` does with the mask from `nfsd4_revoke_states()`.
