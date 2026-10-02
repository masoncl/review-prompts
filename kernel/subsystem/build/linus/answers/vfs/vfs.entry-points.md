| Job | Start reading from |
|---|---|
| Open a file | `do_file_open()` in `fs/namei.c`; there is no do_filp_open() here. `do_sys_openat2()` and `file_open_name()` in `fs/open.c` call it |
| Create by name, from a syscall | `filename_mknodat()`, `filename_mkdirat()`, `filename_symlinkat()`, `filename_linkat()` in `fs/namei.c`; there is no do_mknodat() or do_mkdirat() here |
| Create on open with `O_CREAT` | `lookup_open()` in `fs/namei.c`; it calls `atomic_open()` or `->create` directly and does not call `vfs_create()` |
| Unlink by name, from a syscall | `filename_unlinkat()`, `filename_rmdir()` in `fs/namei.c`; there is no do_unlinkat() here |
| Rename by name, from a syscall | `filename_renameat2()` in `fs/namei.c`; there is no do_renameat2() here |
| Create, remove, rename by name from kernel code, under a known parent | `start_creating()`, `start_removing()`, `start_renaming()` in `fs/namei.c`, paired with `end_creating()`, `end_removing()`, `end_renaming()` |
| Create or remove from kernel code, by path string | `start_creating_path()` with `end_creating_path()`; `start_removing_path()` with `end_removing_path()` |
| Look up one name under a directory from kernel code | `lookup_one()` (checks permission on the parent) or `lookup_noperm()` (does not); both take a `struct qstr`. There is no lookup_one_len() here |
| Drop the last reference to a dentry | `dput()`, then `fast_dput()`, `finish_dput()`, `dentry_kill()` in `fs/dcache.c`; there is no __dentry_kill() here |
| Drop the last reference to a file | `fput()`, then `__fput_deferred()`, `__fput()` in `fs/file_table.c`. `close(2)` uses `fput_close_sync()` and `filp_close()` uses `fput_close()` instead of `fput()` |
| Resolve a user path; find or create an inode; drop the last reference to an inode | Models have these right: `user_path_at()`, `iget_locked()` and `iget5_locked()`, `iput()` |
