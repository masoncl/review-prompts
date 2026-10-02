- `CONFIG_ARCH_HAS_NON_OVERLAPPING_ADDRESS_SPACE`: when it is set,
  `fetch_store_strlen()`, `fetch_store_string()` and `probe_mem_read()` in
  `kernel/trace/trace_probe_kernel.h` read an address below `TASK_SIZE` as
  a user address; when it is not set they read every address as kernel.
- Uprobe: uses only faulting copies, `copy_from_user()`,
  `strncpy_from_user()` and `strnlen_user()`; none of its helpers in
  `kernel/trace/trace_uprobe.c` is a nofault call.
- Uprobe `$comm`: `FETCH_OP_COMM` yields the sentinel `FETCH_TOKEN_COMM`, and
  the string helpers copy `current->comm` directly when they see it.
- When the fetch runs: kprobe, fprobe and eprobe call `store_trace_args()`
  after reserve, into the record, with preemption off; uprobe fetches first
  into `struct uprobe_cpu_buffer` under its mutex, then copies after reserve.
- `struct trace_probe`: has no probe_flags member; the `TP_FLAG_TRACE` and
  `TP_FLAG_PROFILE` bits are in `flags` of `struct trace_probe_event`.
- Tracepoint probes: live in `kernel/trace/trace_fprobe.c` and share its
  `process_fetch_insn()`.
- `error_log` instance: `__trace_probe_log_err()` passes a NULL trace array to
  `tracing_log_err()`, so the entry always goes to the top-level file.
- Unlogged errors: `__trace_probe_log_err()` returns without logging when
  `trace_probe_log_init()` has not run or its own `kzalloc()` fails.
