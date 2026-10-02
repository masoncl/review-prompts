These are conventions that the maintainers of the Rust code in the kernel ask
for. No code in a kernel tree states them, so they are kept by hand and
inserted as they are.

- In an abstraction, such as the `kernel` crate, a small function should be
  annotated with `#[inline]`, and so should a function that forwards to a C
  binding call.
- A leaf crate, such as a driver, is exempt from that convention. Its author
  is free to use `#[inline]` or to omit it.
- A function may use `#[inline(always)]` or `#[inline]` whether or not it uses
  `build_assert!()`, for example because it is small or because its speed
  matters.
