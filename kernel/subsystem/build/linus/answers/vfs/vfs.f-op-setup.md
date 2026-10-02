- NULL `i_fop` or failed `try_module_get()`: both hit `WARN_ON(!f->f_op)` in
  `do_dentry_open()` and return `-ENODEV`.
- Failed open: `cleanup_all` calls `fops_put(f->f_op)` and leaves `f_op`
  pointing at the table; it is not reset to NULL.
- `replace_fops()`: a statement macro; it returns nothing and calls no
  `->open`.
- New `->open` failing after `replace_fops()`: `do_dentry_open()` drops the
  new table's reference under `cleanup_all`; the open method must not drop it
  too, see `chrdev_open()` in `fs/char_dev.c`.
- Pseudo files: `file_init_path()` in `fs/file_table.c` stores the caller's
  table without `fops_get()`, yet `__fput()` always calls `fops_put()`.
- `__anon_inode_getfile()`: takes that module reference itself with
  `try_module_get()` before `alloc_file_pseudo()`.
- **Potentially unsafe usage**: assigning `file->f_op` directly.
  - Unsafe: when the old or the new table sets `owner`, the two differ, and
    the code does not itself pin the new owner and drop the old one;
    `do_dentry_open()` pinned the old owner and `fops_put()` in `__fput()`
    drops the new one.
  - Safe: `fops_get()` on the new table, then `replace_fops()`, inside
    `->open()`, as `chrdev_open()` does.
  - Safe: `fops_get()` on the new table by hand, with the old table saved
    and passed to `fops_put()` later, as `snd_card_disconnect()` and
    `snd_card_file_remove()` in `sound/core/init.c` do.
  - Safe: when neither table sets `owner`, as `memory_open()` in
    `drivers/char/mem.c`; `module_put()` ignores NULL.
