# Scope-Based Cleanup and Guards

## Main structures

### Objects and how they relate

- `__free()` and classes: two separate mechanisms on top of `__cleanup()`.
  `DEFINE_FREE()` generates only `__free_##_name()`; it does not use
  `DEFINE_CLASS()` and creates no type, constructor or destructor.
- A class is a naming convention: `CLASS()` pastes `class_##_name##_t`,
  `class_##_name##_constructor` and `class_##_name##_destructor`, whoever
  defined them.
- `DEFINE_GUARD()`: the only guard definer that calls `DEFINE_CLASS()`.
  `DEFINE_LOCK_GUARD_0()` and `DEFINE_LOCK_GUARD_1()` generate the same
  names: type and destructor through `__DEFINE_UNLOCK_GUARD()`, constructor
  through `__DEFINE_LOCK_GUARD_0()` or `__DEFINE_LOCK_GUARD_1()`.
- There is no DEFINE_LOCK_GUARD_N here. `DEFINE_LOCK_GUARD_2()` exists, but
  only in `kernel/sched/sched.h`.
- Conditional guard instance from `DEFINE_GUARD_COND()` or
  `DEFINE_LOCK_GUARD_1_COND()`: has the base class's type and no extra
  "acquired" field. Failure is stored in the lock pointer as `ERR_PTR(_RET)`:
  NULL for a failed trylock, an error pointer for the forms that return an
  errno.
- `ACQUIRE()`: exactly `CLASS()`, so a named instance.
- Macros that add `class_##_name##_lock_ptr()` and
  `class_##_name##_is_conditional` to an existing class:

  | Macro | Use when |
  |---|---|
  | `DEFINE_CLASS_IS_GUARD()` | instance is a pointer, class is not conditional |
  | `DEFINE_CLASS_IS_COND_GUARD()` | instance is a pointer, NULL or error pointer means not acquired; for example `lock_timer` in `kernel/time/posix-timers.c` |
  | `DEFINE_CLASS_IS_UNCONDITIONAL()` | instance is not a lock pointer; for example `sched_change` in `kernel/sched/sched.h` |

- Context-analysis alias: for lock classes that follow
  `DECLARE_LOCK_GUARD_1_ATTRS()` with a `#define` of the constructor name to
  `WITH_LOCK_GUARD_1_ATTRS()`, for example
  `#define class_mutex_constructor(_T) WITH_LOCK_GUARD_1_ATTRS(mutex, _T)` in
  `include/linux/mutex.h`, the constructor is a macro.
  - One `guard()`, `CLASS()` or `scoped_guard()` then declares two
    `__cleanup()` variables: the instance, and a pointer alias whose cleanup
    `__class_##_name##_cleanup_ctx()` has an empty body.
- `scoped_seqlock_read()` in `include/linux/seqlock.h`: not a class; it puts
  `__cleanup()` directly on a `struct ss_tmp`. Its `for` loop is a retry
  loop, so the body can run a second time, unlike `scoped_guard()`.
- There is no `DEFINE_FREE()` and no class named fdput; `fdput()` is the
  destructor expression of the classes `fd` and `fd_raw` in
  `include/linux/file.h`.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| Documentation | `Documentation/core-api/cleanup.rst` | renders only the `DOC: scope-based cleanup helpers` block; the per-macro comments in `include/linux/cleanup.h` are plain comments, read them in the header |
| Compiler attribute | `include/linux/compiler_attributes.h` | defines `__cleanup()`; `include/linux/compiler-clang.h` does not redefine it |
| Slab wrappers | `include/linux/slab.h` | `kfree`, `kvfree`, `kvfree_atomic` skip `IS_ERR_OR_NULL()` pointers; `kfree_sensitive` skips only NULL |
| Mutex guards | `include/linux/mutex.h` | besides `mutex_try` and `mutex_intr` there are `mutex_kill` and `mutex_init` |
| Read-write semaphore guards | `include/linux/rwsem.h` | conditional forms are `rwsem_read_try`, `rwsem_read_intr`, `rwsem_write_try`, `rwsem_write_kill`; no killable read, no interruptible write |
| SRCU and tasks-trace RCU guards | `include/linux/srcu.h`, `include/linux/rcupdate_trace.h` | `srcu` and its fast forms; `rcu_tasks_trace` |
| Preemption guards | `include/linux/preempt.h` | `preempt` and `preempt_notrace` only |
| Migration guard | `include/linux/sched.h` | `migrate` is at the end of this file, not in `include/linux/preempt.h`, which holds only the `migrate_disable()` comment |
| Script that checks a declaration | `scripts/checkpatch.pl` | `ERROR()` of type `UNINITIALIZED_PTR_WITH_FREE`; matches a pointer declared with `__free()` and followed directly by `,` or `;`; explained in `Documentation/dev-tools/checkpatch.rst` |

**Macro families**

