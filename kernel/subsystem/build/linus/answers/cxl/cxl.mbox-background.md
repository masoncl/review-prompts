- Background test: `return_code == CXL_MBOX_CMD_RC_BACKGROUND`, read from the
  status register after the doorbell clears; the opcode is not consulted, and
  there is no cxl_is_background_cmd() or mbox_poll_timeout in this tree.
- `mbox_wait`: a `struct rcuwait`, not a completion; the waiter uses
  `rcuwait_wait_event_timeout()` and `cxl_pci_mbox_irq()` uses
  `rcuwait_wake_up()`.
- With or without an interrupt: the same loop runs; the interrupt only ends a
  pass early.
- `cxl_mbox_cmd_ctor()`: sets neither `poll_count` nor `poll_interval_ms`, so a
  command other than `CXL_MBOX_OP_SANITIZE` from the ioctl path that goes to
  the background gets no wait and `-ETIMEDOUT` unless the status register
  already shows 100 percent.
