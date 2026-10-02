- Asynchronous branch: taken only for `CXL_MBOX_OP_SANITIZE`;
  `CXL_MBOX_OP_SECURE_ERASE` takes the synchronous wait like any other opcode.
- `poll_dwork` delay: 1 second for the first run, then `poll_tmo_secs + 10`
  seconds; `CXL_MAILBOX_TIMEOUT_MS` is the doorbell timeout only.
- Mailbox gate: `poll_tmo_secs > 0`, not `sanitize_active`; it lasts until
  `cxl_mbox_sanitize_work()` sets it to 0, and `CXL_MBOX_OP_GET_HEALTH_INFO`
  passes it.
- `cxl_decoder_commit()` in `drivers/cxl/core/hdm.c`: returns `-EBUSY` for an
  endpoint decoder while `sanitize_active` is set; `cxl_mem_probe()` makes no
  such test.
- `cxl_decoder_commit()`: reads `sanitize_active` without `mbox_mutex`; it runs
  under `cxl_rwsem.region` held for write by `__commit()`, and
  `cxl_mem_sanitize()` starts a sanitize under the same rwsem held for read.
- `cxl_pci_mbox_irq()` for a sanitize: only reschedules `poll_dwork` with delay
  0; `cxl_mbox_sanitize_work()` clears the state and notifies, with or without
  an interrupt.
- `sanitize_node` NULL: the interrupt does not reschedule the work and no
  notification is sent; it is NULL when `devm_cxl_sanitize_setup_notifier()`
  found `CXL_SEC_ENABLED_SANITIZE` clear, and after
  `sanitize_teardown_notifier()`.
