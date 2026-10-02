- `core::sync::atomic` atomic types: not used outside the vendored crates and
  `rust/pin-init/examples/`; binder uses `Atomic<T>`, and `rust/kernel/` uses
  `Atomic<T>` and `AtomicFlag`.
- The one import of `core::sync::atomic` outside the vendored crates and
  `rust/pin-init/examples/`: `fence` and `Ordering` in
  `drivers/gpu/nova-core/gsp/cmdq.rs`; no atomic type is involved.
- `.clippy.toml`: has no rule against `core::sync::atomic`; only the module doc
  of `rust/kernel/sync/atomic.rs` says to avoid it.
- `AtomicType` implementations in `rust/kernel/sync/atomic/predefine.rs`:
  `bool`, `i8`, `i16`, `i32`, `i64`, `u32`, `u64`, `isize`, `usize`, `*mut T`
  and `*const T`; there is no `u8` or `u16`.
- `Atomic<T>` over `bool`, `i8`, `i16` and pointers: has `load()`, `store()`,
  `xchg()` and `cmpxchg()`; `add()`, `fetch_add()` and `fetch_sub()` exist only
  where `T: AtomicAdd`, which is the 32-bit, 64-bit and pointer-sized integers.
- `AtomicFlag` in `rust/kernel/sync/atomic.rs`: a boolean flag preferred over
  `Atomic<bool>` when `xchg()` or `cmpxchg()` is needed.
- Ordering: always an explicit value argument; there is no default.
- `load()` accepts only `Relaxed` or `Acquire`, `store()` only `Relaxed` or
  `Release`, and `add()` only `Relaxed`; anything else fails to compile.
- Raw-pointer forms: the free functions `atomic_load()`, `atomic_store()`,
  `xchg()` and `cmpxchg()` in `rust/kernel/sync/atomic.rs`; `atomic_load()` and
  `atomic_store()` stand in for `READ_ONCE()`, `smp_load_acquire()`,
  `WRITE_ONCE()` and `smp_store_release()` on C memory.
- Barriers in `rust/kernel/sync/barrier.rs`: the public functions are only
  `mb()`, `smp_mb()` and `dma_mb()`, each taking `Read`, `Write` or `Full`.
- There is no Rust `smp_rmb()` or `smp_wmb()` function; write `smp_mb(Read)` and
  `smp_mb(Write)`.
