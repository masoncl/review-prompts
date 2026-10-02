- `drm_exec_lock_obj()` on `-EDEADLK`: only takes a reference and stores the
  object in `exec->contended`. It unlocks nothing.
- `drm_exec_cleanup()`, the loop condition: unlocks and puts everything.
- The slow lock: taken by `drm_exec_lock_contended()` at the start of the
  next `drm_exec_lock_obj()`, whichever object that call asks for.
- `drm_exec_retry`: a plain function-scope label reached by a plain `goto`.
  A second loop in one function needs `__label__ drm_exec_retry;` in its
  enclosing block, as in `drivers/gpu/drm/tests/drm_exec_test.c`.
- `drm_exec_retry_on_contention()`: compiles only lexically inside the loop,
  because it reads `__drm_exec_loop`. A helper returns `-EDEADLK` and the
  loop body calls the macro.
- **Unsafe usage**: a retry pass through the loop body that makes no lock
  call. Only `drm_exec_lock_contended()` clears a contended object from
  `exec->contended`, so `drm_exec_cleanup()` returns true forever.
  - Safe: every pass calls `drm_exec_lock_obj()` or `drm_exec_prepare_obj()`
    at least once, as `drm_gpuvm_exec_lock()` does.
  - Safe: `drm_exec_prepare_array()` with zero objects; it calls
    `drm_exec_lock_contended()` itself.
- `drm_exec_retry()`: restarts the loop unconditionally. It warns unless
  `exec->contended` is `DRM_EXEC_DUMMY`, so the caller must run
  `drm_exec_fini()` and `drm_exec_init()` first.
