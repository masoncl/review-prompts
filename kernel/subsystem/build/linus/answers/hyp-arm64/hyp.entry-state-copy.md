| State | Protected | Non-protected |
|---|---|---|
| `arch.ctxt` on entry | whole struct assigned from host | `__copy_vcpu_state()`, only if host has `PKVM_HOST_STATE_DIRTY` |
| `arch.ctxt` on exit | whole struct assigned to host | only `regs.pc` and `regs.pstate` |

- Everything else in `flush_hyp_vcpu()` and `sync_hyp_vcpu()`: same for both
  kinds.
- vgic on entry, `flush_hyp_vgic_state()`: `vgic_hcr`, `used_lrs` clamped to
  `hyp_gicv3_nr_lr`, and that many `vgic_lr[]`; `vgic_sre` is set to a
  constant, not taken from the host.
- vgic on exit, `sync_hyp_vgic_state()`: `vgic_hcr`, `vgic_vmcr`, and
  `vgic_lr[]` up to the hyp `used_lrs`.
- `arch.ctxt.__hyp_running_vcpu`: set to NULL after the copy;
  `arch/arm64/kvm/hyp/include/hyp/sysreg-sr.h` treats a non-NULL value as
  "this is the host context".
- `flush_debug_state()` with host-owned debug: also copies
  `external_mdscr_el1`, which the world switch loads as MDSCR_EL1.
- `arch.pid`: copied on entry; read by `arch/arm64/kvm/hyp/include/nvhe/trace.h`.
- `fpsimd_sve_sync()`: does nothing unless `guest_owns_fp_regs()`.
