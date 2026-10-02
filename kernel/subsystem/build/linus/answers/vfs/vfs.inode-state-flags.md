- `I_CREATING` setters in `fs/inode.c`: `insert_inode_locked()` (with `I_NEW`,
  under `i_lock`) and `insert_inode_locked4()` (before it calls
  `inode_insert5()`); `inode_insert5()` itself sets only `I_NEW`. Filesystems
  set it too, on an inode not yet hashed, for example `ovl_create_object()`.
- `discard_new_inode()`: clears `I_NEW` only; `I_CREATING`, if set, stays, so
  `find_inode()` and `find_inode_fast()` keep returning `ERR_PTR(-ESTALE)` for
  that inode until `I_FREEING` or `I_WILL_FREE` is set on it.
- `I_NEW` without `I_CREATING` seen by a hash lookup: `find_inode()` and
  `find_inode_fast()` take a reference with `__iget()` first; the caller,
  except `ilookup5_nowait()`, then sleeps in `wait_on_new_inode()`; there is
  no wait_on_inode() in this tree.
- `I_FREEING` setters: `iput_final()`, `evict_inodes()`, `inode_lru_isolate()`;
  all under `i_lock` with `i_count` 0; there is no invalidate_inodes() here.
- Wakeups on `__I_NEW`: `inode_wake_up_bit()`, which is `wake_up_var()` on
  `inode_state_wait_address()`; `wake_up_bit()` on the word wakes nobody.
- Not every flag test is under `i_lock`: `igrab_from_hash()`,
  `find_inode_rcu()` and `find_inode_by_ino_rcu()` use
  `inode_state_read_once()`.
- `igrab_from_hash()` in `fs/inode.c`: tried first on each matching inode in
  `find_inode()` and `find_inode_fast()`; if none of `I_NEW`, `I_CREATING`,
  `I_FREEING`, `I_WILL_FREE` is seen and `i_count` is nonzero it takes the
  reference without `i_lock`.
- **Unsafe usage**: setting `I_NEW` or `I_CREATING` on an inode that is
  already inserted in the inode hash table; `igrab_from_hash()` may have
  tested the flags just before and hands the inode out as initialised.
  - Safe: set the flag before the insertion, as `insert_inode_locked4()` does,
    or together with it inside one `i_lock` hold, as `iget_locked()` and
    `insert_inode_locked()` do.
