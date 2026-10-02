- `NFSD4_SLOT_INUSE` is tested first in `check_slot_seqid()`: matching seqid
  gives `nfserr_jukebox`, every other seqid (next one included) gives
  `nfserr_seq_misordered`.

| Slot not in use, seqid is (first match wins) | Status |
|---|---|
| slot seqid + 1 | `nfs_ok` |
| 1, with `NFSD4_SLOT_REUSED` | `nfs_ok` |
| slot seqid | `nfserr_replay_cache` (internal) |
| other | `nfserr_seq_misordered` |

- Reused slot, seqid equal to the remembered one and not 1:
  `nfserr_replay_cache` turns into `nfserr_seq_misordered` in
  `nfsd4_sequence()`, because the new slot has no `NFSD4_SLOT_INITIALIZED`.
- `sl_seqid` update: in `nfsd4_sequence()`, only after
  `nfsd4_sequence_check_conn()` and `xdr_restrict_buflen()` also pass; a
  request failing either leaves the slot untouched.
- `NFSD4_SLOT_REUSED`: cleared at that same point.
- `nfsd4_create_session()` passes flags 0 and bumps `cl_cs_slot.sl_seqid`
  right after `nfs_ok`, before the credential checks; later errors are cached
  in the slot, and only the `nfserr_jukebox` path decrements it again.
