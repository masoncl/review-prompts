- `cxl_internal_send_cmd()` in `drivers/cxl/core/mbox.c`: has no NULL test of
  `cxl_mbox`; the `-EINVAL` NULL test is in `cxl_mailbox_init()`.
- `-E2BIG`: returned by `cxl_internal_send_cmd()` itself, before `mbox_send` is
  called, when `size_in` or `size_out` exceeds `payload_size`.
- `__cxl_pci_mbox_send_cmd()` in `drivers/cxl/pci.c`: its error returns are
  `-EBUSY`, `-EINVAL` and `-ETIMEDOUT`; it does not return `-ENXIO`.
- Device codes: `CMD_CMD_RC_TABLE` in `drivers/cxl/cxlmem.h` maps every error
  code to `-ENXIO`, including `CXL_MBOX_CMD_RC_BUSY`, except
  `CXL_MBOX_CMD_RC_PADDR` (`-EFAULT`) and `CXL_MBOX_CMD_RC_POISONLMT`
  (`-EBUSY`).
- `-EBUSY` from `cxl_internal_send_cmd()`: either the transport refused the
  command or the device reported `CXL_MBOX_CMD_RC_POISONLMT`.
- `min_out == 0` with a nonzero entry `size_out`: the reply must fill the whole
  entry `size_out`, else `-EIO`.
- Entry `size_out == 0`: the only successful case with no output size check.
- `size_out` on return: meaningful only when the result is 0 or `-EIO`; the PCI
  transport leaves the entry value in place on a transport error and on a
  device error.
- **Unsafe usage**: a `mbox_send` implementation that returns `-EIO`.
  - Unsafe: `cxl_internal_send_cmd()` hits `WARN_ONCE()` and returns `-ENXIO`;
    `cxl_xfer_log()` takes `-EIO` to mean a short log and reads `size_out`.
  - Safe: return 0 and put the device code in `return_code`, or return another
    errno, as `__cxl_pci_mbox_send_cmd()` does.
- `handle_mailbox_cmd_from_user()`: calls `mbox_send` directly, not
  `cxl_internal_send_cmd()`, so the `-E2BIG` test, the `-EIO` translation, the
  `min_out` test and the device-code conversion do not apply; the device code
  goes to user space in `retval`.
