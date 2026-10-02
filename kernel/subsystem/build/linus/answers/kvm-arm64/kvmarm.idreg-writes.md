- Limit: `rd->reset(vcpu, rd)`, computed again at each write; not the stored
  value and not the raw host value.
- Direction: set per field by its `struct arm64_ftr_bits` type through
  `kvm_arm64_ftr_safe_value()`, so not every field may only be lowered.
- Writable field: one whose whole `arm64_ftr_mask()` lies inside `rd->val`.
- Everything else must equal the limit bit for bit: fields outside the mask,
  fields partly inside it, and bits with no `struct arm64_ftr_bits`.
- Error code: `arm64_check_features()` returns `-E2BIG`; `set_id_reg()`
  returns `-EINVAL` to userspace in its place.
- No `struct arm64_ftr_reg` for the register: `-EINVAL`.
- RAZ register, before the VM has run: only 0 is accepted.
- Once the VM has run: the comparison is with the stored value, which
  includes the edits of `kvm_finalize_sys_regs()`, not with the limit.
- Custom setters run before `set_id_reg()`: their fix-ups apply to the value
  that is compared, and their `-EINVAL` comes before `-EBUSY`; see
  `set_id_aa64dfr0_el1()`.
