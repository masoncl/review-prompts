- `rb_is_static()`: true for a mapped, persistent
  (`struct ring_buffer_cpu_meta`) or remote (`struct ring_buffer_remote`) CPU
  buffer.
- Persistent header check: `rb_meta_init()` tests `magic`, `struct_sizes`,
  `total_size` and `buffers_offset`. There is no rb_meta_valid() or
  rb_cpu_meta_init function.
- `rb_cpu_meta_valid()`: tests `subbuf_size == PAGE_SIZE`, `nr_subbufs`,
  `head_buffer` and `commit_buffer` in range, `buffers[]` in range and
  unique. The `commit` bound is in `__rb_validate_buffer()`.
- `struct ring_buffer_cpu_meta`: `head_buffer` and `commit_buffer` are
  addresses, rebased in `rb_range_meta_init()`; the reader page is
  `buffers[0]`.
- Bad sub-buffer: `__rb_validate_buffer()` empties that page alone and sets
  `commit` to `RB_MISSED_EVENTS`; the rest of the CPU buffer is kept.
- Whole CPU buffer wiped: when `rb_meta_init()` or `rb_cpu_meta_valid()`
  fails, or when `rb_meta_validate_events()` never reaches the commit page.
- Head rewind: `rb_meta_validate_events()` walks back from the head, so pages
  already read in the last boot are readable again; see
  `rb_meta_inject_reader_page()`.
- Persistent in `kernel/trace/trace.c`: `allocate_trace_buffer()` does
  `tr->mapped++`, so snapshots are refused; `trace_ok_for_array()` rejects
  tracers that use a snapshot.
- `tracing_buffers_mmap()`: -ENODEV for `TRACE_ARRAY_FL_MEMMAP` and
  `TRACE_ARRAY_FL_VMALLOC`; other persistent buffers can be mapped.
- `ring_buffer_map()` on an already mapped CPU buffer: maps again and counts
  `user_mapped`; -EBUSY only at `UINT_MAX`. Nothing is read back from user
  space.
- `ring_buffer_map()` errors: -EINVAL for a remote buffer, -E2BIG above
  `rb_static_max_pages()`; `__rb_map_vma()` gives -EPERM for `VM_WRITE`,
  `VM_EXEC` or no `VM_MAYSHARE`.
- Snapshot against mapping: `get_snapshot_map()` in
  `kernel/trace/trace_snapshot.c` returns -EBUSY when `tr->snapshot` is set.
- Remote allocation: `alloc_buffer()` needs 2 to `rb_static_max_pages()`
  pages; `__rb_allocate_pages()` fails unless `nr_page_va` is `nr_pages + 1`.
- Remote page ids: `ring_buffer_desc_page()` bounds them by `nr_page_va`;
  `__rb_get_reader_page_from_remote()` rejects `reader.id > nr_pages` after
  the swap.
- Remote event content: not validated at allocation.
  `rb_meta_validate_events()` returns at once without `ring_meta`;
  `rb_read_remote_meta_page()` copies the counters.
- Remote refusals: `record_disabled` is raised at allocation on the buffer
  and each CPU buffer, so `ring_buffer_lock_reserve()` returns NULL and
  `ring_buffer_write()` -EBUSY; resize and order change -EBUSY.
- Remote data arrival: `ring_buffer_poll_remote()` re-reads the counters from
  the meta page and wakes waiters; `kernel/trace/trace_remote.c` calls it
  from delayed work.
