# What the cleanup measurement found

Three models were asked the 43 questions in `cleanup-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C had the least rewritten,
reader A was close behind, and reader B had two thirds of every answer
replaced. The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

The header is young and still growing. Readers A and C describe the mechanism
correctly (what `__free()` expands to, reverse order of definition, the return
expression being evaluated before the cleanups run, `scoped_guard()` being a
loop) and are wrong about the newest macros, about which header holds which
guard, and about nearly every in-tree example they offer. Reader B describes
the header as it was several releases ago and is wrong in ways that change a
verdict.

## What all three readers got wrong

- **Which definer the mutex guard uses, and which classes exist.**
  `include/linux/mutex.h` uses `DEFINE_LOCK_GUARD_1()`, not `DEFINE_GUARD()`.
  Every reader left out `mutex_kill`, and reader C said it does not exist.
  The `migrate` guard is in `include/linux/sched.h`, not
  `include/linux/preempt.h`. Read-write locks have plain, `_irq` and
  `_irqsave` guards in `include/linux/spinlock.h` and no `_bh` or `_try`
  forms. Read-write semaphores have `rwsem_read_try`, `rwsem_read_intr`,
  `rwsem_write_try` and `rwsem_write_kill` and nothing else. All four
  spinlock forms and all four raw spinlock forms have a `_try` class.
- **The slab header has four wrappers.** `kfree`, `kvfree` and `kvfree_atomic`
  test `!IS_ERR_OR_NULL(_T)`; `kfree_sensitive` tests `if (_T)`. Readers A and
  C missed `kvfree_atomic`. Reader B listed two, both as `if (_T)`; see below.
- **A checkpatch rule exists.** Asked where the rules are, every reader said
  no script enforces anything. `scripts/checkpatch.pl` reports a `__free()`
  pointer declared without an initialiser as the error
  `UNINITIALIZED_PTR_WITH_FREE`; it matches pointer declarations only. GCC's
  own warning is switched off in `scripts/Makefile.warn` except under W=2.
- **A NULL lock argument.** All three said the guard destructors skip a NULL
  lock. Only the destructors of conditional classes test, with
  `__GUARD_IS_ERR()`; `DEFINE_CLASS()` and `__DEFINE_UNLOCK_GUARD()` run the
  unlock expression unconditionally. The unconditional constructors carry
  `__nonnull_args(1)`, so a NULL the compiler can see warns. The conditional
  constructors evaluate the lock expression before they look at `_T`.
- **A non-pointer type under `DEFINE_FREE()`.** None could name one.
  `fs/btrfs/ctree.h` has `DEFINE_FREE(btrfs_release_path, struct btrfs_path,
  btrfs_release_path(&_T))`, used through `BTRFS_PATH_AUTO_RELEASE()`.
- **How conditional classes are built.** `DEFINE_GUARD_COND()` and
  `DEFINE_LOCK_GUARD_1_COND()` go through `EXTEND_CLASS_COND()`, which
  generates a new destructor that returns early on `__GUARD_IS_ERR()` and
  otherwise calls the base one. Readers A and C said `EXTEND_CLASS()` and the
  base destructor; reader B said failure is stored as NULL. It is stored as
  `ERR_PTR(_RET)`, which is NULL only for a trylock.
- **A declaration under a `case` label.** The tree builds with `-std=gnu11`
  and still supports GCC 8.1. GCC 8 to 10 reject a declaration directly after
  a label; GCC 11 and later accept it and say nothing about a later label
  jumping past it; Clang rejects that jump. Reader A said GCC accepts it
  silently, reader B that it compiles everywhere, reader C said "older GCC".
- **In-tree examples.** Almost every function a reader named was wrong:
  `fd_install(fd, no_free_ptr(file))` placed in `fs/namespace.c` (the only
  one is in `drivers/xen/gntdev-dmabuf.c`), `sched_getaffinity()` for
  returning a field under a guard, `msi_create_device_irq_domain()` for the
  conditional `retain_and_null_ptr()` pattern, `CLASS(hb, hb)` in the futex
  code. Examples that do hold: `do_new_mount_fc()` in `fs/namespace.c`
  (`retain_and_null_ptr()` only when `do_add_mount()` succeeds), `acct_on()`
  in `kernel/acct.c`, `gpiod_export()` in `drivers/gpio/gpiolib-sysfs.c`
  (`__free(kfree)`, `guard(mutex)` and a chain of error labels in one
  function), `try_to_wake_up()` (`guard(preempt)` with `goto out` in the same
  scope), `snd_timer_resolution()` in `sound/core/timer.c` (reference
  declared before the spinlock guard so that it is dropped after the unlock).
- **What a change to the header must keep working.**
  `tools/testing/shared/linux/cleanup.h` includes the kernel header, and
  `tools/testing/selftests/bpf/prog_tests/socket_helpers.h` copies
  `__get_and_null()`; readers said there is no copy or did not know.
  `__get_and_null()` is also used by `take_fd()` in `include/linux/file.h` and
  `take_idr_id()` in `include/linux/idr.h`. Classes outside the header set the
  conditional flag themselves: `__DEFINE_CLASS_IS_CONDITIONAL()` in
  `kernel/irq/internals.h` and `include/linux/tty_port.h`,
  `DEFINE_CLASS_IS_COND_GUARD()` in `kernel/time/posix-timers.c`,
  `DEFINE_CLASS_IS_UNCONDITIONAL()` in `kernel/sched/sched.h`,
  `DEFINE_CLASS_IS_GUARD()` in `drivers/nvdimm/nd.h`, and hand-written
  defines in the DRM headers. The header has no sparse lock annotations, only
  `__force` casts; `__acquires()` and `__releases()` are context-analysis
  attributes in this tree. `scripts/tags.sh` has a pattern for each definer.

## What readers A and B got wrong

- **Guards that only initialise.** `mutex_init`, `spinlock_init`,
  `raw_spinlock_init`, `rwlock_init`, `rwsem_init`, `seqlock_init`,
  `local_lock_init` and `local_trylock_init` are lock guard classes whose lock
  expression is the init function and whose unlock is empty.
  `guard(spinlock_init)(&d->lock)` holds nothing; it lets context analysis
  accept the initialisation of guarded members. Neither reader was sure they
  exist.
- **`CLASS_INIT()`** was not recognised by either.
- **Context analysis.** `DECLARE_LOCK_GUARD_1_ATTRS()` puts the release
  attribute on an empty `__class_<name>_cleanup_ctx()` helper, not on the
  destructor, and `WITH_LOCK_GUARD_1_ATTRS()` attaches that helper to an alias
  variable. A new lock guard needs both lines and a redefinition of its
  constructor, once for each conditional class as well.
- **The netdev policy.** `Documentation/process/maintainer-netdev.rst`
  discourages `guard()` in a function longer than 20 lines, calls
  `scoped_guard()` more readable, still weakly prefers plain lock and unlock,
  and discourages direct `__free()` in networking core and drivers. Reader B
  said no subsystem restricts the helpers; reader A left out its opening
  statement that every auto-cleanup API is "merely an acceptable" style;
  reader C had it nearly right but said netdev prefers `scoped_guard()`.
- **What the jump over a declaration does.** Reader A quoted Clang's
  secondary note as the error; reader B said both compilers accept the jump
  silently. Clang refuses it ("cannot jump from this goto statement to its
  label"), GCC accepts it, and nothing in the kernel's build flags makes GCC
  say anything. Two comments in `sound/soc/generic/` record the Clang
  behaviour.

## What reader B got wrong as well

These are the ones that would change a verdict.

- **`__free(kfree)` and `__free(kvfree)` called NULL-only.** They skip error
  pointers. Reader B would report a correct `memdup_user()` into
  `__free(kfree)` followed by an `IS_ERR()` return.
- **The generated function has a NULL test of its own.** It does not:
  `DEFINE_FREE()` expands to `_type _T = *(_type *)p; _free;` and any test is
  part of the wrapper's expression. `firmware`, `free_page`, `free_percpu`,
  `fwnode_handle` and `btrfs_free_path` have none and rely on the release
  function.
- **The header's position on `goto`, backwards.** Reader B said the header
  allows `goto` beside guards. The DOC comment expects the two never to be
  mixed in one function: convert every resource or none.
- **Why the header says to declare at the point of initialisation.** Reader B
  gave uninitialised garbage as the reason. The header's reason is order:
  `= NULL` at the top is defined before a later `guard()`, so its cleanup
  runs after the unlock.
- **Macros denied or doubted that exist**: `retain_and_null_ptr()`,
  `ACQUIRE()`, `ACQUIRE_ERR()`, `scoped_class()`.
- **`ACQUIRE_ERR()` takes the address of the variable**, gives exactly
  `-EBUSY` for a failed trylock and the lock function's own error otherwise.
- **`scoped_cond_guard()` on an unconditional class** is a `BUILD_BUG_ON()`,
  not a synonym for `scoped_guard()`.
- **`device_try` does not exist**; the device lock has `device_intr` only.
- **Wrapper names.** `device_node`, `fwnode_handle`, `firmware` and `bitmap`
  are the names, not the release functions' names; `put_cred` tests
  `!IS_ERR_OR_NULL`; there is no put_page wrapper.
- **`__free(path_put)`** is not a `DEFINE_FREE()`: `include/linux/path.h`
  defines `__free_path_put` as `path_put`, so the function gets a pointer to
  the variable, nothing tests it, and the variable has to be initialised.
- **Scoped iterators.** `for_each_child_of_node_scoped()` is its own `for`
  loop; `of_get_next_child()` drops the previous reference and the attribute
  only acts when the loop is left. The header quotes the GCC documentation for
  the unwind order, not the C++ standard. `Documentation/process/coding-style.rst`
  does not mention the helpers.

## What the readers already knew

Readers A and C, and reader B in outline: cleanups run in reverse order of
definition, inner scopes first; the return expression is evaluated before any
cleanup runs, so returning a field under a guard is safe and a plain `return p`
of a `__free()` pointer hands back freed memory; `return_ptr()` and
`no_free_ptr()` and the `__must_check` trick; a guard lasts to the end of the
enclosing braces; converting lock and unlock calls to `guard()` stretches the
critical section over everything after the old unlock; `break` and `continue`
inside `scoped_guard()` leave the guard, not an enclosing loop; `guard()` on a
conditional class carries on without the lock and nothing checks (A and C);
`scoped_guard()` on one skips its body silently (A and C); the table of common
wrappers outside the slab header (reader C had every row right, reader A all
but two); the
difference between `DEFINE_GUARD()`, `DEFINE_LOCK_GUARD_1()` and
`DEFINE_LOCK_GUARD_0()`; what a conversion from `goto` has to preserve (A).

That list is about two thirds of the hand-written guide.

## Where the hand-written guide is stale

What `cleanup.md` quotes holds on this tree: the `kfree` and `kfree_sensitive`
tests, the unwind order, the scope example, the three transfer macros, the
header's paragraph on `goto`. What is wrong with it is what it makes of them
and what it leaves out.

- It turns the header's "expectation" about `goto` into a rule to report every
  function that has both a label and a `__free()` or `guard()`. Correct
  in-tree code has both: `gpiod_export()`, `try_to_wake_up()`,
  `futex_lock_pi()`. What is unsafe is narrower: a forward jump over a
  declaration to a label inside its scope, which GCC compiles into a cleanup of
  an uninitialised variable and Clang refuses, and a label that still releases
  by hand what the attribute will release as well.
- It attributes the unwind-order sentence to the header; the header quotes the
  GCC documentation.
- It lists "using `no_free_ptr()` before early return to inhibit cleanup" as a
  mitigation. `no_free_ptr()` must have its value used; discarding ownership
  is what `retain_and_null_ptr()` is for, and the comment above it limits that
  to a callee that consumed the pointer.
- Of the slab wrappers it has two of four, and it gives no way into the rest:
  which wrappers elsewhere test for an error pointer (`fput`, `putname`,
  `put_cred`, `argv_free`) and which test nothing.
- It says nothing about conditional guards, `ACQUIRE()`, `scoped_cond_guard()`,
  the `_init` guards, `scoped_guard()` being a loop, the checkpatch rule, the
  netdev policy or context analysis.

## What was left out of the build set, and why

The hand-written guide is 934 words, so the build set has 21 questions.

- `cleanup.unwind-order`, `cleanup.guard-scope`, `cleanup.return-usage`,
  `cleanup.no-free-ptr`, `cleanup.widened-critical-section`,
  `cleanup.when-cleanup-runs`, `cleanup.guard-definers`: readers A and C
  answer them. What reader B lacks in them comes back through
  `cleanup.return-expression-order`, `cleanup.declare-at-init`,
  `cleanup.lock-resource-order` and `cleanup.conversion-checklist`.
- `cleanup.guard-names`: a table of 120 words that the readers mostly know.
  The rows they had wrong (`mutex_kill`, `migrate`, no rwlock `_bh`) are
  covered by `cleanup.core-files` and `cleanup.cond-guard-names`.
- `cleanup.macro-families`, `cleanup.class-expansion`,
  `cleanup.cond-guard-definition`, `cleanup.free-expansion`: how the macros
  are built. The header is one file and the reader can open it; the parts
  that change a review are asked by the questions on conditional locks and on
  wrappers.
- `cleanup.docs`: its content is split between `cleanup.core-files`,
  `cleanup.uninitialised-usage` and `cleanup.subsystem-policy`.
- `cleanup.null-lock-argument`: every reader was wrong, but it is narrow, and
  a NULL the compiler can see already warns.
- `cleanup.case-label-usage`: two readers wrong, but the mistake fails the
  build on one compiler or the other.
- `cleanup.context-analysis-hooks`: two readers wrong; only someone adding a
  guard for a new lock type needs it, and `cleanup.header-change-checklist`
  names the macros.
- `cleanup.mixed-unwind-usage`: folded into `cleanup.goto-usage` and
  `cleanup.conversion-checklist`.
- `cleanup.reassignment-usage`, `cleanup.null-test-reason`,
  `cleanup.free-without-define`, `cleanup.non-pointer-transfer`,
  `cleanup.scoped-iterators`: real, relevance 2 or 3, no room. The scoped
  iterators belong with the device tree material.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           64        25%     13      8   6.12 to 6.19
reader B           85        68%      0     39   6.12 to 6.14
reader C           66        14%     27      3   6.12 to 7.0

question                              reader A      reader B      reader C
cleanup.core-files                    18% ( 7)      86% (12)      26% ( 9)
cleanup.docs                          32% ( 2)      87% ( 3)      41% ( 2)
cleanup.macro-families                12% ( 2)      59% ( 3)      13% ( 2)
cleanup.free-expansion                32% ( 2)      64% ( 2)      38% ( 1)
cleanup.free-without-define            0% ( 0)      88% ( 1)       0% ( 0)
cleanup.null-test-reason              17% ( 1)      86% ( 1)       0% ( 0)
cleanup.when-cleanup-runs             26% ( 1)      58% ( 1)      22% ( 2)
cleanup.slab-wrappers                 20% ( 3)      58% ( 3)      14% ( 2)
cleanup.common-wrappers                4% ( 3)      23% ( 1)       3% ( 1)
cleanup.errptr-usage                  15% ( 1)      56% ( 1)       6% ( 1)
cleanup.uninitialised-usage           37% ( 1)      73% ( 1)      25% ( 2)
cleanup.reassignment-usage            33% ( 2)      39% ( 1)      12% ( 0)
cleanup.unwind-order                  16% ( 1)      38% ( 2)       0% ( 0)
cleanup.return-expression-order        3% ( 0)      58% ( 1)       0% ( 0)
cleanup.declare-at-init               36% ( 1)      88% ( 1)       0% ( 0)
cleanup.lock-resource-order           34% ( 1)      82% ( 1)      14% ( 1)
cleanup.guard-scope                   17% ( 1)      58% ( 1)       8% ( 1)
cleanup.widened-critical-section      16% ( 1)      70% ( 1)       0% ( 0)
cleanup.scoped-guard-loop              6% ( 0)      68% ( 1)       4% ( 1)
cleanup.case-label-usage              55% ( 1)      73% ( 2)      18% ( 1)
cleanup.no-free-ptr                   19% ( 1)      58% ( 3)       4% ( 1)
cleanup.return-usage                   3% ( 1)      47% ( 1)       0% ( 0)
cleanup.retain-and-null               42% ( 1)      86% ( 1)       6% ( 1)
cleanup.transfer-usage                20% ( 1)      67% ( 1)       8% ( 2)
cleanup.non-pointer-transfer          14% ( 0)      41% ( 1)      32% ( 1)
cleanup.class-expansion               24% ( 3)      80% ( 5)       0% ( 1)
cleanup.guard-definers                14% ( 1)      58% ( 2)       0% ( 0)
cleanup.guard-names                   11% ( 1)      27% ( 2)       8% ( 4)
cleanup.init-guards                   47% ( 1)      93% ( 1)       8% ( 1)
cleanup.null-lock-argument            59% ( 1)      81% ( 1)      69% ( 3)
cleanup.context-analysis-hooks        57% ( 1)      87% ( 1)      25% ( 1)
cleanup.cond-guard-definition         21% ( 2)      89% ( 4)      19% ( 3)
cleanup.cond-guard-names              15% ( 2)      52% ( 2)      10% ( 2)
cleanup.cond-with-guard               20% ( 1)      73% ( 1)       0% ( 0)
cleanup.cond-with-scoped-guard        35% ( 1)      75% ( 1)       5% ( 1)
cleanup.acquire                       20% ( 1)      74% ( 1)       8% ( 2)
cleanup.goto-documentation            28% ( 1)      81% ( 1)       0% ( 0)
cleanup.goto-usage                    42% ( 3)      78% ( 2)      30% ( 3)
cleanup.mixed-unwind-usage            15% ( 1)      49% ( 1)      37% ( 2)
cleanup.scoped-iterators              25% ( 0)      70% ( 3)      37% ( 3)
cleanup.subsystem-policy              52% ( 2)      94% ( 2)      20% ( 2)
cleanup.conversion-checklist           5% ( 1)      66% ( 2)      21% ( 2)
cleanup.header-change-checklist       66% ( 6)      89% ( 6)      46% ( 5)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `cleanup.macro-families`, `cleanup.free-expansion`, `cleanup.when-cleanup-runs`, `cleanup.guard-scope`, `cleanup.widened-critical-section`, `cleanup.no-free-ptr`, `cleanup.class-expansion`, `cleanup.guard-definers`, `cleanup.cond-guard-definition`.

## Questions reorganised

Subjects now: freeing a variable, order and scope, ownership transfer, guard classes, conditional
guards, goto and policy. Nothing merged. Dropped: `cleanup.conversion-checklist`, five items each
asked by a question in its own subject (`cleanup.lock-resource-order`,
`cleanup.widened-critical-section`, `cleanup.transfer-usage`, `cleanup.return-expression-order`);
the label that still releases by hand what the attribute releases went into `cleanup.goto-usage`.
`cleanup.header-change-checklist` asks what outside the header depends on its internals, not for
seven things to keep working; `cleanup.common-wrappers` groups wrappers by what they tolerate and
`cleanup.cond-guard-names` asks for the suffixes and the forms that are missing. 32 became 31.
