- Limit: `FGRAPH_ARRAY_SIZE` is `FGRAPH_INDEX_BITS`, which is 16.
- No free slot: `register_ftrace_graph()` returns `-ENOSPC`.
- Existing tasks get a shadow stack only when `ftrace_graph_active` becomes 1;
  later registrations only call `init_task_vars()`.
- `SHADOW_STACK_SIZE`: 4096 bytes whatever the page size, from the cache
  `fgraph_stack_cachep`, which `register_ftrace_graph()` creates on its first
  call.
- Shadow stack allocation failure fails registration only in
  `start_graph_tracing()`. `ftrace_graph_init_idle_task()` and
  `ftrace_graph_init_task()` return silently and leave `ret_stack` NULL; that
  task is then not traced.
- `ftrace_graph_exit_task()` is called from `free_task()` in `kernel/fork.c`,
  when the `struct task_struct` is freed.
