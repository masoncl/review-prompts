- Register macros carry the `GICV5_` prefix; there is no ITS_DIDR, ITS_EIDR
  or ITS_STATUSR identifier, and the sync idle bit is
  `GICV5_ITS_SYNC_STATUSR_IDLE`.
- `gicv5_its_itt_cache_inv()`: writes `GICV5_ITS_DIDR` (64-bit), then
  `GICV5_ITS_EIDR`, then `GICV5_ITS_INV_EVENTR`, then calls
  `gicv5_its_cache_sync()`.
- `GICV5_ITS_INV_EVENTR`: written with `GICV5_ITS_INV_EVENTR_I` only;
  `GICV5_ITS_INV_EVENTR_ITT_L2SZ` and `GICV5_ITS_INV_EVENTR_L1` are never
  set.
- `gicv5_its_device_cache_inv()`: writes `GICV5_ITS_DIDR`, then
  `GICV5_ITS_INV_DEVICER` (I bit, `event_id_bits` of the device,
  `GICV5_ITS_INV_DEVICER_L1` 0), then calls `gicv5_its_cache_sync()`.
- `gicv5_its_cache_sync()`: writes nothing; polls `GICV5_ITS_STATUSR` for
  `GICV5_ITS_STATUSR_IDLE` with `gicv5_wait_for_op_atomic()`.
- `gicv5_its_cache_sync()` and `gicv5_its_syncr()`: unrelated; neither
  calls the other.

| | `gicv5_its_cache_sync()` | `gicv5_its_syncr()` |
|---|---|---|
| Writes | nothing | `GICV5_ITS_SYNCR`, 64-bit: `GICV5_ITS_SYNCR_SYNC` plus DeviceID |
| Polls | `GICV5_ITS_STATUSR` | `GICV5_ITS_SYNC_STATUSR` |
| Wait helper | `gicv5_wait_for_op_atomic()`, busy-waits | `gicv5_wait_for_op()`, i.e. `readl_poll_timeout()`, may sleep |
| Result | returned | discarded; function is `void` |
| Scope | takes no ID; waits on the one idle bit of that ITS | one DeviceID |
| Called from | the two invalidate helpers | `gicv5_its_irq_domain_free()` only |

- `GICV5_ITS_SYNCR_SYNCALL`: defined, never used; no whole-ITS sync exists.
- `gicv5_its_syncr()` in `gicv5_its_irq_domain_free()`: runs after
  `irq_domain_free_irqs_parent()` and before `gicv5_irs_syncr()`; it
  follows no table write.
- `gicv5_its_syncr()`: needs a context that may sleep; the
  activate/deactivate callbacks are not one, they can run under
  `desc->lock`.
