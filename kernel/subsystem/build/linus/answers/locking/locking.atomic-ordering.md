- `atomic_dec_and_test()`, `atomic_sub_and_test()`, `atomic_inc_and_test()`,
  `atomic_add_negative()`: not conditional; they always perform the RMW and
  are fully ordered whatever they return.
- Conditional ops (unordered when they do not store): the generated kerneldoc
  in `include/linux/atomic/atomic-arch-fallback.h` marks each one with
  "relaxed ordering is provided" for the case where `@v` is not modified; for
  example `raw_atomic_add_unless()`, `raw_atomic_inc_not_zero()`,
  `raw_atomic_try_cmpxchg()`.
- "Unordered" in `Documentation/atomic_t.txt`: unordered against other memory
  locations; address dependencies from the value read still hold.
- Bitops are sorted by `Documentation/atomic_bitops.txt`, not
  `Documentation/atomic_t.txt`, and the conditional rule differs: conditional
  RMW bitops are fully ordered.
- `test_and_set_bit()` on an already-set bit: still fully ordered; the generic
  `arch_test_and_set_bit()` in `include/asm-generic/bitops/atomic.h` always
  does `raw_atomic_long_fetch_or()`.
- `test_and_set_bit_lock()`: ACQUIRE only when it sets the bit; the generic
  version in `include/asm-generic/bitops/lock.h` returns after a `READ_ONCE()`
  when the bit is already set.
