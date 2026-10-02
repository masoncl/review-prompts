- Variants that end in _nested: two locks taken with the same subclass and
  held together are one class, and `check_deadlock()` reports "possible
  recursive locking detected".
- Variants that end in _nested, not checked: that a given instance gets the
  same subclass on every path; swapped instances with unswapped subclasses
  look identical to lockdep.
- Nest lock, what is checked: `__lock_acquire()` tests only that the current
  task holds the named lock, else "Nested lock was not taken".
- Nest lock, what is not checked: that the named lock excludes every other
  task that takes several locks of the class; `mm_take_all_locks()` in
  `mm/vma.c` names `mm->mmap_lock` and also takes `mm_all_locks_mutex`.
- Nest lock position: it must sit below the first held lock of the class in
  the held stack; `check_deadlock()` otherwise reports recursion.
- Nest lock with another lock of the class already held: `validate_chain()`
  skips `check_prevs_add()`, so that acquisition records no edge from any held
  lock, of any class.
- `lock_set_cmp_fn()`, when it runs: `cmp_fn` is tested only in
  `check_deadlock()` and `check_prev_add()`, which run only when the chain is
  not yet in the chain cache.
- `lock_set_cmp_fn()`, consequence: the chain key hashes class and read mode,
  not the instance, so once a chain of held classes has passed, a later
  nesting with the same chain in the wrong instance order is not compared.
- `cmp_fn` result of 0 or more: treated as not allowed; the report adds "and
  the lock comparison function returns".
- `lockdep_set_lock_cmp_fn()`: sets `cmp_fn` on one `struct lock_class`, so an
  acquisition with another subclass is not covered.
- `lock_set_cmp_fn()` without `CONFIG_PROVE_LOCKING`: expands to nothing.
