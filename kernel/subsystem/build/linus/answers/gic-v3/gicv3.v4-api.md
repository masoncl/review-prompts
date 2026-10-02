- `enum its_vcpu_info_cmd_type` in `include/linux/irqchip/arm-gic-v4.h`: the
  vPE commands are `SCHEDULE_VPE`, `DESCHEDULE_VPE`, `COMMIT_VPE` and
  `INVALL_VPE`; the only vSGI command is `PROP_UPDATE_VSGI`.
- `its_unmap_vlpi()`: carries no command; it passes NULL, which
  `its_irq_set_vcpu_affinity()` tests before the switch and hands to
  `its_vlpi_unmap()`.
- Doorbell receiver: `its_vpe_set_vcpu_affinity()` for `its_vpe_irq_chip`,
  `its_vpe_4_1_set_vcpu_affinity()` for `its_vpe_4_1_irq_chip`;
  `its_vpe_irq_domain_alloc()` picks the chip from `has_rvpeid`.
- `irq_set_vcpu_affinity()` in `kernel/irq/manage.c`: holds the irq's
  `irq_desc` lock across the receiver, and walks up the hierarchy to the first
  chip that has the callback.
- vLPI INT and CLEAR take another route: `irq_set_irqchip_state()` on the host
  irq reaches `its_irq_set_irqchip_state()`, which calls `its_send_vint()` or
  `its_send_vclear()` when `irqd_is_forwarded_to_vcpu()`.
- Doorbell pending state: only `its_vpe_irq_chip` has
  `its_vpe_set_irqchip_state()`; `its_vpe_4_1_irq_chip` has no
  `irq_set_irqchip_state` member.
- Preemption disabled: `its_make_vpe_resident()`,
  `its_make_vpe_non_resident()` and `its_commit_vpe()` each do
  `WARN_ON(preemptible())` and then carry on; no other function in
  `drivers/irqchip/irq-gic-v4.c` has the check.
- Reason for the three: their receivers address the current CPU's
  redistributor through `gic_data_rdist_vlpi_base()`.
- `its_invall_vpe()`: no preemption check.