| Family | For | Defines a member | Uses a member |
|---|---|---|---|
| Free, giving ownership away | stop `__free()` from freeing | none | `no_free_ptr()`, `return_ptr()`, `retain_and_null_ptr()`; `take_fd()` is not one of them: it is in `include/linux/file.h` and resets an int for `CLASS(get_unused_fd)` |
| Class | constructor and destructor for a named variable | `DEFINE_CLASS()`; `EXTEND_CLASS()`; `EXTEND_CLASS_COND()`, whose destructor returns without calling the base destructor when the condition holds | `CLASS()`; `CLASS_INIT()`, which takes an initialiser expression instead of calling the constructor; `scoped_class()`, bound to the next statement |
| Class markers | let a `DEFINE_CLASS()` class work with `scoped_guard()` | `DEFINE_CLASS_IS_GUARD()` and `DEFINE_CLASS_IS_COND_GUARD()` for a class whose value is a pointer; `DEFINE_CLASS_IS_UNCONDITIONAL()` for a class that always counts as acquired | `scoped_guard()`; `scoped_cond_guard()`, of the three markers, is for `DEFINE_CLASS_IS_COND_GUARD()` only, its failure branch holds `BUILD_BUG_ON(!__is_cond_ptr(_name))`; `DEFINE_CLASS_IS_UNCONDITIONAL()` gives nothing for `ACQUIRE_ERR()` to call |
| Conditional guard | lock that can fail | `DEFINE_GUARD_COND()`, three arguments or four; the fourth is the success test on `_RET` | `scoped_cond_guard()`; `scoped_guard()`, body skipped on failure; `ACQUIRE()` with `ACQUIRE_ERR()` |
| Lock guard | guard held in a struct with a `lock` member | `DEFINE_LOCK_GUARD_1()`: constructor takes one lock pointer; `DEFINE_LOCK_GUARD_0()`: constructor takes nothing; both take extra members such as `flags`; `DEFINE_LOCK_GUARD_1_COND()` is the only conditional form, there is none for `DEFINE_LOCK_GUARD_0()` | `guard()`, `scoped_guard()`, `scoped_cond_guard()`, `ACQUIRE()` |
| Context-analysis attributes | show the compiler what a lock guard acquires and releases | `DECLARE_LOCK_GUARD_0_ATTRS()`; `DECLARE_LOCK_GUARD_1_ATTRS()`, placed after the lock guard definer | for the `_1` form the lock's header defines the constructor name as a macro, as in `#define class_mutex_constructor(_T) WITH_LOCK_GUARD_1_ATTRS(mutex, _T)` in `include/linux/mutex.h`, so `guard(mutex)()` declares a second hidden variable |

## Freeing a variable

**Generated cleanup function**

- `DEFINE_FREE()` in `include/linux/cleanup.h`: the generated function is
  `static __always_inline`, not plain `inline`.

**Types other than pointers**

- `btrfs_release_path` in `fs/btrfs/ctree.h`: a `DEFINE_FREE()` whose type is
  `struct btrfs_path`, not a pointer; used through
  `BTRFS_PATH_AUTO_RELEASE()`.
- `_T` for a struct type: a copy of the whole struct; `btrfs_release_path(&_T)`
  is given the address of the copy, not of the variable.
- `include/linux/file.h`: the `int` and `struct fd` cases are `DEFINE_CLASS()`
  (`get_unused_fd`, `fd`), not `DEFINE_FREE()`; the only `DEFINE_FREE()` there
  is `fput`.
- `__free_path_put` in `include/linux/path.h`: written by hand as
  `#define __free_path_put path_put`, so `path_put()` gets the address of the
  variable, with no copy and no test.
- `struct path` under `__free(path_put)`: must be initialised, as in
  `struct path path __free(path_put) = {};`.

**Scope exits**

- `goto` forward past the declaration to a label inside the variable's scope:
  where the compiler accepts the jump, the cleanup function still runs at
  scope exit, on a variable that was never initialised; Clang rejects the jump
  (see "Goto and cleanup in one function").

**Slab wrappers**

- `include/linux/slab.h` defines four wrappers: `kfree`, `kvfree`,
  `kvfree_atomic` and `kfree_sensitive`.
- `kmem_cache_destroy()`: has no `DEFINE_FREE()` wrapper in this tree.

| Wrapper | Test | Not released at scope exit |
|---|---|---|
| `kfree` | `if (!IS_ERR_OR_NULL(_T)) kfree(_T)` | NULL, error pointer |
| `kvfree` | `if (!IS_ERR_OR_NULL(_T)) kvfree(_T)` | NULL, error pointer |
| `kvfree_atomic` | `if (!IS_ERR_OR_NULL(_T)) kvfree_atomic(_T)` | NULL, error pointer |
| `kfree_sensitive` | `if (_T) kfree_sensitive(_T)` | NULL only |

- `kfree_sensitive` holding an error pointer: `kfree_sensitive()` in
  `mm/slab_common.c` passes it to `ksize()` and `kfree()`, whose pointer test
  is `ZERO_OR_NULL_PTR()`, not `IS_ERR()`.

**Common wrappers elsewhere**

- Tests in use: `if (_T)`, `if (!IS_ERR_OR_NULL(_T))`, `if (!IS_ERR(_T))`, and
  no test.
- `_T >= 0`: no `DEFINE_FREE()` uses it; it is the test in
  `DEFINE_CLASS(get_unused_fd, ...)` in `include/linux/file.h`.
- `if (!IS_ERR(_T))` wrappers: `mntput` and `mnt_ns_release` in
  `fs/namespace.c`, `x509_free_certificate` in
  `crypto/asymmetric_keys/x509_parser.h`; each release function tests NULL
  itself.
- `fwnode_handle` in `include/linux/property.h`: no test in the wrapper;
  `fwnode_handle_put()` skips both NULL and error pointers through
  `fwnode_has_op()` in `include/linux/fwnode.h`.
- Wrapper with no test: what the release function accepts decides, for NULL and
  for error pointers alike; `release_firmware()` in
  `drivers/base/firmware_loader/main.c`, behind the `firmware` wrapper in
  `include/linux/firmware.h`, and `free_percpu()` test NULL only.
- `dput()`: has no `DEFINE_FREE()` wrapper in this tree.
- Finding a definition: search for `DEFINE_FREE(name,`; if nothing matches,
  search for `__free_name`, since some cleanup functions are written by hand.
