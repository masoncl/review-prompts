- `__dynamic_array(type, item, len)`: has no assign macro; the block writes
  through `__get_dynamic_array(item)`.
- `__dynamic_array()` `len`: a count of elements; `__get_dynamic_array_len()`
  returns bytes.
- `__string_len(item, src, len)`: filled with `__assign_str(item)`, read with
  `__get_str(item)`.
- `__sockaddr(field, len)`: filled with `__assign_sockaddr(dest, src, len)`,
  read with `__get_sockaddr(field)`.
- `__rel_string()`, `__rel_string_len()`, `__rel_bitmask()`, `__rel_cpumask()`
  and `__rel_sockaddr()`: filled and read with their own macros in
  `include/trace/stages/stage6_event_callback.h` and
  `include/trace/stages/stage3_trace_output.h`, for example
  `__assign_rel_str()` and `__get_rel_str()`;
  `__rel_dynamic_array()` has no assign macro and is written through
  `__get_rel_dynamic_array()`. Mixing with the plain forms names a
  `__data_loc_<item>` or `__rel_loc_<item>` member that the record does not
  have and fails to build.
- `__get_bitmask()` and `__get_cpumask()`: inside `TP_fast_assign()` they are
  the raw destination pointer (`include/trace/stages/stage6_event_callback.h`);
  inside `TP_printk()` they return a formatted string from
  `trace_print_bitmask_seq()` (`include/trace/stages/stage3_trace_output.h`).
- `__assign_bitmask(dst, src, nr_bits)`: copies `__bitmask_size_in_bytes()`,
  which is `nr_bits` rounded up to whole longs; `src` must be readable to that
  size.
