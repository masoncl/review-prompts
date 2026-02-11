# Block Layer Subsystem Details

## Queue Freezing Synchronization

`blk_mq_freeze_queue()` ensures all in-flight bios complete by waiting for
`q->q_usage_counter` to reach zero. Every bio holds a reference to
`q->q_usage_counter` from submission (`blk_try_enter_queue`) to completion
(`blk_queue_exit`), so teardown functions protected by a freeze cannot race
with bio completion paths.

## Bio Merging

Merging combines bios into requests at the queue level. The merging rules
establish which bios are allowed to be combined. When investigating a bug
related to merged bios, first verify the merging rules permit that
combination to exist. All bio operation types can pass through merge paths.

## Bio Operation Type Safety

Accessing bio data fields on a bio that has no data buffers (e.g., discard,
flush) causes a NULL pointer dereference. Code that handles bios must check
the operation type before accessing data fields.

| Operation | `bi_io_vec` | Has Data |
|-----------|-------------|----------|
| `REQ_OP_READ` | Valid | Yes |
| `REQ_OP_WRITE` | Valid | Yes |
| `REQ_OP_DISCARD` | NULL | No |
| `REQ_OP_FLUSH` | NULL | No |
| `REQ_OP_WRITE_ZEROES` | NULL | No |
| `REQ_OP_SECURE_ERASE` | NULL | No |

**Data field accesses that require guards:**
- Direct: `bio->bi_io_vec`, `bio->bi_vcnt`, `bio->bi_iter.bi_bvec_done`
- Indirect: `bio_get_first_bvec()`, `bio_get_last_bvec()`,
  `bio_for_each_bvec()`, `bio_for_each_segment()`

**Required guard:** `bio_has_data()` before accessing any data field. Note
that `op_is_write()` is NOT a valid guard — it returns true for DISCARD,
WRITE_ZEROES, and SECURE_ERASE (which have no data). Merge functions must
also guard data field accesses since all bio operation types can reach them.

## Bio Mempool Allocation Guarantees

Mempool-backed bio allocations (`bio_alloc`, `bio_alloc_bioset`) with
`GFP_NOIO`/`GFP_NOFS` cannot fail (mempool guarantee via
`__GFP_DIRECT_RECLAIM`). ENOMEM paths are only reachable with
`GFP_ATOMIC`/`GFP_NOWAIT`. Note that `bio_kmalloc()` does NOT use a mempool
and CAN fail regardless of GFP flags.

- `bio_alloc_bioset()` — mempool alloc, cannot fail with `GFP_NOIO`
- `bvec_alloc()` — falls back to mempool with `__GFP_DIRECT_RECLAIM`
- `bio_integrity_prep()` — uses `GFP_NOIO`, cannot fail
- `bio_integrity_alloc_buf()` — tries `kmalloc` with `GFP_NOIO` (without
  direct reclaim), falls back to mempool with `GFP_NOFS`; cannot fail
