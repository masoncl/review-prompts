| Lock | Defined in | Protects |
|---|---|---|
| `vmapp_lock` | `struct its_vm` | `vlpi_count[]` of `struct its_vm` and the VMAPP sends decided from it; not `vmapp_count` |
| `vpe_lock` | `struct its_vpe` | `col_idx`; on GICv4.1 also `pending_last`, between `its_vpe_4_1_deschedule()` with `req_db` and `vgic_v4_doorbell_handler()` |
| `vmovp_lock` | one file-scope lock in `drivers/irqchip/irq-gic-v3-its.c` | `vmovp_seq_num` and the order of ITSList VMOVPs |
| `rd_lock` | per-CPU `rdist` of `struct rdists`, `include/linux/irqchip/arm-gic-v3.h` | a register write plus its poll on one redistributor: `GICR_INVLPIR` or `GICR_INVALLR` then `GICR_SYNCR`, `GICR_VSGIR` then `GICR_VSGIPENDR` |
| `vlpi_lock` | `struct event_lpi_map` | a device's `event_map.vm`, `nr_vlpis` and the `vlpi_maps` pointer; `its_irq_set_vcpu_affinity()` holds it across every request it handles |

- `vmapp_count`: an `atomic_t` in `struct its_vpe`, changed in
  `its_build_vmapp_cmd()`; no lock in this list covers it.
- `GICR_VPENDBASER` programming (`its_vpe_schedule()`,
  `its_vpe_deschedule()`, `its_vpe_4_1_schedule()`): takes no `rd_lock`.
- `vmovp_lock`: there is no per-VM lock of that name; `struct its_vm` has no
  such field.
- Written order: the comment above `vmapp_lock` in `struct its_vm`,
  `include/linux/irqchip/arm-gic-v4.h`: `vmapp_lock` -> `vpe_lock` ->
  `vmovp_lock`, for sequences that involve the ITSList.
- `rd_lock`, `vlpi_lock` and `vpe_proxy.lock`: not in that comment; their
  order is only in the code.
- `vlpi_lock` is outside `vmapp_lock`: `its_irq_set_vcpu_affinity()` ->
  `its_vlpi_map()` -> `its_map_vm()`.
- `rd_lock` is inside `vpe_lock` in `its_vpe_4_1_invall()`,
  `its_sgi_get_irqchip_state()` and `its_vpe_set_affinity()`.
- `__direct_lpi_inv()` on a physical LPI: takes `rd_lock` with no `vpe_lock`,
  because `irq_to_cpuid_lock()` locks nothing for that case.
- `its_vpe_invall()`: takes `vmapp_lock` whether or not `its_list_map` is set,
  and does not take `vpe_lock`.
- Not irqsave, for example: `vmapp_lock` in `its_vpe_set_affinity()`,
  `vmovp_lock` in `its_send_vmovp()`, and every `rd_lock` acquisition; they
  rely on interrupts being off already.
- irqsave: `vmapp_lock` in `its_map_vm()`, `its_unmap_vm()` and
  `its_vpe_invall()`.