- Hand-written cleanup functions: `__free_path_put` (see "Types other than
  pointers"), `__free_klistmount_free()` in `fs/namespace.c`,
  `__free_klistns_free()` in `kernel/nstree.c`; each gets the address of the
  variable and has no `_T`.

**Error pointers under a cleanup attribute**

- **Potentially unsafe usage**: initialising a `__free()` variable from a
  function that can return an error pointer.
  - Unsafe: when neither the wrapper nor the release function tests
    `IS_ERR()`, as with `kfree_sensitive`, whose wrapper tests only `if (_T)`;
    on the `IS_ERR()` early return `kfree_sensitive()` is called on the error
    pointer.
  - Safe: when the wrapper tests `IS_ERR_OR_NULL()`, as `kfree` does for
    `memdup_user()` in `snd_ctl_elem_read_user()` in `sound/core/control.c`.
  - Safe: when the wrapper tests `IS_ERR()`, as `mntput` does for `fc_mount()`
    in `do_new_mount_fc()` in `fs/namespace.c`.
  - Safe: when the wrapper has no test and the release function makes it, as
    `fwnode_has_op()` does for `fwnode_handle` in `usb_acpi_add_usb4_devlink()`
    in `drivers/usb/core/usb-acpi.c`.
- `_opp_set_availability()` in `drivers/opp/core.c`: initialises a
  `__free(put_opp)` variable with `ERR_PTR(-ENODEV)` on purpose; `put_opp`
  tests `IS_ERR_OR_NULL()`, so an error pointer is a valid "nothing held"
  value.
- `drivers/net/ethernet/intel/ice/ice_debugfs.c`: has no `__free(kfree)`
  variable; use the examples above.

**Declarations without an initialiser**

- `scripts/checkpatch.pl`: reports it as `ERROR`, type
  `UNINITIALIZED_PTR_WITH_FREE`, text "pointer '$1' with __free attribute
  should be initialized".
- What the check matches: one added line with `*`, an identifier,
  `__free(name)`, then `,` or `;`.
- Not matched: a non-pointer variable such as `struct path path
  __free(path_put);`.
- The check reads the declaration line only: it also reports a declaration
  that is assigned in the very next statement.
- GCC: `scripts/Makefile.warn` adds `-Wno-maybe-uninitialized` under
  `CONFIG_CC_IS_GCC` unless the build uses `W=2`.
- Clang: `scripts/Makefile.warn` and the top-level `Makefile` name no
  `uninitialized` warning flag for Clang; the `-Wno-maybe-uninitialized` in
  `scripts/Makefile.warn` is under `CONFIG_CC_IS_GCC` only.
- **Potentially unsafe usage**: declaring a `__free()` variable without an
  initialiser.
  - Unsafe: when a `return` or other scope exit can run between the
    declaration and the first assignment; the function generated by
    `DEFINE_FREE()` copies the variable on every exit and applies its test to
    an uninitialised value.
  - Safe: when the first assignment is reached before any exit from the
    scope, as with `buf` in `ovl_parse_layer()` in `fs/overlayfs/params.c`.

## Cleanup order and guard scope

**Guard lifetime**

- `return` expression at function level: evaluated before the unlock, so
  `return p->field;` reads under the lock; `snd_seq_timer_get_cur_tick()` in
  `sound/core/seq/seq_timer.c` relies on this.
- `guard()` under a `case` label: in-tree code braces the case body
  (`case X: {` then `guard()`), as `iio_dummy_read_raw()` in
  `drivers/iio/dummy/iio_simple_dummy.c` does; the lock is then held to the
  closing brace of that case.
- Conditional class under `guard()`: the variable is named by
  `__UNIQUE_ID(guard)`, so `ACQUIRE_ERR()` cannot test it, and the rest of the
  scope runs whether or not the lock was taken.
- Conditional class, form to use: `ACQUIRE()` followed by `ACQUIRE_ERR()`, or
  `scoped_cond_guard()`.

**Control flow inside a scoped guard**

- `__scoped_guard()` loop exit: the condition is evaluated once, before the
  body; the loop ends because the increment clause `({ goto _label; })` jumps
  to a `break`, not because the condition turns false.
- `scoped_class()` in `include/linux/cleanup.h`: same `for` / `if (0)` /
  `else` shape with an empty condition, so `break` and `continue` behave the
  same in it and in its wrappers, for example `scoped_with_creds()` in
  `include/linux/cred.h`.
- `break` inside `scoped_guard()`: used in-tree on purpose as "leave the
  guard early", for example `try_to_wake_up()` in `kernel/sched/core.c`.
- **Potentially unsafe usage**: `break` or `continue` in a `scoped_guard()`
  body that sits inside a loop.
  - Unsafe: when the `break` or `continue` binds to the `scoped_guard()`
    itself, not to a loop or `switch` nested in its body, and a statement
    between the end of the `scoped_guard()` body and the end of the enclosing
    loop body must not run for that case; it runs, without the lock.
  - Safe: `break` to leave only the guard, with a flag tested right after it,
    as `get_modules_for_addrs()` in `kernel/trace/bpf_trace.c` does with
    `skip_add` followed by `if (skip_add) continue;`.
  - Safe: `continue` when the only statement after the `scoped_guard()` in the
    loop body is one that may run anyway, as in `vmstat_shepherd()` in
    `mm/vmstat.c`, where only `cond_resched()` follows.

**Declaring at the point of initialisation**

- "Must be initialised": not stated as a requirement in
  `include/linux/cleanup.h`, whose DOC comment only recommends defining and
  assigning in one statement, for the unwind-order reason; the requirement is
  the `UNINITIALIZED_PTR_WITH_FREE` error in `scripts/checkpatch.pl`,
  described in `Documentation/dev-tools/checkpatch.rst`.
- `UNINITIALIZED_PTR_WITH_FREE`: matches only a pointer declared with
  `__free()` and no initialiser; `= NULL` at the top of a function passes it.
- `__free(...) = NULL` at the top of a function: present in-tree and correct
  where no later guard or cleanup variable depends on the order, for example
  `kmod_dup_request_exists_wait()` in `kernel/module/dups.c`, whose only lock
  is a `scoped_guard()` and whose `put_kmod_req()` needs no lock.

**Guard and resource declaration order**

| Case | In-tree code | What to see |
|---|---|---|
| release after unlock, lock inside the object | `cxl_add_to_region()` in `drivers/cxl/core/region.c` | `cxlrd` with `__free(put_cxl_root_decoder)` is declared before `guard(mutex)(&cxlrd->regions_lock)` |
| release after unlock, scoped lock | `cxl_mem_probe()` in `drivers/cxl/mem.c` | `parent_port` with `__free(put_cxl_port)`, then `scoped_guard(device, endpoint_parent)` |
| both orders in one function | `perf_pmu_register()` in `kernel/events/core.c` | `pmu` with `__free(pmu_unregister)`, then `guard(mutex)(&pmus_lock)`, then `CLASS(idr_alloc, pmu_type)` |

- `cxl_add_to_region()`: the last put reaches `cxl_root_decoder_release()` in
  `drivers/cxl/core/port.c`, which calls `mutex_destroy()` on `regions_lock`
  and `kfree()` on the decoder, so the put has to run after the unlock.
- `cxl_mem_probe()`: the `scoped_guard()` ends before the function does, so
  the lock is dropped before `parent_port` is put whatever the declaration
  order.
- `perf_pmu_register()`, release under the lock: the `CLASS(idr_alloc,
  pmu_type)` destructor calls `idr_remove()` on `pmu_idr` before `pmus_lock`
  is dropped; the `idr_cmpxchg()` and `idr_remove()` calls on `pmu_idr` in
  that file are under `pmus_lock` too.
- `perf_pmu_register()`, release after unlock: `perf_pmu_free()` runs after
  `pmus_lock` is dropped, as it does in `perf_pmu_unregister()`.
- Release under the lock with a `__free()` variable: shown by the corrected
  `init()` in the DOC comment of `include/linux/cleanup.h`, which is not
  compiled; the `perf_pmu_register()` case uses `CLASS()`.
- `__free()` after a `guard()` in-tree: for example `cxlr` in
  `cxl_add_to_region()`, a reference whose put does not need the lock.

**Converting lock calls to guards**

- `__free()` and `CLASS()` variables declared after the new `guard()`: their
  release now runs before the unlock, so a put or free that used to follow the
  unlock call now runs under the lock; `cxlr` in `cxl_add_to_region()` in
  `drivers/cxl/core/region.c` is put before `regions_lock` is dropped.
- A release that takes the same lock: must stay outside the guard;
  `tracepoint_user_put()` in `kernel/trace/trace_fprobe.c` takes
  `tracepoint_user_mutex` itself.
- `scoped_guard()` keeping the old hold time, in-tree: `perf_pmu_unregister()`
  in `kernel/events/core.c` wraps only the `pmu_idr` and list update, then
  calls `synchronize_srcu()` and `perf_pmu_free()` unlocked.
- `tracepoint_user_put()`: frees with `__tracepoint_user_free()` after its
  `scoped_guard()` has ended.

## Ownership transfer

**no_free_ptr and return_ptr**

- Ignored value, compile time: `no_free_ptr()` passes the value through
  `__must_check_fn()`, which is `static __always_inline __must_check` in
  `include/linux/cleanup.h`, so a `no_free_ptr(p);` statement draws the
  unused-result warning.
- DOC comment at the top of `include/linux/cleanup.h`: its `init()` example
  writes `no_free_ptr(obj);` as a bare statement; that is the form
  `__must_check_fn()` warns about, and the statement form in this tree is
  `retain_and_null_ptr()`.
- `(void)no_free_ptr(p)`: appears nowhere in this tree.
- NULL test in a `DEFINE_FREE()` expression: a convention, not enforced; after
  `no_free_ptr()` the cleanup still runs with NULL.

**Disarming with retain_and_null_ptr**

- `retain_and_null_ptr()`: defined in `include/linux/cleanup.h` as
  `((void)__get_and_null(p, NULL))`.
- Comment above it, first statement: only for an allocation that is handed in
  to another function and consumed by that function on success.
- Comment above it, second statement: after the call the variable is NULL and
  cannot be dereferenced.
- Comment's example: `ret = bar(f);` with `f` still armed, then
  `retain_and_null_ptr(f)` only under `if (!ret)`.
- Callee behaviour on failure: not stated in the comment; the variable is still
  armed on that path, so `__free()` frees the object and the callee must not
  have freed or kept it.

**Transfer to another owner**

- **Potentially unsafe usage**: `no_free_ptr()` in the argument list of a call
  that can return an error.
  - Unsafe: when the callee can return an error without freeing or keeping the
    object; the variable is already NULL, so the cleanup frees nothing and the
    object leaks.
  - Safe: when the callee releases the object on its own failure path, as
    `add_or_reset_cxl_resource()` does for `__cxl_parse_cfmws()` in
    `drivers/cxl/acpi.c`.
  - Safe: `devm_add_action_or_reset()`, which calls the action on failure
    (`__devm_add_action_or_reset()` in `include/linux/device/devres.h`), as in
    `devm_cxl_setup_fwctl()` in `drivers/cxl/core/features.c`.
  - Safe: when the callee returns `void`, as `auxiliary_set_drvdata()` in
    `mlx5ctl_probe()` in `drivers/fwctl/mlx5/main.c`.
  - Safe: pass the pointer armed and call `retain_and_null_ptr()` only on
    success, as `do_new_mount_fc()` in `fs/namespace.c` does; the comment above
    `retain_and_null_ptr()` defines this form.
- **Potentially unsafe usage**: disarming a `__free()` variable before the last
  failure return of the function.
  - Unsafe: when nothing releases the new owner on the later failure path; the
    object is then freed by nobody.
  - Safe: when the new owner is itself still armed, as in
    `__trace_uprobe_create()` in `kernel/trace/trace_uprobe.c`: `filename` is
    stored into `tu`, and `free_trace_uprobe()` frees `tu->filename`.
  - Safe: after the last failure return, as `msi_create_device_irq_domain()`
    in `kernel/irq/msi.c` does with `retain_and_null_ptr()`.
- Using the object after the disarm: take a plain pointer before it;
  `__cxl_parse_cfmws()` keeps `cxld` for its `dev_dbg()` after
  `no_free_ptr(cxlrd)`.
- Fd and file together: `fd_publish()` in `include/linux/file.h` calls
  `fd_install()`, then `retain_and_null_ptr()` on the file and `take_fd()` on
  the fd; `FD_ADD()` in the same file builds on `FD_PREPARE()` and
  `fd_publish()`.

## Guard classes

**Guard definition macros**

- `mutex`, `rwsem_read` and `rwsem_write` guards: defined with
  `DEFINE_LOCK_GUARD_1()` and no extra member, in `include/linux/mutex.h` and
  `include/linux/rwsem.h`; their expressions use `_T->lock`, and the class type
  is a struct, not the lock pointer.
- A guard that is to carry `DECLARE_LOCK_GUARD_1_ATTRS()`:
  `DEFINE_LOCK_GUARD_1()` even with no extra state.
  `DECLARE_LOCK_GUARD_1_ATTRS()` declares the constructor with a
  `lock_##_name##_t *` parameter, which conflicts with the by-value `_type _T`
  constructor of `DEFINE_GUARD()`.
- `DEFINE_GUARD()`: `_T` is the value passed to `guard()`, which may be an
  object that holds the lock; the `cooling_dev` guard in
  `include/linux/thermal.h` locks `&_T->lock`.
- `DEFINE_GUARD()`, `DEFINE_LOCK_GUARD_1()` and `DEFINE_LOCK_GUARD_0()`
  destructors: run `_unlock` unconditionally, with no NULL or error-pointer
  test.
- `__GUARD_IS_ERR()`: true for NULL and for error pointers; tested only in the
  destructor that `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`
  generate, which returns before the base destructor.
- A lock pointer that may be NULL: neither `DEFINE_GUARD()` nor
  `DEFINE_LOCK_GUARD_1()`; both constructors are `__nonnull_args(1)`.
  `DEFINE_CLASS()` plus `DEFINE_CLASS_IS_GUARD()`, with the NULL test written
  into both expressions, does it; see `nvdimm_bus` in `drivers/nvdimm/nd.h`.
- `DEFINE_LOCK_GUARD_0()`: `_T->lock` is a `void *` set to `(void*)1`, not NULL,
  so `class_##_name##_lock_ptr` returns non-NULL.
- `DEFINE_LOCK_GUARD_0()`: has no conditional form; the macros that add a
  conditional variant to a guard are `DEFINE_GUARD_COND()` and
  `DEFINE_LOCK_GUARD_1_COND()` only.
- Several extra members: one macro argument with the members separated by `;`,
  not `,`; see the `task_rq_lock` guard in `kernel/sched/sched.h`.

**Class macros and generated names**

- `lock_##_name##_t`: a fourth generated name. `DEFINE_CLASS()` makes it the
  class type; `__DEFINE_UNLOCK_GUARD()` makes it the lock type while the class
  type is the struct; `EXTEND_CLASS_COND()` copies it to the extended name.
- `class_##_name##_lock_ptr`, `class_##_name##_lock_err` and
  `class_##_name##_is_conditional`: not generated by `DEFINE_CLASS()`.
  `scoped_guard()` needs the first and third, `ACQUIRE_ERR()` the second.
- Macros that add those names to a `DEFINE_CLASS()` class:

| Macro | Conditional | Adds |
|---|---|---|
| `DEFINE_CLASS_IS_GUARD()` | no | lock pointer and error from the class value |
| `DEFINE_CLASS_IS_COND_GUARD()` | yes | the same |
| `DEFINE_CLASS_IS_UNCONDITIONAL()` | no | lock pointer always `(void *)1`; no `class_##_name##_lock_err` |

- `EXTEND_CLASS()`: is `EXTEND_CLASS_COND()` with condition `0`; used for a
  second constructor on a plain class, for example the `filename` classes in
  `include/linux/fs.h`.
- `_irq`, `_bh` and `_irqsave` guards: separate classes with their own
  definer, not extensions; for example `spinlock_irq` in
  `include/linux/spinlock.h` is a `DEFINE_LOCK_GUARD_1()`.
- `CLASS_INIT(_name, _var, _init_expr)`: in this tree. It initialises the
  variable from `_init_expr` and does not call the constructor, so the class
  needs only the type and the destructor.
- `CLASS_INIT()` user: `FD_PREPARE()` in `include/linux/file.h`, on a class
  whose typedef and destructor are hand-written and which has no constructor.
- `scoped_class(_name, var, args...)`: in this tree; the caller names the
  variable. `scoped_guard()` is not built on it; `__scoped_guard()` has its own
  loop.
- `scoped_class()` loop: has no condition, so the body runs once whatever the
  constructor returned, and the class needs none of the guard helper names.
  See `fs/overlayfs/dir.c`.
- Tags: `scripts/tags.sh` emits `class_` plus the name (plus the extension),
  with no `_t`, `_constructor` or `_destructor` suffix. Its patterns match the
  definer macro only at the start of a line.
- Tag for `DEFINE_FREE()`: `cleanup_` plus the name, although the generated
  function is `__free_##_name`.

**Initialisation guards**

- Defined in this tree, each as `DEFINE_LOCK_GUARD_1()` with an empty unlock
  expression; search for `DEFINE_LOCK_GUARD_1\(\w+_init`. For example
  `mutex_init` in `include/linux/mutex.h` and `spinlock_init` in
  `include/linux/spinlock.h`.
- Names that do not match the init function: for example `rwsem_init` calls
  `init_rwsem()`. `local_trylock_init` is a separate class from
  `local_lock_init`.
- `guard(mutex_init)(&m)`: the constructor calls `mutex_init()` on the lock, so
  the guard replaces the init call rather than accompanying it.
- Plain `mutex_init()`: carries no context-analysis annotation. The documented
  alternatives to the guard are `context_unsafe()` and `__context_unsafe()`.
- `scoped_guard(spinlock_init, &lock) { }`: limits the region in which the
  analysis treats the lock as held to the block; see `drivers/scsi/hosts.c`.
- Lockdep key under `CONFIG_DEBUG_LOCK_ALLOC`: `mutex_init()` expands its
  `static struct lock_class_key __key` inside the guard constructor. Every
  mutex initialised with `guard(mutex_init)` in one translation unit therefore
  shares one key, and the lockdep name is `_T->lock`.
- A direct `mutex_init()` call: gets one key per call site and the caller's
  expression as the name.

**Dependents of the header**

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

## Conditional guards

**Conditional guard names**

- Classes defined for the five bases (`include/linux/mutex.h`,
  `include/linux/rwsem.h`, `include/linux/spinlock.h`,
  `include/linux/device.h`):

  | Base | `_try` | `_intr` | `_kill` |
  |---|---|---|---|
  | `mutex` | `mutex_try` | `mutex_intr` | `mutex_kill` |
  | `rwsem_read` | `rwsem_read_try` | `rwsem_read_intr` | none |
  | `rwsem_write` | `rwsem_write_try` | none | `rwsem_write_kill` |
  | `spinlock` | `spinlock_try` | none | none |
  | `device` | none | `device_intr` | none |

- `mutex_kill`: exists, calls `mutex_lock_killable()`.
- `rwsem_read`: no `_kill` class, although `down_read_killable()` exists.
- `device`: no `_try` class, although `device_trylock()` exists.
- `_try` is not always a trylock: `pm_runtime_active_try` and
  `pm_runtime_active_auto_try` in `include/linux/pm_runtime.h` call
  `pm_runtime_get_active()`, which resumes the device, and use `_RET == 0`;
  failure is a negative errno, not 0.
- Other suffixes in this tree: `_try_enabled` (`include/linux/pm_runtime.h`),
  `_try_direct` (`include/linux/iio/iio.h`, bool, failure 0), `_ioctl`
  (`drivers/gpu/drm/xe/xe_pm.h`, success is `_RET >= 0`).
- Conditional classes with no suffix: for example `irqdesc_lock` in
  `kernel/irq/internals.h` and `lock_timer` in `kernel/time/posix-timers.c`;
  search for `__DEFINE_CLASS_IS_CONDITIONAL` and `DEFINE_CLASS_IS_COND_GUARD`.

**Conditional guard definition**

- `DEFINE_GUARD_COND_4()` and `DEFINE_LOCK_GUARD_1_COND_4()`: built on
  `EXTEND_CLASS_COND()`, not directly on `EXTEND_CLASS()`.
- Conditional class destructor: its own function,
  `class_##_name##ext##_destructor`; it returns when `__GUARD_IS_ERR()` is
  true and otherwise calls the base destructor.
- Conditional constructor: does not call the base constructor; it builds the
  instance and evaluates `_lock` into `int _RET` itself.
- Failure value: `ERR_PTR(_RET)`; NULL only when `_RET` is 0, as for a failed
  trylock.
- `_cond`: a separate fourth macro argument over `_RET`; `_lock` is the bare
  call and does not assign `_RET`.
- Conditional class made without these macros: gets no `__GUARD_IS_ERR()`
  test; the pointer is tested in the unlock expression of `irqdesc_lock` in
  `kernel/irq/internals.h`, and in `unlock_timer()`, which the unlock
  expression of `lock_timer` in `kernel/time/posix-timers.c` calls.
- **Unsafe usage**: a 4-argument definition whose `_cond` can be false while
  `_RET` is positive.
  - Unsafe: `ERR_PTR()` of a positive value fails `__GUARD_IS_ERR()`, so the
    instance counts as held and the destructor unlocks.
  - Safe: `_RET` on failure is 0 or a negative errno, as in
    `pm_runtime_active_try`, where `pm_runtime_get_active()` turns every
    non-negative result of `__pm_runtime_resume()` into 0.

**Conditional class under a plain guard**

- `guard()`: is `CLASS(_name, __UNIQUE_ID(guard))` and nothing else; it has no
  `BUILD_BUG_ON()` and does not read `__is_cond_ptr()`, so `guard(mutex_try)`
  compiles.
- `BUILD_BUG_ON()` on `__is_cond_ptr()`: only in `__scoped_cond_guard()`, and
  it tests for the opposite case, an unconditional class.
- Header text in `include/linux/cleanup.h`: `guard()` is "not recommended for
  conditional locks"; it names `ACQUIRE()` with `ACQUIRE_ERR()` as the form
  for conditional locks and states no prohibition.
- Context analysis annotation: `DECLARE_LOCK_GUARD_1_ATTRS()` gives the
  constructors of `mutex_try`, `mutex_intr`, `mutex_kill` and
  `spinlock_try` the same unconditional `__acquires(_T)` as the base class,
  not `__cond_acquires()`.
- In-tree use: no `guard()` on a `_try`, `_intr` or `_kill` class exists in
  this tree to cite as correct.

**Conditional class under a scoped guard**

- `__scoped_guard()` loop condition:
  `__guard_ptr(_name)(&scope) || !__is_cond_ptr(_name)`; on failure the body
  is never entered.
- `scoped_cond_guard()` on an unconditional class: the only check is
  `BUILD_BUG_ON(!__is_cond_ptr(_name))`, which sits inside the failure branch
  of `__scoped_cond_guard()`, `if (!__guard_ptr(_name)(&scope))`, which is a
  call to `class_##_name##_lock_ptr()`; `__compiletime_assert()` in
  `include/linux/compiler_types.h` reports it through a call to an error
  function, so it fires only where the compiler keeps that branch.
  `class_##_name##_lock_ptr()` from `DEFINE_CLASS_IS_UNCONDITIONAL()` always
  returns `(void *)1`.
- `scoped_irqdesc_get_and_lock()` and `scoped_irqdesc_get_and_buslock()` in
  `kernel/irq/internals.h`: are `scoped_guard()` on the conditional class
  `irqdesc_lock`, so their body is skipped when the descriptor lookup fails.
- **Potentially unsafe usage**: code after `scoped_guard()` on a conditional
  class.
  - Unsafe: when it reads a result that only the body sets, or touches the
    protected data.
  - Safe: every path through the body returns and the statement after
    returns the error, as `min_show()` in
    `drivers/input/mouse/elan_i2c_core.c` does with `return -EINTR`.
  - Safe: the result is preset to the failure value before the statement, as
    `ret = -EINVAL` in `__irq_apply_affinity_hint()` in
    `kernel/irq/manage.c`.
  - Safe: skipping is the intended outcome and nothing after depends on the
    body, as in `tsc200x_esd_work()` in
    `drivers/input/touchscreen/tsc200x-core.c`, which only re-arms the work.

**Named conditional acquisition**

- `ACQUIRE()` and `ACQUIRE_ERR()`: both defined in
  `include/linux/cleanup.h`.
- `ACQUIRE_ERR()` after a failed trylock: `-EBUSY`, set in
  `class_##_name##_lock_err()` from `__DEFINE_GUARD_LOCK_PTR()` when the held
  value is NULL.
- `ACQUIRE_ERR()` with the base class name: works for an instance of any
  conditional class of that base, because each
  `class_##_name##_ext##_lock_err()` forwards to the base one;
  `PM_RUNTIME_ACQUIRE_ERR()` in `include/linux/pm_runtime.h` passes
  `pm_runtime_active` for all four `PM_RUNTIME_ACQUIRE()` variants, two of
  which extend `pm_runtime_active_auto`, whose class type is also
  `struct device *`.
- Wrappers that hide the pair: `PM_RUNTIME_ACQUIRE()` with
  `PM_RUNTIME_ACQUIRE_ERR()`, and `IIO_DEV_ACQUIRE_DIRECT_MODE()` with
  `IIO_DEV_ACQUIRE_FAILED()` in `include/linux/iio/iio.h`.
- `IIO_DEV_ACQUIRE_FAILED()`: is `ACQUIRE_ERR()` on a bool `_try_direct`
  class, so it yields 0 or `-EBUSY`, not a bool.
- **Potentially unsafe usage**: `ACQUIRE()` with no `ACQUIRE_ERR()` test
  before the protected data is used.
  - Unsafe: when the class is conditional; the constructor may have stored
    NULL or an error pointer and nothing else reports it.
  - Safe: when the class is unconditional and `ACQUIRE()` is used only to
    name the instance, as `ttwu_runnable()` in `kernel/sched/core.c` does
    with `__task_rq_lock`, a `DEFINE_LOCK_GUARD_1()` class in
    `kernel/sched/sched.h`, to read `guard.rq`.
  - Safe: when `ACQUIRE_ERR()` is tested and the scope is left on non-zero,
    as `commit_show()` in `drivers/cxl/core/region.c` does.

## Goto and policy

**Documented position on goto**

- Wording in the DOC block of `include/linux/cleanup.h`: "the expectation is
  that usage of "goto" and cleanup helpers is never mixed in the same
  function"; it is stated as an expectation, not as a preference. The next
  sentence spells it out: for a given routine, convert all resources that need
  a `goto` cleanup to scope-based cleanup, or convert none of them.
- Stated reason: the benefit of the helpers is removal of `goto`, and `goto`
  "can jump between scopes". The text names no consequence (no mention of an
  uninitialised variable or of a destructor running on garbage).
- Reverse-declaration-order text: belongs to the earlier paragraphs, and
  argues against `__free(...) = NULL` at the top of a function; it is not the
  reason given for the `goto` rule.
- In-tree code that mixes both in one function, for example:
  `simple_util_parse_tdm_width_map()` in
  `sound/soc/generic/simple-card-utils.c`,
  `audio_graph2_link_c2c()` in `sound/soc/generic/audio-graph-card2.c`,
  `posixtimer_send_sigqueue()` in `kernel/signal.c`, `futex_unqueue()` in
  `kernel/futex/core.c`, `gpiochip_add_data_with_key()` in
  `drivers/gpio/gpiolib.c`.
- A mix alone is therefore not a defect in this tree; see "Goto and cleanup in
  one function" for which mixes break.
- The header's own macros expand to `goto`: `__scoped_guard()`,
  `__scoped_cond_guard()` and `__scoped_class()`.
- `__scoped_user_access()` in `include/linux/uaccess.h`: takes an error label
  as an argument, so its users combine a cleanup scope and `goto` by design.
- `scripts/checkpatch.pl`: its one cleanup check is
  `UNINITIALIZED_PTR_WITH_FREE` (a `__free()` pointer with no initialiser);
  it has no check for `goto` mixed with the helpers.

**Subsystem policy**

- `Documentation/process/maintainer-netdev.rst`, section "Using
  device-managed and cleanup.h constructs", is the only document under
  `Documentation/` (translations aside) that restricts the helpers.

| Construct | What the section says |
|---|---|
| all "auto-cleanup" APIs, `devm_` included | "not the preferred style of implementation, merely an acceptable one" |
| `guard()` | discouraged in any function longer than 20 lines |
| `scoped_guard()` | "considered more readable" |
| plain lock/unlock | "still (weakly) preferred" |
| `__free()` | usable when building APIs and helpers, "especially scoped iterators"; direct use in networking core and drivers discouraged |
| mid-function declarations | one sentence: "Similar guidance applies to declaring variables mid-function." |

- The section has no maintainer-approval exception.
- "Clean-up patches" section of the same file: lists conversions to `devm_`
  helpers among discouraged standalone clean-ups; it does not list
  conversions to cleanup.h constructs.
- Reverse-xmas-tree ordering: a separate section of the same file ("Local
  variable ordering"); the cleanup section does not refer to it.
- `Documentation/dev-tools/checkpatch.rst`, under
  `UNINITIALIZED_PTR_WITH_FREE`: says the opposite for `__free()` pointers,
  that the declarations-at-top rule "can be relaxed"; this and the DOC block in
  `include/linux/cleanup.h` conflict with the netdev sentence on mid-function
  declarations.
- `Documentation/RCU/checklist.rst` and
  `Documentation/hwmon/hwmon-kernel-api.rst`: present the `guard()` and
  `scoped_guard()` forms as available, with no restriction.

**Goto and cleanup in one function**

- **Unsafe usage**: a `goto` placed before a `__free()` or `guard()`
  declaration that targets a label inside that declaration's scope.
  - Safe: every exit before the declaration is a `return`, and `goto` appears
    only after it, as in `simple_util_parse_tdm_width_map()` in
    `sound/soc/generic/simple-card-utils.c` and
    `ieee80211_rx_mgmt_assoc_resp()` in `net/mac80211/mlme.c`; the comment in
    the former states the requirement.
  - Safe: `guard()` is the first statement and all `goto` follow it, as in
    `posixtimer_send_sigqueue()` in `kernel/signal.c`.
  - Safe: a backward `goto` to a label that follows the declaration, as
    `goto retry` in `futex_unqueue()` in `kernel/futex/core.c`; the guard is
    not re-taken.
  - Safe: the declaration sits in a nested block or is a `scoped_guard()`,
    and the labels are at function level, so a `goto` either skips the whole
    block or leaves it; `gpiochip_add_data_with_key()` in
    `drivers/gpio/gpiolib.c` does both with `scoped_guard()`.
- **Unsafe usage**: an `asm goto` inside a cleanup scope whose target label
  is outside that scope.
  - Safe: route it through a label local to the scope and leave with a plain
    C `goto`, as `unsafe_get_user()`, `unsafe_put_user()` and
    `__get_kernel_nofault()` in `include/linux/uaccess.h` do with
    `__label__ local_label` when the architecture defines
    `arch_unsafe_get_user` or `arch_get_kernel_nofault`; the comment above
    them defines the requirement and says Clang rejects the direct form while
    GCC silently emits buggy code.
  - Safe: a plain C `goto` out of a cleanup scope, which is how those
    wrappers themselves leave (`goto label`); the same comment says it "works
    correctly".
- `__scoped_user_access()` in `include/linux/uaccess.h`: its error label
  "must be placed outside the scope".
- `__free(...) = NULL` at the top of the function: not a requirement; it puts
  the declaration ahead of every `goto`, and `scripts/checkpatch.pl` accepts
  it, but the DOC block in `include/linux/cleanup.h` recommends against it
  because unwind order then follows declaration order, not acquisition order.
- Clang, forward jump over the declaration: the tree records it as a build
  failure, in comments in `simple_util_parse_tdm_width_map()` and
  `audio_graph2_link_c2c()` ("Clang doesn't allow to use "goto end" before
  calling __free(), because it bypasses the initialization").
- GCC, forward jump over the declaration: the tree has no statement that GCC
  rejects it, and no build flag names such a diagnostic; the string
  jump-misses-init appears nowhere in the tree, including
  `scripts/Makefile.warn`.
- Supported compilers and minimum versions: `scripts/min-tool-version.sh`.

## Model gaps

### Other mistakes models make

- Models take `mutex` and `rwsem_read` to be `DEFINE_GUARD()` classes. Here
  the variants of `mutex`, `rwsem_read` and `rwsem_write` are added with
  `DEFINE_LOCK_GUARD_1_COND()`; see `include/linux/mutex.h` and
  `include/linux/rwsem.h`.
- Models take `scoped_seqlock_read()` to be a one-pass scope. Its body runs
  again when `read_seqretry()` returns non-zero after the lockless pass; see
  `__scoped_seqlock_next()` in `include/linux/seqlock.h`.
- Models take a `goto` label next to a cleanup scope as a breach of the
  header's rule. `__scoped_user_access_begin()` in `include/linux/uaccess.h`,
  behind `scoped_user_read_access()` and its siblings, does `goto elbl` before
  the `__cleanup()` variable is declared.
