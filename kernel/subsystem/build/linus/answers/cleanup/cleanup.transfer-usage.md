- **Potentially unsafe usage**: `no_free_ptr()` in the argument list of a call
  that can return an error.
  - Unsafe: when the callee can return an error without freeing or keeping the
    object; the variable is already NULL, so the cleanup frees nothing and the
    object leaks.
  - Safe: when the callee releases the object on its own failure path, as
    `add_or_reset_cxl_resource()` does for `__cxl_parse_cfmws()` in
    `drivers/cxl/acpi.c`.
  - Safe: `devm_add_action_or_reset()`, which calls the action on failure
    (`__devm_add_action_or_reset()` in `include/linux/device/devres.h`), as in
    `devm_cxl_setup_fwctl()` in `drivers/cxl/core/features.c`.
  - Safe: when the callee returns `void`, as `auxiliary_set_drvdata()` in
    `mlx5ctl_probe()` in `drivers/fwctl/mlx5/main.c`.
  - Safe: pass the pointer armed and call `retain_and_null_ptr()` only on
    success, as `do_new_mount_fc()` in `fs/namespace.c` does; the comment above
    `retain_and_null_ptr()` defines this form.
- **Potentially unsafe usage**: disarming a `__free()` variable before the last
  failure return of the function.
  - Unsafe: when nothing releases the new owner on the later failure path; the
    object is then freed by nobody.
  - Safe: when the new owner is itself still armed, as in
    `__trace_uprobe_create()` in `kernel/trace/trace_uprobe.c`: `filename` is
    stored into `tu`, and `free_trace_uprobe()` frees `tu->filename`.
  - Safe: after the last failure return, as `msi_create_device_irq_domain()`
    in `kernel/irq/msi.c` does with `retain_and_null_ptr()`.
- Using the object after the disarm: take a plain pointer before it;
  `__cxl_parse_cfmws()` keeps `cxld` for its `dev_dbg()` after
  `no_free_ptr(cxlrd)`.
- Fd and file together: `fd_publish()` in `include/linux/file.h` calls
  `fd_install()`, then `retain_and_null_ptr()` on the file and `take_fd()` on
  the fd; `FD_ADD()` in the same file builds on `FD_PREPARE()` and
  `fd_publish()`.
