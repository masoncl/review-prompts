- `rust/kernel/types.rs`: does not re-export `ARef` or `AlwaysRefCounted`, so
  a path through `kernel::types` does not resolve for either.
- `kernel::sync::aref`: the only path for `ARef` and `AlwaysRefCounted`;
  `rust/kernel/sync.rs` and `rust/kernel/prelude.rs` do not re-export them
  either.
- `Opaque::cast_into()`: `*const Opaque<T>` to `*mut T`, without creating a
  reference.
- `Opaque::cast_from()`: `*const T` to `*const Opaque<T>`; it returns a const
  pointer, so a caller that needs `*mut` must cast again.
- `Opaque<T>` has no `raw_get()` method; `raw_get()` in this tree belongs to
  `Work` and `HrTimer`.
- `Opaque::pin_init()`: the `Wrapper` trait method from `pin_init`, so the
  trait must be in scope to call it.
