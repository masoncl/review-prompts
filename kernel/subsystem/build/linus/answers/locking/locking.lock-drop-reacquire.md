- There is no pipe_read() here; `anon_pipe_read()` in `fs/pipe.c` does that.
  It drops `pipe->mutex` to wait, and after retaking it reads `pipe->head` and
  `pipe->tail` again at the top of its loop.
- `find_lock_lowest_rq()` in `kernel/sched/rt.c`: re-checks the task only when
  `double_lock_balance()` returns nonzero, which is its report that it
  dropped the lock.
- The re-check there fails on `is_migration_disabled(task)`, on
  `lowest_rq->cpu` not in `task->cpus_mask`, or on
  `task != pick_next_pushable_task(rq)`. On failure it unlocks `lowest_rq`
  with `double_unlock_balance()` and gives up; `rq` stays locked.
- `find_inode()` in `fs/inode.c`: `__wait_on_freeing_inode()` drops
  `inode->i_lock`, the RCU read lock and, if held, `inode_hash_lock`; after
  it returns, `find_inode()` restarts the hash chain walk from the head.
