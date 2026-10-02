- `s2s_cp_stateids` in `struct nfsd_net`: holds only copy-notify stateids,
  `struct nfs4_cpntf_state`; its `copy_stateid_t` is not a
  `struct nfs4_stid`.
- `sc_cp_list`: a list head in the parent stid for its copy-notify states
  (linked through `cp_list`), not a list the stid sits on.
- `find_stateid_locked()`: matches `si_opaque.so_id` only; the clientid half,
  `so_clid`, is compared by `set_client()` in `nfsd4_lookup_stateid()`.
- Type names: `SC_TYPE_COPY` is a fifth bit beside the four known ones;
  `NFS4_COPYNOTIFY_STID` is still the `cs_type` of a `copy_stateid_t`.
