- `bio_chain_endio()` in `block/bio.c`: its body is `BUG()`; it is a marker
  only. `bio_endio()` compares `bi_end_io` with it and runs
  `__bio_chain_endio()` instead of calling it.
- **Unsafe usage**: calling the handler of a `bio_chain()` child through the
  `bi_end_io` pointer; it reaches `BUG()` in `bio_chain_endio()`.
  - Safe: `bio_endio()` on the child, which never calls the marker.
  - Safe: the pointer calls in `bio_complete_work_fn()` and
    `bio_complete_batch_cpu_dead()`; `bio_endio()` queues a bio there only
    after its chain test.
- `BIO_CHAIN`: set on the parent by `bio_inc_remaining()`; `bio_chain()` does
  not set it on the child. `bio_remaining_done()` clears it when
  `__bi_remaining` reaches zero.
- `bio_endio()` makes no blk-throttle or blk-crypto call and does not call
  `bio_uninit()` on the bio whose handler it runs; there is no
  blk_throtl_bio_endio() in this tree. Under `CONFIG_BLK_CGROUP` it does
  `blkg_put()` of `bi_blkg`, after the chain jump.
- `BIO_COMPLETE_IN_TASK` (`include/linux/blk_types.h`): when set and
  `bio_in_atomic()` is true, `bio_endio()` does not call `bi_end_io`; it queues
  the bio with `__bio_complete_in_task()` and a per-CPU work item calls the
  handler later. A direct `bi_end_io` call skips this deferral.
- `__bio_complete_in_task()`: links the bio through `bi_next`
  (`bio_list_add()`).
- `bio_in_atomic()` in `include/linux/bio.h`: always true without
  `CONFIG_PREEMPT_COUNT`, so flagged bios are always deferred there.
- `BIO_COMPLETE_IN_TASK` on a chain child: no effect; `bio_endio()` moves to
  the parent before it tests the flag, so the parent's flag decides.
- **Unsafe usage**: `BIO_COMPLETE_IN_TASK` on a bio whose `bi_end_io` is NULL;
  `bio_endio()` tests for NULL only on the non-deferred branch, and
  `bio_complete_work_fn()` calls the pointer unconditionally.
  - Safe: handler set before submission, as `__bh_submit()` in `fs/buffer.c`
    does.
- `bio_complete_in_task()` in `include/linux/bio.h`: for use inside a handler;
  when it returns `true` the bio is queued and the handler runs again from the
  worker, where the flag it set makes the call return `false`.
- `bio_endio_status()` in `include/linux/bio.h`: stores `bi_status`, then calls
  `bio_endio()`; `bio_io_error()` and `bio_wouldblock_error()` wrap it.
- **Unsafe usage**: passing as the child to `bio_chain()` a bio with NULL
  `bi_pool` (set up by `bio_init()` in caller memory, or from `bio_kmalloc()`);
  `__bio_chain_endio()` calls `bio_put()`, and `bio_free()` dereferences
  `bi_pool`.
  - Safe: a child from a `struct bio_set`, as the `bio_split()` result that
    `bio_submit_split_bioset()` chains.
- Parent `bi_status` with several failing children: `__bio_chain_endio()` tests
  and stores without a lock or atomic, so which child's error is kept is not
  defined.
- Parent `bi_status` written by the parent's own completer: not guarded;
  `bio_endio_status()` stores unconditionally, so a success value written
  there replaces a child's error. `blk_update_request()` in `block/blk-mq.c`
  writes `bi_status` only with a nonzero status.
