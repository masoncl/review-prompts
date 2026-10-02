- `BTRFS_PATH_AUTO_RELEASE()` in `fs/btrfs/ctree.h`: declares an on-stack,
  zeroed `struct btrfs_path` that gets `btrfs_release_path()` at scope exit;
  no allocation, pass `&path`; see `fs/btrfs/scrub.c` for a user.
- `btrfs_search_slot()` returning `< 0`: the path holds nothing taken by the
  search (`btrfs_release_path()` runs at `done:`), unless
  `p->skip_release_on_error` is set, or the error is `-ENOMEM` from
  `finish_need_commit_sem_search()` (`p->need_commit_sem` set).
- `p->skip_release_on_error`: the path can still hold its extent buffers and
  locks after the error and the caller must release it; set for example
  before `btrfs_insert_empty_item()` in `fs/btrfs/inode-item.c` and
  `fs/btrfs/tree-log.c`.
- Reusing a path: `btrfs_search_slot()` only does
  `WARN_ON(p->nodes[0] != NULL)` at entry, it does not release, so the caller
  must call `btrfs_release_path()` between searches.
