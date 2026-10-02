- Source pointer: saved by the measure step in member `<item>_ptr_` of
  `struct trace_event_data_offsets_<class>`; `__assign_str()` reads it from
  there. There is no __str_src helper; `__string_src()` only substitutes
  `EVENT_NULL_STR` for the `strlen()`.
- `__assign_str()`: `memcpy()` of the measured length minus one, then writes
  the NUL itself; it does not use `strcpy()`, so the copy cannot exceed the
  reserved bytes and the field always ends in NUL.
- Source that shrank between the steps: `__assign_str()` still reads the full
  measured length from the source.
- `__string()` source expression: expanded twice in the measure step (once for
  `strlen()`, once for the saved pointer).
- **Potentially unsafe usage**: `__string_len()` with a source that can be
  NULL.
  - Unsafe: with a non-zero `len`; nothing measures the source, and
    `__assign_str()` copies `len` bytes starting at `EVENT_NULL_STR`.
  - Safe: `len` is 0 whenever the source is NULL, as `nfsd_handle_dir_event`
    in `fs/nfsd/trace.h`; the record then holds an empty string, not
    `"(null)"`.
  - Safe: `__string()`, which measures `EVENT_NULL_STR` itself.
