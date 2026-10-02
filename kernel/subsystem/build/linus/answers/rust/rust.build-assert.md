| Macro | Condition may use | Where | Failure |
|---|---|---|---|
| `static_assert!` | constants only; no generics, no variables | module level and inside bodies | compile error; evaluated even if the enclosing function is never used |
| `const_assert!` | constants and generics of the enclosing function or `impl`; no variables | statement position inside a body | compile error, only for instances that are actually instantiated |
| `build_assert!` | anything, including function arguments | statement position inside a body or const initializer block | const context: compile-time panic; otherwise undefined `rust_build_error` at link |
| `build_error!` | nothing; unconditional | expression position on a path that must be dead | same two modes as `build_assert!` |

- `const_assert!`: exists; defined in `rust/kernel/build_assert.rs` beside the
  other three, and all four are in `rust/kernel/prelude.rs`.
- `static_assert!`: defined in `rust/kernel/build_assert.rs`; there is no
  rust/kernel/static_assert.rs.
- `static_assert!` expands to an unnamed `const _: () = ...;` item, so it goes
  at module level or inside a body, not as an associated item of an `impl`.
- `build_error()` in `rust/build_error.rs` is a `const fn` that panics, so a
  `build_assert!` evaluated in const context fails in the compiler, not the
  linker; `rust/kernel/iov.rs` uses it that way in a `const _` block.
- `const_assert!` cannot refer to function arguments even inside a
  `const fn`; such a function uses `build_assert!`, as `_IOC()` in
  `rust/kernel/ioctl.rs` does.
- `build_assert!` on generics only (for example `LockedBy::new()` in
  `rust/kernel/sync/locked_by.rs`): works with no inline attribute; the module
  doc marks it "Discouraged" in favour of `const_assert!`.
- `CONFIG_RUST_BUILD_ASSERT_ALLOW`: `rust/Makefile` then links
  `build_error.o` and `rust/exports.c` exports `rust_build_error`, so a
  surviving call becomes a run-time panic; without it the object is built but
  not linked.
- **Potentially unsafe usage**: `build_assert!` or `build_error!` on a
  condition that depends on a function argument, in a function without
  `#[inline(always)]`.
  - Unsafe: when the function has a run-time caller; if it is emitted out of
    line the call to `build_error()` survives.
  - Safe: `#[inline(always)]` on the function and on every wrapper that
    forwards the argument, as `_IO()` and `_IOC()` in `rust/kernel/ioctl.rs`,
    and `io_view_assert()` with its callers in `rust/kernel/io.rs`; the
    kerneldoc of `build_assert!` states the requirement.
  - Safe: a `const fn` that is private or generic and has no run-time caller,
    as `DataDirection::const_cast()` in `rust/kernel/dma.rs` (private, called
    only for enum discriminants) and `ModInfoBuilder::push()` in
    `rust/kernel/firmware.rs` (generic over `N`, reached only from
    `module_firmware!`); the const evaluator panics instead.
