- `{:p}` through `fmt!`: hashed like C `%p`, not the raw address; see
  `HashedPtr` in `rust/kernel/fmt.rs`.
- `HashedPtr` output: `0x` prefix, zero-padded to pointer width; the real
  address appears only when `no_hash_pointers` is set.
- Types routed to `HashedPtr`: `*const T`, `*mut T`, `&T`, `&mut T` and
  `NonNull<T>`.
- `pr_info!` and the other macros built on `print_macro!`, and the macros built
  on `dev_printk!` (for example `dev_info!`): expand through `fmt!`, so `{:p}`
  in them is hashed too.
- `fmt::Pointer` in `rust/kernel/fmt.rs`: implemented only in that file; `{:p}`
  on any other type through `fmt!` does not compile.
- `{:?}`, `{:x}` and the other specifiers in `impl_fmt_adapter_forward!`:
  `Adapter` forwards them to `core::fmt` and they never reach `HashedPtr`.
- `{:?}` on a raw pointer, or on a struct deriving `Debug` over one: formatted
  by `core`, so not hashed.
- `c_str!`: matches `$str:expr`, not only a literal; in-tree uses are inside
  macros, over `concat!`, `stringify!`, `file!` or a macro argument.
- `CString::try_from_fmt()`: returns `EINVAL` when the formatted text has an
  interior NUL, besides the allocation failure.
- `CString::try_from_fmt()` and `to_cstring()`: take no flags and allocate with
  `GFP_KERNEL`.
- `as_char_ptr_in_const_context()` in `rust/kernel/str.rs`: the free function
  for `const` code, where the trait method cannot be called.
