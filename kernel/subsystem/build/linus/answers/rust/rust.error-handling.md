- `Error::from_errno()`: the only public constructor from an integer.
- `Error::try_from_errno()` and `Error::from_errno_unchecked()`: private to
  `rust/kernel/error.rs`, so code outside that file cannot call them.
- `from_err_ptr()`: after `IS_ERR()` it uses `Error::from_errno_unchecked()` on
  `PTR_ERR()`, with no further range check and no warning.
- `from_err_ptr()` on NULL: returns `Ok(ptr)`; a C function that returns NULL on
  failure needs its own check.
- `from_result()`: the bound is `T: From<i16>` and the errno is cast `as i16`;
  there is no ReturnToKernelPort trait in this tree.
- `Error::to_blk_status()`: `pub(crate)` and only under `CONFIG_BLOCK`.
