- Error state: there is no BTRFS_FS_STATE_ERROR bit in this tree;
  `__btrfs_handle_fs_error()` stores the errno in `fs_info->fs_error`, tested
  with `BTRFS_FS_ERROR()` in `fs/btrfs/fs.h`.
- `btrfs_abort_should_print_stack()` in `fs/btrfs/transaction.h` (there is no
  abort_should_print_stack()): false for exactly `-EIO`, `-EROFS`, `-ENOMEM`.
- `btrfs_handle_fs_error()`: touches no transaction; it does not set
  `trans->aborted` or `BTRFS_FS_STATE_TRANS_ABORTED` and wakes no transaction
  waiters.
- `btrfs_handle_fs_error()` call sites: none in `fs/btrfs/transaction.c` or
  `fs/btrfs/disk-io.c`; `btrfs_commit_transaction()` calls
  `btrfs_abort_transaction()` when `btrfs_write_and_wait_transaction()` fails.
- Choosing between the two: see `process_one_buffer()` in
  `fs/btrfs/tree-log.c`, which aborts when `trans` is non-NULL and calls
  `btrfs_handle_fs_error()` otherwise; it is also used where no handle is
  held, for example in `rollback_verity()` in `fs/btrfs/verity.c` when
  starting the transaction failed.
- Helper that aborts: returns the error without ending the handle, as
  `btrfs_update_root()` in `fs/btrfs/root-tree.c` does; the function that
  started or joined the handle ends it.
- `btrfs_commit_transaction()`: frees the handle on every return path,
  including errors, so no `btrfs_end_transaction()` may follow it.
- **Unsafe usage**: passing a value that can be zero or positive to
  `btrfs_abort_transaction()`, such as an unconverted `1` from
  `btrfs_search_slot()`.
  - Unsafe: the sign carries "first abort" into
    `__btrfs_abort_transaction()`, so a positive value inverts it and is
    stored negated; zero is stored in `trans->aborted` and
    `fs_info->fs_error`, so `TRANS_ABORTED()` and `BTRFS_FS_ERROR()` are false
    afterwards.
  - Unsafe: `VERIFY_NEGATIVE_ERROR()` in `fs/btrfs/transaction.h` breaks the
    build only for a compile-time constant that is not negative; a variable
    is checked only under `CONFIG_BTRFS_DEBUG`, by `DEBUG_WARN()`.
  - Safe: convert first, as `__btrfs_update_delayed_inode()` in
    `fs/btrfs/delayed-inode.c` does with `if (ret > 0) ret = -ENOENT;`.
