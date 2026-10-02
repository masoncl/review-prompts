- The four callbacks are members of `struct ata_reset_operations` in
  `include/linux/libata.h`; `struct ata_port_operations` has no flat
  `prereset` or `hardreset` member, and drivers write `.reset.hardreset`.
- `struct ata_port_operations` embeds it as `reset` and `pmp_reset`;
  `ata_std_error_handler()` passes `&ap->ops->reset`, and
  `sata_pmp_eh_recover()` passes `pmp_reset` for the fan-out links.
- `ata_eh_freeze_port()` before the reset: unconditional, also on an already
  frozen port, but only when `ata_is_host_link()` is true.
- PMP fan-out link: `ata_eh_reset()` calls neither `ata_eh_freeze_port()` nor
  `ata_eh_thaw_port()`.
- After `postreset`: only `eh_info.serror` of the link and slave is zeroed;
  `ATA_PFLAG_EH_PENDING` is not cleared and there is no second thaw.
- `-ENOENT` is special only from `prereset`: reset skipped, classes set to
  `ATA_DEV_NONE`, result 0, with no freeze, thaw or `postreset` call.
- `-ENOENT` with a slave link: skips the reset only when both `prereset`
  calls return `-ENOENT`.
- `-ENOENT` from `softreset` or `hardreset`: an ordinary failure, taken to the
  `fail` label.
- Other non-zero value from `prereset`: `ata_eh_reset()` returns it at once,
  with no retry.
- `-EAGAIN` from the first reset method, hard or soft: not a failure.
- `-EAGAIN` from `hardreset`: asks for a follow-up softreset; see "Choice of
  reset method".
- `-EAGAIN` from the follow-up softreset: a failure, like any non-zero value.
- `sata_link_hardreset()` returns `-EAGAIN` when the link is not offline,
  `sata_pmp_supported()` is true and the link is the host link, with or
  without `check_ready`.
