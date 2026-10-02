- `ICC_IAFFIDR_EL1`: `access_gicv5_iaffid()` in `arch/arm64/kvm/sys_regs.c`
  returns `vcpu->vcpu_id` in the `IAFFID` field; a write gets
  `undef_access()`.
- `ICC_IDR0_EL1`: only `PRI_BITS` and `ID_BITS` are filled; every other bit,
  `ICC_IDR0_EL1_GCIE_LEGACY` included, reads 0.
- `vgic_v5_reset()`: stores two constants and reads no host register.
  `num_id_bits` is `ICC_IDR0_EL1_ID_BITS_16BITS` (raw field value 0, the
  lowest encoding); `num_pri_bits` is the count 5.
- Userspace: no path writes either field for a GICv5 VM.
  `vgic_v5_set_attr()` in `arch/arm64/kvm/vgic/vgic-kvm-device.c` returns
  `-ENXIO` for `KVM_DEV_ARM_VGIC_GRP_CPU_SYSREGS`; `vgic_v5_reset()` is the
  only writer.
- **Unsafe usage**: storing a bit count in `num_id_bits`, or a raw field value
  in `num_pri_bits`.
  - Unsafe: `access_gicv5_idr0()` emits `num_id_bits` unchanged and
    `num_pri_bits - 1`, so the guest reads the wrong width.
  - Safe: raw value for ID bits and count for priority bits, as
    `vgic_v5_reset()` does; count 5 gives `ICC_IDR0_EL1_PRI_BITS_5BITS`.
- **Unsafe usage**: letting a GICv5 vCPU enter the guest while `num_pri_bits`
  is still 0.
  - Unsafe: `num_pri_bits - 1` wraps and `access_gicv5_idr0()` returns
    `PRI_BITS` as all ones.
  - Safe: set the field from `vgic_init()`, which calls `vgic_v5_reset()` for
    every vCPU with `kvm->arch.config_lock` asserted.
    `kvm_arch_vcpu_precreate()` refuses new vCPUs once `vgic_initialized()`,
    and `vgic_v5_map_resources()` returns `-EBUSY` at first run until then.
- **Unsafe usage**: emulating a GICv5 register value while only
  `__compute_fgt()` computes its trap bit.
  - Unsafe: a GICv5 guest has no FGU bits in the GICv5 groups, so the bit
    stays set, the access does not trap and the guest reads the hardware
    value.
  - Safe: clear the bit after `__compute_fgt()`, as `__compute_ich_hfgrtr()`
    does for `ICH_HFGRTR_EL2_ICC_IDRn_EL1`.
- **Unsafe usage**: a userspace setter that lets `num_pri_bits` or
  `num_id_bits` grow past the value reset stored.
  - Safe: return `-EINVAL` for a value greater than the stored one, as
    `set_gic_ctlr()` in `arch/arm64/kvm/vgic-sys-reg-v3.c` does for GICv3.
