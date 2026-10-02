- `event_map.vlpi_lock`: a raw spinlock, taken only in
  `its_irq_set_vcpu_affinity()`, which then calls `its_vlpi_map()` or
  `its_vlpi_unmap()`; there is no mutex on this path.
- Context: `irq_set_vcpu_affinity()` holds the irq descriptor lock as well, so
  neither function may sleep; `vlpi_maps` is allocated with `kzalloc_objs()`
  and `GFP_ATOMIC`.
- Both cases: the VM binding check and the copy of `*info->map` into
  `vlpi_maps[event]` run before the forwarded test.
- Already forwarded: tested with `irqd_is_forwarded_to_vcpu()`, not a
  counter; sends only `its_send_vmovi()`.
- Already forwarded: no property-table write, no DISCARD, `nr_vlpis`
  unchanged.
- Not yet forwarded, in order:
  1. `its_map_vm()`
  2. `irqd_set_forwarded_to_vcpu()`
  3. `lpi_write_config()` with `info->map->properties`
  4. `its_send_discard()`
  5. `its_send_vmapti()`
  6. `event_map.nr_vlpis++`
- Step 2 before step 3: `lpi_write_config()` picks the VM's `vprop_page`
  through `get_vlpi_map()`, which returns NULL until the irq is flagged
  forwarded.
- `its_send_vmapti()`: always VMAPTI; there is no VMAPI variant here.
- Last unmap (`nr_vlpis` reaches 0): sets `event_map.vm = NULL` and
  `kfree()`s `event_map.vlpi_maps`; the `vlpi_maps` pointer is left stale.
- `event_map.vm`: what the driver tests for "device has vLPIs"; a NULL test
  on `vlpi_maps` is wrong after the last unmap.
- `its_unmap_vm()`: called on every unmap, before the `nr_vlpis` test; its
  per-ITS count is `vm->vlpi_count[]`, separate from `nr_vlpis`.
