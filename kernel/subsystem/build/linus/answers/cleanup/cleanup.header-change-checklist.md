- `ACQUIRE_ERR()`: depends on `class_##_name##_lock_err` through
  `__guard_err()`, not on the lock-pointer helper.
- `__guard_ptr()` outside the header: `scoped_irqdesc` in
  `kernel/irq/internals.h` and `scoped_tty()` in `include/linux/tty_port.h`.
- Variable name `scope` of `__scoped_guard()` and `__scoped_cond_guard()`: used
  by name outside the header, by `scoped_irqdesc` and `scoped_tty()`, by
  `scoped_timer` in `kernel/time/posix-timers.c`, and directly in guard
  bodies, for example as `scope->flags` in `kernel/sched/core.c`.
- Hand-written `class_##_name##_lock_ptr` helpers: in
  `include/drm/gpu_scheduler.h`, `include/drm/ttm/ttm_bo.h` and
  `drivers/gpu/drm/xe/xe_validation.h`. These define
  `class_##_name##_is_conditional` as a `#define`, not as the `const bool` the
  header generates.
- Hand-written classes: `fd_prepare` in `include/linux/file.h` (typedef,
  destructor and `class_fd_prepare_lock_err()`), and `perf_ctx_lock` in
  `kernel/events/core.c`.
- Internal macros used outside the header: `__DEFINE_UNLOCK_GUARD()` and
  `__DEFINE_CLASS_IS_CONDITIONAL()` in `include/linux/tty_port.h` and
  `kernel/irq/internals.h`; `__DEFINE_UNLOCK_GUARD()` in `DEFINE_LOCK_GUARD_2()`
  in `kernel/sched/sched.h`.
- `lock_##_name##_t`: used by `DECLARE_LOCK_GUARD_1_ATTRS()` and by
  `DECLARE_LOCK_GUARD_2_ATTRS()` in `kernel/sched/sched.h`.
- To find the rest: search outside the header for
  `class_\w+_(t|constructor|destructor|lock_ptr|lock_err|is_conditional)`.
- Scripts: `scripts/tags.sh` has patterns keyed on the definer macro names;
  `scripts/checkpatch.pl` matches the `__free(` spelling.
- `tools/testing/shared/linux/cleanup.h`: includes the kernel header by
  relative path.
- Lock type for a new guard: declared with `context_lock_struct()` from
  `include/linux/compiler-context-analysis.h`; a lock with no struct uses
  `token_context_lock()`, as `RCU` does in `include/linux/rcupdate.h`.
- Guard declaration, for each class in this order:
  1. The definer: `DEFINE_LOCK_GUARD_1()` for the base class,
     `DEFINE_LOCK_GUARD_1_COND()` for an extended class such as `mutex_try`.
  2. `DECLARE_LOCK_GUARD_1_ATTRS()` with the acquire and release attributes.
  3. `#define` of the constructor name to `WITH_LOCK_GUARD_1_ATTRS()`, as
     `class_mutex_constructor` in `include/linux/mutex.h`.
- Order of step 3: after steps 1 and 2 for that class, because both spell the
  constructor name followed by `(`, which the macro would expand.
- `_T` in the acquire attribute: the constructor parameter, a pointer to the
  lock type.
- `_T` in the release attribute: a pointer to the alias variable that holds
  the lock pointer, so it is cast and dereferenced, as in
  `*(struct mutex **)_T`.
- Lock that is a member of the guarded object: both attributes name the
  member; see the `task_lock` guard in `include/linux/sched/task.h`.
- Guard with no lock argument: `DECLARE_LOCK_GUARD_0_ATTRS()` only, which puts
  the attributes on the constructor and destructor declarations. There is no
  WITH_LOCK_GUARD_0_ATTRS and no constructor `#define`; see the `rcu` guard in
  `include/linux/rcupdate.h`.
- `WITH_LOCK_GUARD_1_ATTRS()`: uses its argument twice, so the lock expression
  given to `guard()` is evaluated twice for a class with the override. This
  holds whether or not `WARN_CONTEXT_ANALYSIS` is defined.
- `WITH_LOCK_GUARD_1_ATTRS()`: adds a second declarator after the constructor
  call. It therefore relies on `CLASS()` ending in the bare constructor name
  inside a declaration.
