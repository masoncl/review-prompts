- `struct vgic_its_abi`: has no revision field; the revision is the index
  into `its_table_abi_versions[]`.
- `vgic_mmio_uaccess_write_its_iidr()`: returns `-EINVAL` when
  `rev >= NR_ITS_ABIS`; it reads only `GITS_IIDR_REV(val)` and ignores the
  other fields.
- Entry size check in `vgic_its_read_entry_lock()` and
  `vgic_its_write_entry_lock()`: a `BUILD_BUG_ON()` that the `sizeof` of the
  object passed equals `ABI_0_ESZ`, while `NR_ITS_ABIS == 1`.
- Run-time `KVM_BUG_ON()` returning `-EINVAL`: guarded by `NR_ITS_ABIS > 1`,
  so it never runs in this tree.
- Checked object: `*valp` for a read, `val` for a write, so a zero entry is
  written as `0ULL`; a plain `0` fails the build.
