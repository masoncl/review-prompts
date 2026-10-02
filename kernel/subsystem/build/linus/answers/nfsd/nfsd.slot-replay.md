- Cache decision: `NFSD4_SLOT_CACHETHIS` alone, from `seq->cachethis`; there is
  no nfsd4_cache_this() or nfsd4_is_solo_sequence().
- Nothing stored: `nfsd4_sequence_done()` touches no slot when
  `nfsd4_has_session()` is false (`cstate.slot` is NULL), and
  `nfsd4_store_cache_entry()` returns early when `resp->opcnt == 1` with
  non-zero `cstate.status`; in that second case `sl_seqid` stays advanced.
- Oversize reply: never truncated into the slot; with `cachethis` set
  `nfsd4_sequence()` limits the encode buffer to `maxresp_cached`, so the op
  fails with `nfserr_rep_too_big_to_cache`.
- `nfsd4_store_cache_entry()`: copies `buf->len - data_offset` bytes into
  `sl_data` with no bound check; it relies on that limit and on the size
  chosen in `nfsd4_alloc_slot()`.
- `replay_matches_cache()` fails when: cachethis differs from
  `NFSD4_SLOT_CACHETHIS`; `sl_opcnt < argp->opcnt` with zero `sl_status`;
  `sl_opcnt > argp->opcnt`; `same_creds()` false. No opcode or hash compare.
- Replay encode: `nfsd4_replay_cache_entry()` calls `nfsd4_encode_operation()`
  on `args->ops[0]`; there is no nfsd4_enc_sequence_replay().
- Solo SEQUENCE replay (`args->opcnt == 1`): returns the re-encoded SEQUENCE
  status, before `NFSD4_SLOT_CACHED` is looked at.
