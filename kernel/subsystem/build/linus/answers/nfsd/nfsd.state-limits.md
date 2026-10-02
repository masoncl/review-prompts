| Object | Bound | Counter | At the bound |
|---|---|---|---|
| Clients | `nn->nfs4_max_clients` | `nn->nfs4_client_count` | no error; see below |
| Delegations | `max_delegations` | `num_delegations` | no delegation granted |
| Running async copies | `sp_nrthreads` of the request's pool | `nn->pending_async_copies` | `nfserr_jukebox` |
| Slots per session | `NFSD_MAX_SLOTS_PER_SESSION` | `se_fchannel.maxreqs` | fewer slots granted |
| Ops per compound, v4.0 | `NFSD_MAX_OPS_PER_COMPOUND` | none | `nfserr_resource` |
| Ops per compound, sessions | `se_fchannel.maxops` | none | `nfserr_too_many_ops` |

- Clients: `alloc_client()` never refuses on the count. At the bound, and
  only if `nn->nfsd_courtesy_clients` is non-zero, it kicks the laundromat.
- `nfserr_jukebox` from EXCHANGE_ID or SETCLIENTID: never means that a limit
  was hit; for example `create_client()` failed to allocate.
- nfsd_drc_max_mem, nfsd_drc_mem_used and nfs4_courtesy_client_count are not
  in this tree. There is no session memory budget.
- Slots: `alloc_session()` needs only slot 0; CREATE_SESSION returns
  `nfserr_jukebox` if that fails. `nfsd4_sequence()` grows the table, capped
  by `svc_serv_maxthreads()`. `nfsd_slot_shrinker_scan()` lowers
  `se_target_maxslots`; `nfsd4_sequence()` then frees the slots.
- Delegation test: in `__alloc_init_deleg()`, so directory delegations from
  `alloc_init_dir_deleg()` count too. Both counters are global, not per net
  namespace.
- `nfs4_alloc_stid()`: returns NULL on failure; each caller picks the status.
