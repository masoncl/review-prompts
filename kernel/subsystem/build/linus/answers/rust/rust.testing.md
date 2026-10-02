- Option for a new `#[kunit_tests]` suite: add it to
  `rust/kernel/Kconfig.test`, inside `if RUST_KUNIT_TESTS`, and put a
  `#[cfg]` on that option above `#[kunit_tests(...)]`; follow
  `RUST_STR_KUNIT_TEST` and `rust/kernel/str.rs`.
- `kunit_tests()` in `rust/macros/kunit.rs`: adds
  `#[cfg(CONFIG_KUNIT="y")]` to the module itself, so a suite is not built
  with `KUNIT=m`.
- `RUST_KERNEL_DOCTESTS`: `depends on RUST && KUNIT=y`, default
  `KUNIT_ALL_TESTS`.
- Only examples reachable from `rust/kernel/lib.rs` become KUnit tests
  (`cmd_rustdoc_test_kernel` in `rust/Makefile`); examples in a driver or
  sample are not compiled by any target; `rusttest` runs those of
  `rust/macros/lib.rs`.
- `no_run`: has no effect on the KUnit tests; rustdoc is already run with
  `--no-run`, and `scripts/rustdoc_test_gen.rs` emits a call to `main()` for
  every example the builder saved, without reading attributes.
- **Potentially unsafe usage**: an example that touches hardware or user
  memory, relying on `no_run` to keep it from executing.
  - Unsafe: when the statements sit at the top level of the example; they
    become the body of `main()`, which the generated KUnit case calls.
  - Safe: when the statements are inside a function that the example never
    calls, as in the example on `Firmware` in `rust/kernel/firmware.rs`.
- `compile_fail`: `scripts/rustdoc_test_builder.rs` saves the source and
  compiles nothing, so an expected failure cannot be checked; under
  `rust/kernel/` the only use is `ignore,compile_fail` in
  `rust/kernel/types/for_lt.rs`.
- Example on a private item: the generated tests are a separate crate built
  with `--extern kernel`, so the example cannot name an item that is not
  `pub`; `Documentation/rust/testing.rst` states that doctests are not run for
  nonpublic functions.
