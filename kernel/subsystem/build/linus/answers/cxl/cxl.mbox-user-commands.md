- `cxl_validate_cmd_from_user()`: takes a `const struct cxl_send_command *`,
  returns `int`, and fills a `struct cxl_mbox_cmd`; there is no
  struct cxl_memdev_command in this tree.
- `flags` in `cxl_to_mem_cmd()`: bits outside `CXL_MEM_COMMAND_FLAG_MASK` give
  `-EINVAL`; bits inside the mask pass.
- `CXL_CMD_FLAG_FORCE_ENABLE`: not looked at during validation, which tests
  only `enabled_cmds`; `cxl_enumerate_cmds()` sets those bits in
  `enabled_cmds`.
- `out.size > payload_size`: `-EINVAL` only in `cxl_to_mem_cmd_raw()`; for
  other commands `cxl_mbox_cmd_ctor()` allocates
  `min(out.size, payload_size)`, for fixed and variable sizes alike.
- `cxl_payload_from_user_allowed()` false: `-EBUSY` from `cxl_mbox_cmd_ctor()`,
  the same errno as an exclusive command.
- `cxl_to_mem_cmd_raw()`: tests none of `flags`, `in.rsvd`, `out.rsvd`,
  `enabled_cmds` or `exclusive_cmds`; an opcode the kernel owns is kept from
  the raw path only by `cxl_mem_raw_command_allowed()`
  (`cxl_disabled_raw_commands[]` and `cxl_is_security_command()`), and
  `cxl_raw_allow_all` bypasses both.
- Raw path: has no `CAP_SYS_RAWIO` test and no `add_taint()` call of its own;
  an accepted raw command triggers `dev_WARN_ONCE()`, whose `TAINT_WARN` is
  the only taint.
- `enabled_cmds` and `exclusive_cmds`: fields of `struct cxl_mailbox` in
  `include/cxl/mailbox.h`.
- `set_exclusive_cxl_commands()` in `drivers/cxl/core/memdev.c`: holds
  `cxl_memdev_rwsem` for write, not `mbox_mutex`; its only caller is
  `cxl_nvdimm_probe()` in `drivers/cxl/pmem.c`, with the bitmap that
  `cxl_pmem_init()` fills.
