- **Potentially unsafe usage**: `goto` in a function that uses `guard()`.
  - Unsafe: when the `goto` is before the `guard()` and its label is after it
    in the same scope; the jump skips the constructor and the destructor
    still runs at scope exit.
  - Safe: when the `guard()` comes before every `goto`, as in
    `stat_seq_init()` in `kernel/trace/trace_stat.c`.
  - Safe: when the lock is taken with `scoped_guard()` or
    `scoped_cond_guard()` and the labels are outside its body, as in
    `input_register_device()`.
- `goto` and cleanup helpers: the comment in `include/linux/cleanup.h` states
  "never mixed" as an expectation; `scripts/checkpatch.pl` has no test for
  it.
- **Unsafe usage**: `guard()` with a conditional class (suffix such as
  `_try`, `_intr`, `_kill`); the result is not tested and the code runs
  without the lock.
  - Safe: `scoped_cond_guard()`, as in `input_register_device()`, or
    `ACQUIRE()` followed by a test of `ACQUIRE_ERR()`, as in
    `drivers/pci/tsm.c`; `guard()` is "not recommended for conditional locks"
    in `include/linux/cleanup.h`.
- **Potentially unsafe usage**: `scoped_guard()` with a conditional class.
  - Unsafe: when the code after the block assumes the body ran.
  - Safe: when the body returns and the code after the block is the failure
    path, as in `margining_eye_show()` in `drivers/thunderbolt/debugfs.c`.
  - Safe: when skipping the body is the intended result of a failed trylock
    and the code after the block is right either way, as in
    `tsc200x_esd_work()`.
- **Potentially unsafe usage**: `break` or `continue` inside
  `scoped_guard()` or `scoped_cond_guard()`.
  - Unsafe: when it is meant for an enclosing loop or `switch`; both only
    leave the guard, because the macro is a `for` loop.
  - Safe: when it is meant to leave the guard early, as in
    `try_to_wake_up()` and `get_modules_for_addrs()`.
- **Potentially unsafe usage**: a `__free()` variable declared `= NULL`
  before a `guard()` in the same scope.
  - Unsafe: when the cleanup function needs the lock; it runs after the
    unlock, since cleanup is in reverse order of declaration.
  - Safe: when the cleanup needs no lock, such as `kfree()` in
    `osnoise_cpus_read()`.
  - Safe: `guard()` first, then declare and initialise the `__free()`
    variable in one statement, as the comment in `include/linux/cleanup.h`
    shows.
- **Unsafe usage**: `guard()` directly under a `case` label without braces;
  `guard()` is a declaration and its scope would run over the later cases.
  - Safe: `case X: { guard(...)(...); ... }`, as in `adxl367_read_raw()`.
- **Unsafe usage**: a lock argument with side effects, for a class whose
  constructor is defined to `WITH_LOCK_GUARD_1_ATTRS()` (for example `mutex`
  and `spinlock`; search for the macro name); the macro evaluates the
  argument twice.
  - Safe: an address expression such as `&obj->lock`.
  - Safe: a getter without side effects, such as `pf_migration_mutex()` in
    `drivers/gpu/drm/xe/xe_sriov_packet.c`.
- Context analysis and conditional classes: where a conditional class has
  `DECLARE_LOCK_GUARD_1_ATTRS()`, its constructor is declared
  `__acquires(_T)` or `__acquires_shared(_T)`, not `__cond_acquires()`, so
  the compiler is told the lock is held even when acquisition failed; it does
  not replace the `ACQUIRE_ERR()` test.
- `return expr;` under a guard: `expr` is evaluated before the destructor
  runs; `return_ptr()` in `include/linux/cleanup.h` relies on this order.
