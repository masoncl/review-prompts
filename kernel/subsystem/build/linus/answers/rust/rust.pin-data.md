- `pin_init!` and `try_pin_init!`: need `#[pin_data]` on the struct.
- `init!` and `try_init!`: work on a struct with no attribute.
- `#[pin_data]`: structs only, and every field must be named; enums and unions
  are rejected.
- `#[pin_data]` generates `project()`, which turns `Pin<&mut Self>` into
  `Pin<&mut T>` for `#[pin]` fields and `&mut T` for the others; used in
  `PinnedDrop::drop()`, for example in `drivers/gpu/nova-core/gpu.rs`.
- `trait InPlaceInit` in `rust/kernel/init.rs`: the one kernel code uses; every
  method takes `flags`.
- `trait InPlaceInit` in `rust/pin-init/src/alloc.rs`: takes no `flags` and is
  not built for the kernel; the examples in `rust/pin-init/src/lib.rs` use it.
- `pin_init()` and `init()` of `trait InPlaceInit` in `rust/kernel/init.rs`:
  need `Error: From<E>` and return `Result` with `Error`.
- `try_pin_init()` and `try_init()`: need `E: From<AllocError>` and return
  `Result<_, E>`.
- `ListArc`: does not implement `InPlaceInit`; its inherent `pin_init()` and
  `init()` need `E: From<AllocError>` and return `Result<Self, E>`.
- Preallocated slot: there is no pin_slot here; call `new_uninit()` on `Box` or
  `UniqueArc`, then `write_pin_init()` or `write_init()`.
- `stack_pin_init!`: accepts only an initializer with error `Infallible`; binds
  `Pin<&mut T>`.
- `stack_try_pin_init!(let x = init)`: binds `Result<Pin<&mut T>, E>`; with
  `=?` it propagates the error.
- Type annotation in the stack macros: names the value type `T`, not the
  `Result`.
- Stack macros: not in `rust/kernel/prelude.rs`; import them from `pin_init`.
- Failure inside a macro initializer: the fields initialized so far are dropped
  by `DropGuard` in `rust/pin-init/src/__internal.rs`; the struct's own
  `PinnedDrop` does not run.
- Failure in a `pin_chain()` or `chain()` closure: the complete value is
  dropped, so its `PinnedDrop` does run; see the `PinInit` impl for
  `ChainPinInit` in `rust/pin-init/src/lib.rs`.
- **Potentially unsafe usage**: a step in a macro initializer whose undo is
  only in the struct's `PinnedDrop`.
  - Unsafe: when a later field, `?` or `_: { }` block can return `Err`; the
    undo never runs and the memory is freed.
  - Safe: when the step is the last one that can fail, as in
    `Registration::new()` in `rust/kernel/irq/request.rs` and `TagSet::new()`
    in `rust/kernel/block/mq/tag_set.rs`.
  - Safe: when the undo is in the `Drop` of the field's own type; `DropGuard`
    drops that field on failure, as for `gsp_resources` in `Gpu::new()` in
    `drivers/gpu/nova-core/gpu.rs`.
