- `evict_inodes()` on `need_resched()`: drops the lock, runs
  `dispose_list()`, retakes the lock and resumes from the current inode; it
  does not restart from the list head.
- `inode_sb_list_del()`: called only from `evict()`, so an inode leaves
  `s_inodes` only in the hands of whoever set `I_FREEING` on it.
- **Potentially unsafe usage**: dropping `s_inode_list_lock` inside the loop
  and continuing from the current inode.
  - Unsafe: when nothing keeps the current inode on `s_inodes`; `evict()`
    unlinks and frees it and the next-pointer read is a use after free.
  - Safe: holding a reference taken with `__iget()` under `i_lock`, after
    skipping `I_NEW | I_FREEING | I_WILL_FREE`, and deferring `iput()` of the
    previous inode to the unlocked window, as `drop_pagecache_sb()`,
    `add_dquot_ref()` and `sync_bdevs()` do.
  - Safe: the walker itself set `I_FREEING` on the current inode and has not
    yet put it on the list it passes to `dispose_list()`, as `evict_inodes()`
    does.
- Loop that never drops the lock: needs no reference; `remove_dquot_ref()` in
  `fs/quota/dquot.c` scans `I_NEW` inodes too and touches only pointers
  guarded by `dq_data_lock`.
- `wait_sb_inodes()`: not an example; it walks `s_inodes_wb` under
  `s_inode_wblist_lock` and `rcu_read_lock()`.
- `fsnotify_unmount_inodes()`: not an example; through
  `fsnotify_get_living_inode()` it walks `inode_conn_list` of
  `struct fsnotify_sb_info` under `list_lock`, in `fs/notify/mark.c`.
