- Models have the layout, the accessors and the borrow rule right; see
  `__fget_light()` in `fs/file.c`.
- `fdget_pos()`: takes `f_pos_lock` only when `file_needs_f_pos_lock()` agrees:
  `FMODE_ATOMIC_POS` is set and either the count is not exactly one or the
  file has `iterate_shared`.
