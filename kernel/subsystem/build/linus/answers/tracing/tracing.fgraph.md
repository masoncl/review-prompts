- Non-zero from `entryfunc` does not guarantee a `retfunc` call:
  `__ftrace_return_to_handler()` takes `ftrace_test_recursion_trylock()` and
  skips every `retfunc` when it fails.
- **Unsafe usage**: a `retfunc` that dereferences `fgraph_retrieve_data()`
  without a NULL test. The return side calls `retfunc` for each bit in the
  saved bitmap, and `function_graph_enter_regs()` always sets bit 0, so the
  user in slot 0 can be called for a call its `entryfunc` rejected.
  - Safe: test for NULL and return, as `trace_graph_return()` in
    `kernel/trace/trace_functions_graph.c` does.
- `fgraph_reserve_data()` called twice in one `entryfunc`: the second call is
  not refused, and `fgraph_retrieve_data()` returns only the later
  reservation.
- `FGRAPH_MAX_DATA_SIZE`: `sizeof(long) * 32`; a larger request returns NULL.
- `fregs` in `retfunc`: NULL without `CONFIG_HAVE_FUNCTION_GRAPH_FREGS`. The
  return value is in `retval` of `struct ftrace_graph_ret`, which exists only
  with `CONFIG_FUNCTION_GRAPH_RETVAL`.
- `fregs` in `entryfunc`: NULL when the arch hook uses
  `function_graph_enter()`.
- `ftrace_graph_ret_addr()` matches a frame on `retp`, which must equal the
  `retp` the arch hook gave `function_graph_enter_regs()`. That is the stack
  slot on x86 and the frame pointer value on arm64.
- `idx` only sets where the search starts; `*idx` is a shadow stack offset,
  0 meaning the top. A fresh `idx` of 0 for a single lookup is valid, as
  `function_get_true_parent_ip()` in `kernel/trace/trace_functions.c` does.
- `ftrace_graph_ret_addr()` with a NULL `idx`, or with a `retp` that matches
  no frame: returns `ret` unchanged, also when it is `return_to_handler`.
- There is no HAVE_FUNCTION_GRAPH_RET_ADDR_PTR in this tree.
- x86 unwinders call it through `unwind_recover_ret_addr()` in
  `arch/x86/include/asm/unwind.h`.
