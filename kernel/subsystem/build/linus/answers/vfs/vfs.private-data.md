- Failure after `->open()` returned 0: `FMODE_OPENED` is already set, so the
  caller's `fput()` runs `->release()`; the open method's allocation must not
  be freed a second time.
- Such failures, for example: the `O_DIRECT` test at the end of
  `do_dentry_open()`; in `do_open()`, `security_file_post_open()` and
  `handle_truncate()`; `may_open()` after `->atomic_open()` opened the file.
- Files from `alloc_file_pseudo()` or `alloc_file_clone()`: `file_init_path()`
  sets `FMODE_OPENED` although `->open()` never ran.
- `fput()` on an error path after such a file was created: runs `->release()`
  with whatever `private_data` holds then.
- `__anon_inode_getfile()`: sets `private_data` to its `priv` argument before
  it returns the file.
