- `rb_get_reader_page()`: only dispatches. `__rb_get_reader_page()` does the
  cmpxchg swap; `__rb_get_reader_page_from_remote()` asks the remote to swap
  and relinks with plain stores, no cmpxchg.
- `cpu_buffer->head_page`: a hint; the write path never writes it.
  `rb_handle_head_page()` moves the `RB_PAGE_HEAD` flag and never this field;
  `rb_set_head_page()` finds the real head from the flag.
- Writer on the reader page: after a swap the writer may still be writing the
  page the reader took (`commit_page == reader_page`).
  `__rb_get_reader_page()` waits up to `USECS_WAIT` for `write` to fall back
  inside the page.
- Write path: takes neither `cpu_buffer->lock` nor `cpu_buffer->reader_lock`,
  including `rb_move_tail()` and `rb_handle_head_page()`.
- `cpu_buffer->pages`: points at one page of the ring; the ring has no list
  head. `list_for_each_entry()` from it skips that page, which is why
  `rb_reset_cpu()` calls `rb_clear_buffer_page()` on `head_page` separately.
- Persistent buffer (`cpu_buffer->ring_meta` set): the writer also updates
  `head_buffer` in `rb_update_meta_head()` and `commit_buffer` in
  `rb_set_commit_to_write()`; the reader updates `buffers[]` in
  `rb_update_meta_reader()`.
