- `its_send_single_command()` and `its_send_single_vcommand()` are both
  instances of `BUILD_SINGLE_CMD_FUNC`; there is no BUILD_SINGLE_VCMD_FUNC
  macro.
- `GITS_CREADR` is read into `rd_idx` under `its->lock`, after the last
  `its_flush_cmd()` and immediately before `its_post_commands()`.
- `its_allocate_entry()` on a full queue: spins 1000000 times with
  `udelay(1)`, about 1 s, with `its->lock` held and IRQs off, then returns
  NULL.
- Sync slot allocation fails: the macro jumps to `post`, so the main command
  is still posted and waited for, with no SYNC or VSYNC after it.
