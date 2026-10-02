- `__rust_helper`: defined only in `rust/helpers/helpers.c`, before the
  `#include` lines of the helper files.
- Expansion in every C compile of the helpers: `__always_inline`.
- Expansion under bindgen: empty. `rust/Makefile` passes `-D__BINDGEN__` in
  `bindgen_c_flags_final`, because bindgen skips inline functions.
- The definition tests only `__BINDGEN__`. It does not depend on
  `CONFIG_RUST_INLINE_HELPERS`.
- `CONFIG_RUST_INLINE_HELPERS`: defined in `lib/Kconfig.debug`; among its
  `depends on` lines are `EXPERT` and `ARM64 || X86_64`.
- With `CONFIG_RUST_INLINE_HELPERS`: `rust/Makefile` compiles `helpers.c` to
  `helpers/helpers.bc` and `helpers/helpers_module.bc`.
  `scripts/Makefile.build` links one of them into each Rust object it builds
  (`helpers/helpers_module.bc` when the object is part of a module,
  `helpers/helpers.bc` otherwise), and `rust/Makefile` links
  `helpers/helpers.bc` into `kernel.o`.
- Coverage: every function body under `rust/helpers/` carries
  `__rust_helper`, including the macro-generated ones in
  `rust/helpers/atomic_ext.c`.
- `rust/helpers/build_assert.c`: holds only a `static_assert()`, so it has no
  function to annotate.
