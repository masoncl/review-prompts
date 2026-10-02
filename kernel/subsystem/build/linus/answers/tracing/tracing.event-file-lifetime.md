- `ref` in `struct trace_event_file`: a `refcount_t`.
- `event_file_put()`: frees the structure only when the count reaches zero and
  `EVENT_FILE_FL_FREED` is set. At zero without the flag it warns and does not
  free. It does not free the filter.
- `remove_event_file_dir()`: frees the filter with `free_event_filter()` and
  does not free triggers. On instance removal `event_trace_del_tracer()` calls
  `clear_event_triggers()` first.
- Holders of `ref`: the creation reference, dropped in
  `remove_event_file_dir()`; one taken in `event_create_dir()` for eventfs;
  one for each open through `tracing_open_file_tr()`.
- eventfs reference: dropped by `event_release()`, the `release` callback of
  the `enable` entry, called from `release_ei()` in
  `fs/tracefs/event_inode.c` when the last reference to the
  `struct eventfs_inode` of the event directory goes: after
  `eventfs_remove_dir()` and after every dentry of the directory and its
  files is released. Every open file in the directory holds such a dentry.
- Open method that takes no reference of its own, such as
  `event_trigger_regex_open()` and `trace_format_open()`: the structure stays
  allocated through the eventfs reference.
- Open through `tracing_open_file_tr()`: also holds `tr->ref`, so
  `__remove_instance()` returns -EBUSY and only removal of the event can set
  `EVENT_FILE_FL_FREED` while the file is open.
- Open without it: instance removal can set the flag and free `file->tr` while
  the file is open.
- `event_file_data()`: asserts `event_mutex` with `lockdep_assert_held()` and
  warns when the pointer is NULL or `EVENT_FILE_FL_FREED` is set. It is for a
  second fetch while the mutex is still held after `event_file_file()`
  succeeded, as `f_next()` does after `f_start()`.
- `event_file_file()` and `event_file_data()`: read `i_private` with a plain
  load.
- `id` file: `i_private` holds the event type number, not a pointer;
  `event_id_read()` reads it directly.
- **Potentially unsafe usage**: using the `struct trace_event_file` from the
  inode without `event_mutex` and a non-NULL `event_file_file()`.
  - Unsafe: when the code follows `file->event_call`, `file->filter`,
    `file->system` or `file->triggers`, or follows `file->tr` in a file whose
    open did not take `tr->ref`; these may be freed once
    `remove_event_file_dir()` has run.
  - Safe: when it reads only a member stored in the structure while a
    reference is held, as `event_enable_read()` reads `file->sm_ref` after it
    drops the mutex; `event_file_put()` frees only at zero.
  - Safe: when it passes the value of `file->tr` to `trace_array_get()`, which
    dereferences it only after it matched a listed instance, as
    `tracing_open_file_tr()` does.
  - Safe: when it follows `file->tr` in a file opened through
    `tracing_open_file_tr()`, as `tracing_release_file_tr()` does; the open
    holds `tr->ref`, and `__remove_instance()` returns -EBUSY while
    `tr->ref > 1`.
