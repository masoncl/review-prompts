- Sparse: checks none of these; under `__CHECKER__` (and `__GENKSYMS__`)
  every annotation in `include/linux/compiler-context-analysis.h` is empty,
  and `__acquire()` and `__release()` are empty statements.
- Clang context analysis: the only tool in this tree that reads them, and
  only in a file that is opted in.
- Build without the analysis: the preprocessor discards the annotation
  arguments, so a wrong lock expression is not even parsed.
- `__cond_acquires()` and `__cond_acquires_shared()`: the first argument is
  pasted into a macro name and must be one of the tokens `true`, `false`,
  `nonzero`, `0`, `nonnull`, `NULL`; any other token breaks the build in
  every configuration.
- `__cond_acquires()` in use: `true` for trylock-style functions, `0` for
  errno-style ones such as `mutex_lock_interruptible()`.
- `__guarded_by()` and `__pt_guarded_by()`: accept several locks; reading
  under any one of them and writing under all of them is accepted, see
  `test_mutex_multiguard()` in `lib/test_context-analysis.c`.
- Function that needs the lock only on some paths: use
  `lockdep_assert_held()`, `lockdep_assert_held_write()` or
  `lockdep_assert_held_read()` in the body instead of `__must_hold()`; they
  expand to `__assume_ctx_lock()` or `__assume_shared_ctx_lock()`.
