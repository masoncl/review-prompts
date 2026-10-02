- `__SC_TEST()`: is
  `(void)BUILD_BUG_ON_ZERO(!__TYPE_IS_LL(t) && sizeof(t) > sizeof(long))`;
  it has no `CONFIG_COMPAT` term.
- `long long` and `unsigned long long`: pass `__SC_TEST()` on every
  architecture; it refuses only a type wider than `long` that is neither.
- `__SC_LONG()`: chooses `long long` by `__TYPE_IS_LL(t)`, which is type
  identity through `__same_type()`, not by `sizeof(t)`.
- Struct or union by value: fails to compile at `(__force t)0` in
  `__TYPE_AS()`, whatever its size; the size comparison in `__SC_TEST()` is
  not what rejects it.
