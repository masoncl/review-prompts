- Hardreset is used first; softreset is first only when no hardreset remains.
- The flag that drops hardreset is `ATA_LFLAG_NO_HRST`; there is no
  ATA_LFLAG_NO_HARDRESET in this tree.
- `ATA_EH_HARDRESET` or `ATA_EH_SOFTRESET` requested in `ehc->i.action` does
  not steer the choice; both bits are cleared before the method is picked, and
  `ata_eh_reset()` then sets the bit of the method it picked.
- The first method is picked before `prereset`, and not picked again after
  it.
- After `prereset` the only test of `ehc->i.action` is whether both
  `ATA_EH_RESET` bits are now clear, which skips the reset.
- Follow-up softreset after a hardreset: when `ata_eh_followup_srst_needed()`
  is true, that is `-EAGAIN` from hardreset, or `sata_pmp_supported()` on the
  host link; the device class is not tested.
- `ata_eh_followup_srst_needed()` is false when `ATA_LFLAG_NO_SRST` is set or
  `ata_link_offline()` is true, even after `-EAGAIN`.
- A failed reset does not switch method: the retry sets the method back to
  hardreset whenever a hardreset callback remains.
