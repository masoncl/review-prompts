- Header side: `DECLARE_TRACEPOINT()` plus `tracepoint_enabled()`, then a call
  to a wrapper function defined in a `.c` file that includes the trace header;
  see `include/linux/mmap_lock.h` and `mm/mmap_lock.c`.
- `DECLARE_TRACEPOINT()`: defined unconditionally as the `extern`
  declaration; only `tracepoint_enabled()` becomes `false` without
  `CONFIG_TRACEPOINTS`.
- Bare tracepoint: pass the name with its `_tp` suffix, as
  `tracepoint_enabled(sched_set_state_tp)` in `include/linux/sched.h`.
- Tracepoint or wrapper built only under another option:
  `tracepoint_enabled()` still references `__tracepoint_` plus the name
  whenever `CONFIG_TRACEPOINTS` is set, so the header needs its own gate; see
  `page_ref_tracepoint_active()` in `include/linux/page_ref.h` (tracepoint
  defined only under `CONFIG_DEBUG_PAGE_REF`) and the `IS_ENABLED()` test in
  `queued_spin_unlock()` in `include/asm-generic/qspinlock.h` (wrapper defined
  only under `CONFIG_QUEUED_SPINLOCKS_TRACE_CONTENDED_RELEASE`).
- Inline usable from modules: export both the wrapper and the tracepoint;
  `net/9p/client.c` uses `EXPORT_TRACEPOINT_SYMBOL(9p_fid_ref)` for the test
  and `EXPORT_SYMBOL(do_trace_9p_fid_get)` for the wrapper.
- Wrapper body: either the normal trace function, which tests the key again
  (`do_trace_write_msr()` in `arch/x86/lib/msr.c`), or the `trace_call__`
  form, which does not (`__trace_set_current_state()`).
- Wrapper that uses the `trace_call__` form: the wrapper no longer tests the
  key, so a caller that skips the enabled test enters the read section on
  every call that passes `cond`.
