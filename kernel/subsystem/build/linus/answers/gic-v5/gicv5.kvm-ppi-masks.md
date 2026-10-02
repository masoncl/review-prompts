All bitmaps are `VGIC_V5_NR_PRIVATE_IRQS` (64) bits and indexed by bare ID.

| Bitmap | Stored in | Computed by, when |
|---|---|---|
| `impl_ppi_mask` | `kvm_vgic_global_state.vgic_v5_ppi_caps` | `vgic_v5_get_implemented_ppis()` at probe; no register is read: five fixed PPIs, plus `GICV5_ARCH_PPI_PMUIRQ` if `system_supports_pmuv3()` |
| `userspace_ppis` | `struct vgic_v5_vm` | `vgic_v5_init()`, at `KVM_DEV_ARM_VGIC_CTRL_INIT` |
| `vgic_ppi_mask` | `struct vgic_v5_vm` | `vgic_v5_finalize_ppi_state()`, first vCPU run |
| `vgic_ppi_hmr` | `struct vgic_v5_vm` | same; bit set means level, from `irq->config` |
| `vgic_ppi_dvir` | `struct vgic_v5_cpu_if` | `vgic_v5_set_ppi_dvi()`, on map and unmap of a physical interrupt |
| `vgic_ppi_enabler` | `struct vgic_v5_cpu_if` | `access_gicv5_ppi_enabler()` in `arch/arm64/kvm/sys_regs.c`, on a trapped guest write, anded with `vgic_ppi_mask` |
| `vgic_ppi_activer` | `struct vgic_v5_cpu_if` | `vgic_v5_fold_ppi_state()`, at exit |
| `pendr` | `vgic_v5_ppi_state` in `struct kvm_host_data` | `vgic_v5_flush_ppi_state()` before entry; overwritten by `__vgic_v5_save_ppi_state()` at exit |
| `activer_exit` | `vgic_v5_ppi_state` in `struct kvm_host_data` | `__vgic_v5_save_ppi_state()`, at exit |

- `vgic_ppi_hmr`: written only; nothing in this tree reads it.
- `for_each_visible_v5_ppi()`: defined in `arch/arm64/kvm/vgic/vgic.h`; walks
  `vgic_ppi_mask`.
- `vgic_ppi_mask` before the first vCPU run: all zeroes, so the loop body
  never runs.
- `vgic_v5_finalize_ppi_state()`: the one loop over `impl_ppi_mask`, because
  it is what builds `vgic_ppi_mask`.
- **Potentially unsafe usage**: dereferencing the result of
  `vgic_get_vcpu_irq()` in a PPI loop with no `NULL` test.
  - Unsafe: when the loop passes the bare index, or an index of 64 or more;
    the lookup returns `NULL`.
  - Safe: index from a `for_each_set_bit()` over a 64-bit PPI mask, passed
    through `vgic_v5_make_ppi()`, as `vgic_v5_flush_ppi_state()` does;
    `__irq_is_ppi()` defines the bound and `private_irqs[]` has 64 entries.
