- `CONFIG_RUST_OVERFLOW_CHECKS`: `default y` in `lib/Kconfig.debug`, so
  overflowing arithmetic panics in a default build; with it off the result
  wraps.
- `CONFIG_RUST_OVERFLOW_CHECKS` also gates explicit `assert!` calls in the
  `kernel` crate, for example adding a `Delta` to an `Instant` in
  `rust/kernel/time.rs`, and `raw_strncpy_from_user()` in
  `rust/kernel/uaccess.rs`.
- `Vec::remove()` and `Vec::insert_within_capacity()` in
  `rust/kernel/alloc/kvec.rs` do not panic on a bad index: `remove()` returns
  `Result<T, RemoveError>` and `insert_within_capacity()` returns
  `InsertError::IndexOutOfBounds`.
- `Vec` has no try_push or swap_remove here; `push()` takes GFP flags and
  `push_within_capacity()` does not allocate.
- `assert!` and `assert_eq!` inside doctests and inside `#[test]` functions of
  a `#[kunit_tests]` module do not panic: `scripts/rustdoc_test_gen.rs` and
  `rust/macros/kunit.rs` override them with `kunit_assert!` and
  `kunit_assert_eq!`, which report to KUnit.
- `unwrap()` and `expect()` in tests still panic;
  `Documentation/rust/testing.rst` asks for `?` instead in documentation
  tests.
- `Documentation/rust/coding-guidelines.rst`: requires a `# Panics` section on
  any function that may panic, and says panicking "should be very rare", with
  a `Result` return as the usual alternative.
- `unsafe_precondition_assert!`: defined in `rust/kernel/safety.rs`; checks,
  inside an `unsafe fn`, a precondition the caller promised in `# Safety`.
- `unsafe_precondition_assert!` expands to `::core::debug_assert!` with the
  prefix "unsafe precondition violated: ", so it is live only with
  `CONFIG_RUST_DEBUG_ASSERTIONS`, which has no `default` line and is off.
- `unsafe_precondition_assert!` when live: a failure is an ordinary panic and
  reaches `BUG()`.
- `unsafe_precondition_assert!` is not in `rust/kernel/prelude.rs`; it is
  `#[macro_export]`, so the path is `kernel::unsafe_precondition_assert!`.
- `unsafe_precondition_assert!` has no caller in this tree outside its own doc
  example; existing `unsafe fn`s use plain `debug_assert!`, for example
  `CpuId::from_i32_unchecked()` in `rust/kernel/cpu.rs`.
