- `ata_exec_internal()` in `drivers/ata/libata-core.c`: releases ownership
  around its completion wait when `eh_owner == current`, so every internal
  command issued from EH lets another port's EH run.
- `msleep()` in EH context: keeps ownership; `ata_msleep()` gives it up when
  its `ap` is not NULL.
- **Unsafe usage**: `ata_msleep()` or `ata_exec_internal()` in the middle of a
  sequence on a resource shared by the ports of one host.
  - Unsafe: when another port's EH can touch the same resource; it runs as
    soon as `ata_eh_release()` unlocks `eh_mutex`.
  - Safe: sleep with `msleep()` so ownership is kept, as `ahci_start_port()`
    in `drivers/ata/libahci.c` does while the host-wide EM transmit bit is
    busy.
- `drivers/ata/Makefile` sets `CONTEXT_ANALYSIS := y`; `ata_eh_acquire()` is
  declared `__acquires(&ap->host->eh_mutex)` and `ata_eh_release()`
  `__releases()` of the same.
- Conditional release under that analysis: `ata_msleep()` is marked
  `__context_unsafe()`; `ata_exec_internal()` balances its calls with
  `__acquire()` and `__release()`.
