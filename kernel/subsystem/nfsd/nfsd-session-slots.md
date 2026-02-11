# NFSD Session Slots and SEQUENCE Operations

Incorrect slot state management causes reply cache corruption
(returning a cached reply for a different operation), protocol
violations (accepting replayed requests as new), or crashes
(accessing a slot beyond the allocated table). The SEQUENCE
operation is the first operation in every NFSv4.1+ compound and
gates all subsequent operations.

## Session Structure

`struct nfsd4_session` (defined in `fs/nfsd/state.h`) holds:

- `se_slots` — an xarray of `struct nfsd4_slot` pointers for
  forward channel slots.
- `se_fchannel` — channel attributes including `maxreqs` (current
  slot table size), `maxresp_cached` (max cached reply size).
- `se_slot_gen` — generation counter for slot table resizing.
- `se_target_maxslots` — target slot count for dynamic resizing.
- `se_dead` — session marked for destruction.

## Slot Structure

`struct nfsd4_slot` (defined in `fs/nfsd/state.h`) holds:

- `sl_seqid` — expected sequence ID for this slot.
- `sl_status` — cached reply status.
- `sl_flags` — state flags (see below).
- `sl_generation` — matches `se_slot_gen` when slot is current.
- `sl_data[]` — flexible array for cached reply data.
- `sl_datalen` — length of cached data.
- `sl_opcnt` — operation count in cached reply.

Slot flags:

| Flag | Meaning |
|------|---------|
| `NFSD4_SLOT_INUSE` | Slot currently processing a request |
| `NFSD4_SLOT_CACHETHIS` | Client requested reply caching |
| `NFSD4_SLOT_INITIALIZED` | Slot has been used at least once |
| `NFSD4_SLOT_CACHED` | Slot contains a cached reply |
| `NFSD4_SLOT_REUSED` | Slot was freed and reallocated |

## SEQUENCE Operation (nfsd4_sequence)

`nfsd4_sequence()` in `fs/nfsd/nfs4state.c` processes the SEQUENCE
operation under `nn->client_lock`:

1. **Session lookup**: finds session by ID in hash table.
2. **Bounds check**: validates `seq->slotid < maxreqs`.
3. **Seqid validation**: `check_slot_seqid()` compares request
   seqid against `sl_seqid`:
   - **Match (seqid == sl_seqid + 1)**: new request, proceed.
   - **Replay (seqid == sl_seqid)**: return cached reply if
     `NFSD4_SLOT_INITIALIZED` and request matches cache.
   - **Misordered**: return `nfserr_seq_misordered`.
   - **False retry**: return `nfserr_seq_false_retry` if replay
     request doesn't match cached parameters.
4. **Accept**: updates `sl_seqid`, sets `NFSD4_SLOT_INUSE`, sets
   `NFSD4_SLOT_CACHETHIS` if requested.
5. **Dynamic growth**: if the client uses the highest slot,
   attempts to grow the slot table by ~20%.

## Reply Caching

When `NFSD4_SLOT_CACHETHIS` is set, the compound reply is cached
in the slot's `sl_data[]` after the compound completes. On replay
detection, `nfsd4_replay_cache_entry()` returns the cached reply.

The response buffer is restricted to `maxresp_cached` when caching
is requested, or `maxresp_sz` otherwise, via
`xdr_restrict_buflen()`.

**REPORT as bugs**: Code that caches a reply when the RFC requires
generating a fresh response (e.g., certain error conditions where
the compound must be re-executed). See commit 48990a0923a7 for an
example where SEQUENCE incorrectly cached a response.

## Slot Table Resizing

The session can dynamically grow and shrink the slot table:

- **Growth**: `nfsd4_sequence()` allocates new slots with
  `GFP_NOWAIT` under `client_lock` when the client uses the highest
  available slot, up to `NFSD_MAX_SLOTS_PER_SESSION`.
- **Shrink**: when `se_target_maxslots < maxreqs` and the client
  acknowledges via `seq->maxslots`, `free_session_slots()` frees
  excess slots.
- **Generation tracking**: `sl_generation` vs `se_slot_gen` detects
  slots that were freed and reallocated (`NFSD4_SLOT_REUSED`).

## Quick Checks

- **Slot bounds**: verify slot IDs from the client are validated
  against `se_fchannel.maxreqs` before use.
- **Seqid ordering**: verify `check_slot_seqid()` is called before
  accepting a request on a slot.
- **Cache-vs-fresh**: verify reply caching decisions match RFC 8881
  section 18.46 requirements — not all replies should be cached.
- **Lock coverage**: slot state is accessed under `nn->client_lock`
  in `nfsd4_sequence()`; verify no unlocked access elsewhere.
