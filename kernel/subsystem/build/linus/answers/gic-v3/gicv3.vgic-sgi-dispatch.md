- Targeted mode: `vgic_v3_dispatch_sgi()` itself does not walk the vCPUs and
  there is no match_mpidr() in this tree; each set bit of the 16-bit list is
  one `kvm_mpidr_to_vcpu()` lookup, and a NULL result is skipped.
- RS field: not read; `ICC_SGI1R_RS_MASK` is not referenced under
  `arch/arm64/kvm`, so only Aff0 values 0 to 15 can be targeted.
- Group argument: set by `access_gic_sgi()` in `arch/arm64/kvm/sys_regs.c`,
  from `Op2` for AArch64 and `Op1` for AArch32.

| Register | `allow_group1` | May raise |
|---|---|---|
| `SYS_ICC_SGI1R_EL1` | true | Group 0 or Group 1 |
| `SYS_ICC_ASGI1R_EL1` | false | Group 0 only |
| `SYS_ICC_SGI0R_EL1` | false | Group 0 only |

- Group test in `vgic_v3_queue_sgi()`: `!irq->group || allow_group1`; it is
  not a match between the register and `irq->group`.
- Group test and broadcast: `vgic_v3_queue_sgi()` applies it per target in
  both modes, and before the `irq->hw` branch.
- IRQ lookup: `vgic_get_vcpu_irq()`, not `vgic_get_irq()`.
- Hardware-backed SGI (`irq->hw`): `vgic_v3_queue_sgi()` calls
  `irq_set_irqchip_state()` on `irq->host_irq` with `IRQCHIP_STATE_PENDING`;
  no function of `arch/arm64/kvm/vgic/vgic-v4.c` is on this path.
- Hardware-backed SGI: `pending_latch` is not set and
  `vgic_queue_irq_unlock()` is not called; a failure only gives
  `WARN_RATELIMIT()`.
