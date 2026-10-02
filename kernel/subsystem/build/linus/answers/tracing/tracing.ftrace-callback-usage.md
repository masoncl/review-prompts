- Preemption is disabled only by `trace_test_and_set_recursion()` in
  `include/linux/trace_recursion.h`, which `ftrace_ops_assist_func()`,
  `__ftrace_ops_list_func()` and `ftrace_test_recursion_trylock()` call. A
  trampoline that calls `ops->func` directly leaves preemption as it was.
- `ftrace_ops_assist_func()` and `__ftrace_ops_list_func()` use
  `TRACE_LIST_START`; `ftrace_test_recursion_trylock()` uses
  `TRACE_FTRACE_START`. The bits are separate, so a callback under the core's
  protection can still take its own trylock.
- One nested entry in the same context succeeds, through the transition bit.
  A callback that calls a traced function is re-entered once before the
  trylock returns -1; `trace_selftest_function_recursion()` in
  `kernel/trace/trace_selftest.c` accepts a count of 1 or 2.
- `CONFIG_FTRACE_VALIDATE_RCU_IS_WATCHING`: the trylock, and the core's own
  test, return -1 with a `WARN_ONCE()` when `rcu_is_watching()` is false.
- `FTRACE_OPS_FL_RCU` exists; in this tree only `samples/ftrace/ftrace-ops.c`
  sets it. `perf_ftrace_function_call()` in
  `kernel/trace/trace_event_perf.c` tests `rcu_is_watching()` itself.
- **Potentially unsafe usage**: calling a traceable function from a callback.
  - Unsafe: before recursion protection is held, on an ops without
    `FTRACE_OPS_FL_RECURSION`; this includes the callback itself when it is not
    `notrace` and its own filter covers it.
  - Safe: after `ftrace_test_recursion_trylock()` returned 0 or more, as
    `fprobe_ftrace_entry()` in `kernel/trace/fprobe.c` does.
  - Safe: the ops sets `FTRACE_OPS_FL_RECURSION`, as `test_rec_probe` in
    `kernel/trace/trace_selftest.c` does; `ftrace_ops_get_func()` then
    returns `ftrace_ops_assist_func()`.
- `kernel/trace/Makefile` removes `CC_FLAGS_FTRACE` for the directory, and adds
  it back for the files listed under `CONFIG_FUNCTION_SELF_TRACING`; code in
  those files is traceable.
