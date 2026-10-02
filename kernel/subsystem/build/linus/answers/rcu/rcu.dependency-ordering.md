- Bare `READ_ONCE()` of the pointer: same ordering as `rcu_dereference()`;
  `__rcu_dereference_check()` is `READ_ONCE()` plus the lockdep and sparse
  checks, and `list_entry_rcu()` is `READ_ONCE()` alone.
  `Documentation/RCU/rcu_dereference.rst` allows the bare form only where data
  is added and never removed while readers run.
- Integer casts: the value must stay a pointer. The document allows a
  temporary cast to `uintptr_t` for two things only: setting or clearing
  low-order must-be-zero bits of an aligned pointer, and XOR to translate
  pointers. Cast back before any other use.
- Comparison rule below: its six safe cases are those of
  `Documentation/RCU/rcu_dereference.rst`.
- **Potentially unsafe usage**: comparing the returned pointer with a
  non-NULL pointer, then loading through it.
  - Unsafe: the equal branch loads through the pointer, and the object compared
    against was initialised or changed recently. The compiler may load from the
    known address, and that load no longer depends on `rcu_dereference()`.
  - Unsafe: the not-equal branch, when the compiler can see that the pointer
    has only two possible values; not-equal then reveals the value too.
  - Safe: comparison with NULL, as `hlist_for_each_entry_rcu()` does.
  - Safe: the pointer is never dereferenced after the comparison, as in
    `list_empty()`.
  - Safe: only the not-equal branch dereferences and the compiler cannot deduce
    the value, as in `list_first_or_null_rcu()` and the loop test of
    `list_for_each_entry_rcu()`.
  - Safe: the object compared against was initialised long before, for example
    at compile time, at boot, at module init, or under an earlier hold of a
    lock now held.
  - Safe: the other pointer also came from `rcu_dereference()`.
  - Safe: every access after the comparison is a store.
