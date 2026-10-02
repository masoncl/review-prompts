- Implementors of `ForeignOwnable`, all five: `Box<T, A>`,
  `Pin<Box<T, A>>`, `Arc<T>`, `ARef<T>` and `()`.
- `ARef<T>`: implemented in `rust/kernel/sync/aref.rs`.
- `Box<T, A>`: generic over the allocator, so `KBox`, `VBox` and `KVBox` all
  qualify.
- References: no `&T` impl exists.
- `Owned` in `rust/kernel/scatterlist.rs`: does not implement
  `ForeignOwnable`.
- `ARef<T>` and `Arc<T>`: `BorrowedMut` is the same shared type as
  `Borrowed`, so `borrow_mut()` gives no exclusive access.
- `FOREIGN_ALIGN` for `ARef<T>` and `()`: plain `align_of`, so it can be below
  4. `rust/kernel/xarray.rs` rejects such types with
  `build_assert!(T::FOREIGN_ALIGN >= 4)`.
- `FOREIGN_ALIGN` for `Box<T, A>`: the larger of `align_of::<T>()` and
  `A::MIN_ALIGN`.
