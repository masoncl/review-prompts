- Flag bits: `vgic_mmio_read_v3r_typer()` sets only `GICR_TYPER_PLPIS` (when
  `vgic_has_its()`) and `GICR_TYPER_LAST`; `GICR_TYPER_VLPIS` is not set, on
  any host.
- Affinity field: `kvm_vcpu_get_mpidr_aff()` masked with `GENMASK(23, 0)`,
  so Aff3 reads as zero.
- Region pointer: `rdreg` in `struct vgic_cpu`, with `rdreg_index`; there is
  no rdist_region field.
- `vgic_mmio_vcpu_rdist_is_last()` does not look at `kvm->online_vcpus`.
- Last, first test: `rdreg` NULL gives false.
- Last, step 1: `rdreg_index < rdreg->free_index - 1` gives false.
- Last, step 2: for `count != 0` and `rdreg_index == count - 1`, the walk over
  `rd_regions` gives false if a region has `base` equal to the end of this
  one and `free_index > 0`.
- Last, step 3: true otherwise, including the highest registered index of a
  region that is not full.
- `rdreg` NULL again: `vgic_v3_free_redist_region()` clears it for every vCPU
  of the freed region, so Last reads clear from then on.
- Userspace read: the `GICR_TYPER` region has `uaccess_read` NULL, so
  `vgic_mmio_read_v3r_typer()` serves userspace too and Last is computed at
  read time.
- Userspace write: `vgic_mmio_uaccess_write_wi()`.
