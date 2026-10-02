- Failed read of a command: the command is skipped and `creadr` still
  advances; the loop does not stop.
- `vgic_its_handle_command()`: takes `its_lock` around the whole dispatch, so
  every handler runs under `cmd_lock` then `its_lock`.
- `vgic_its_process_commands()`: tests only `its->enabled`;
  `GITS_CBASER_VALID` is tested in `vgic_mmio_write_its_ctlr()` when the
  enable bit is set.
- `cwriter` on a disabled ITS: stored after the range test against
  `ITS_CMD_BUFFER_SIZE(its->cbaser)`, as on an enabled one; the commands run
  when `vgic_mmio_write_its_ctlr()` enables the ITS.
- Loop termination: `creadr` wraps only when it equals
  `ITS_CMD_BUFFER_SIZE(its->cbaser)`, so both offsets must be multiples of
  `ITS_CMD_SIZE` below that size.
- That invariant is kept by `vgic_mmio_write_its_cwriter()`,
  `vgic_mmio_uaccess_write_its_creadr()`, and by
  `vgic_mmio_write_its_cbaser()` and `vgic_its_reset()`, which zero both
  offsets.
