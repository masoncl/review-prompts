- Lock: `client_lock` in `struct nfsd_net` covers lookup, seqid check, growth,
  shrink and `reduce_session_slots()` (which uses `spin_trylock()`); `se_lock`
  is for backchannel slots only.
- Without `client_lock`: `nfsd4_sequence_done()` stores the reply and clears
  `NFSD4_SLOT_INUSE`; from `nfsd4_sequence()` until that clear, only the flag
  keeps other requests off the slot.
- Growth trigger: `seq->slotid == se_fchannel.maxreqs - 1` on an accepted new
  request, and `se_target_maxslots >= se_fchannel.maxreqs`.
- Growth cap: min of `NFSD_MAX_SLOTS_PER_SESSION` and
  `svc_serv_maxthreads(rqstp->rq_server)`; growth also raises
  `se_target_maxslots`.
- Shrinker: `nfsd_slot_shrinker_count()` and `nfsd_slot_shrinker_scan()`; there
  are no nfsd_slot_count() or nfsd_slot_scan(). The scan lowers
  `se_target_maxslots` by at most one per session visited and frees no slot
  itself.
- `free_session_slots()` from `nfsd4_sequence()` needs all of: target below
  `maxreqs`; `slot->sl_generation == se_slot_gen`; `seq->maxslots` at or below
  target; `seq->slotid` below target; `nfsd4_slots_inuse()` false from target
  up.
- Reply field: `target_maxslots` in `struct nfsd4_sequence`, encoded minus one
  by `nfsd4_encode_sequence()`; `sr_target_highest_slotid` is a field of the
  NFS client's `struct nfs4_sequence_res`, not of nfsd.
- Freed slot: only `sl_seqid` survives, as `xa_mk_value()` at the same index.
  Cached reply, `sl_cred` and `NFSD4_SLOT_INITIALIZED` are lost.
- **Potentially unsafe usage**: dereferencing `xa_load()` on `se_slots`.
  - Unsafe: index at or above `se_fchannel.maxreqs`; the entry is NULL or a
    value entry, and `nfsd4_sequence()` has no NULL or `xa_is_value()` test
    after its `nfserr_badslot` check.
  - Safe: index below `maxreqs` under `client_lock`, as `nfsd4_slots_inuse()`
    does; on a hashed session `free_session_slots()` and the growth loop
    change `maxreqs` and the entries under that lock.
  - Safe: index equal to `maxreqs` read only through `xa_is_value()` and
    `xa_to_value()`, never dereferenced, as the growth loop in
    `nfsd4_sequence()` does.
