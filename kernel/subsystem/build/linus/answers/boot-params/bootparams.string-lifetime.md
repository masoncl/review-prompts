- `static_command_line`: a copy of the `command_line` that `setup_arch()`
  returned, after `extra_command_line`; not a copy of `boot_command_line`.
- Per-level set functions: the buffer is the `kzalloc()` copy local to
  `do_initcalls()`; it is overwritten before the next level and freed with
  `kfree()` after the last.
- Module load: there is no mod->args here; `load_module()` passes a local
  `args` from `strndup_user()` and calls `kfree()` on it right after
  `parse_args()`.
- sysfs write: `param_attr_store()` passes the sysfs buffer to the set
  function.
- `param_set_charp()`: the test is `slab_is_available()`; it keeps the raw
  pointer only when that is false.
- **Potentially unsafe usage**: keeping the `char *` passed to a handler after
  the handler returns.
  - Unsafe: in an `early_param()` handler, when the pointer is read after
    `free_initmem()`; `tmp_cmdline` in `parse_early_param()` is `__initdata`.
  - Unsafe: in a set function, when `slab_is_available()` is true; the
    buffer is then one of the three short-lived ones above.
  - Safe: in a `__setup()` handler; `static_command_line` comes from
    `memblock_alloc_or_panic()` in `setup_command_line()` and is not freed,
    as `init_setup()` relies on for `execute_command`.
  - Safe: in an `early_param()` handler whose text is read only by `__init`
    code, before `free_initmem()`; `hugetlb_add_param()` in `mm/hugetlb.c`
    copies it to `hstate_cmdline_buf`, also `__initdata`, for
    `hugetlb_parse_params()`.
  - Safe: in a set function that copies whenever `slab_is_available()` is
    true, as `param_set_charp()` does.
