- Queue Freezing Synchronization Rule: When analyzing potential races between
  bio completion paths and queue teardown functions: blk_mq_freeze_queue()
  prevents new I/O and waits for q->q_usage_counter to reach zero. This only
  protects teardown if the path actually takes/releases the usage ref
  (blk_queue_enter/blk_queue_exit via blk_try_enter_queue or bio_queue_enter).
  Custom submission/plug paths that bypass this can slip past freeze; verify
  the accounting for the bio type you're analyzing.
- bio chains are formed as the result of merging tests.  These establish
  rules about what bios are allowed to be mixed together.  If you find a bug
  related to chains of bios, first make sure the merging rules allows that
  chain to exist

## Bio Mempool Allocation Guarantees

Bio allocations with GFP_NOIO/GFP_NOFS often use bioset/bvec mempools when the
bioset was created with one. That makes ENOMEM unlikely but not impossible;
if no mempool is present or extra allocations happen outside the pool (e.g.,
large bvecs), failure is still possible.

- `bio_alloc_bioset()` - uses bioset mempool when configured; still check for NULL
- `bvec_alloc()` - falls back to mempool only if the bioset provides it
- `bio_integrity_prep()` - uses GFP_NOIO; may still fail without a mempool contract
- `bio_integrity_alloc_buf()` - uses GFP_NOFS; may still fail without a mempool contract

Load block specific rules:
- **BLOCK-001** (patterns/BLOCK-001.md): Mandatory when struct bios are passed or used
