- `REG_RAZ`: tested only by `sysreg_visible_as_raz()` in
  `__kvm_read_sanitised_id_reg()` and `arm64_check_features()`, both for ID
  registers; `perform_access()`, `kvm_sys_reg_get_user()` and
  `kvm_sys_reg_set_user()` do not test it.
- `REG_RAZ` on an ID register whose `.reset` is
  `kvm_read_sanitised_id_reg()`: the reset value is 0, so guest and userspace
  read 0; a non-zero userspace write, before the VM has run and without
  `REG_USER_WI`, fails with `-EINVAL` from `set_id_reg()`.
- `REG_RAZ` and guest writes: nothing ignores them; `access_id_reg()` treats a
  write as `write_to_read_only()`, which injects UNDEF.
- `REG_RAZ | REG_USER_WI`: returned by `aa32_id_visibility()`; `REG_RAZ` is not
  combined with `REG_HIDDEN` anywhere.
- There is no user_visibility hook; `REG_USER_WI` from `.visibility` is the
  userspace-only flag, and `kvm_sys_reg_set_user()` returns 0 on it before
  `.set_user` runs.
- `kvm_sys_reg_table_init()`: also checks the GICv3 table returned by
  `vgic_v3_get_sysreg_table()`.
- `check_sysreg_table()` reset check (`.reg` set but no `.reset`): applied only
  when `reset_check` is true, which is `sys_reg_descs` only.
- pKVM table `pvm_sys_reg_descs` in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`:
  checked by `kvm_check_pvm_sysreg_table()`; a failure hits `BUG_ON()` in
  `arch/arm64/kvm/hyp/nvhe/setup.c`.
