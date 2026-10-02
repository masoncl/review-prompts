- VF detection: `test_is_vf()` reads MMIO register `VF_CAP_REG`, not PCI
  config, and only when `xe->info.has_sriov`.
- PF detection: `xe_sriov_pf_readiness()` in `xe_sriov_pf.c`; needs
  `dev_is_pf()` and a non-zero minimum of `xe_configfs_get_max_vfs()` and
  the PCI total VFs; without `CONFIG_PCI_IOV` it is a stub returning false.
- `xe_configfs_get_max_vfs()`: the configfs value, falling back to the
  `max_vfs` module parameter.
- `XE_SRIOV_MODE_NONE` is 1; `xe->sriov.__mode == 0` means not probed yet.
- `vf_update_device_info()` in `xe_device.c`: runs in
  `xe_device_probe_early()` after `xe_sriov_probe_early()`; sets
  `xe->info.skip_pcode` and `xe->info.skip_guc_pc` and clears
  `probe_display` and other feature flags. There is no xe_pcode_init().
- `xe_wa_process_device_oob()` runs before `xe_sriov_probe_early()`, so
  device OOB workaround rules cannot match on VF mode; see the FIXME in
  `wa_14026539277()` in `xe_gt.c`.
- **Unsafe usage**: testing `IS_SRIOV_VF()` before
  `xe_sriov_probe_early()` has run.
  - Unsafe: `xe_device_sriov_mode()` asserts only under
    `CONFIG_DRM_XE_DEBUG`; otherwise the test silently returns false on a
    VF.
  - Safe: after `xe_sriov_probe_early()` has set `xe->sriov.__mode`, as
    the test before `vf_update_device_info()` in
    `xe_device_probe_early()`.
- **Potentially unsafe usage**: a probe step that reads or writes a
  register a VF cannot reach.
  - Unsafe: with no `IS_SRIOV_VF()` test and the value used for a
    decision; `xe_mmio_read32()` does no MMIO on a VF for a register
    without `XE_REG_OPTION_VF`, it returns 0 from `xe_gt_sriov_vf_read32()`
    when the PF did not supply the register, and `xe_mmio_write32()` drops
    the write; both warn only under `CONFIG_DRM_XE_DEBUG`.
  - Safe: return early for a VF before the access, as
    `xe_hwmon_register()`, `detect_preproduction_hw()` and
    `probe_has_flat_ccs()` do.
  - Safe: the register is defined with `XE_REG_OPTION_VF`, as `VF_CAP_REG`
    is.
  - Safe: forcewake; `__domain_ctl()` and `__domain_wait()` in
    `xe_force_wake.c` do nothing on a VF, so the get reports success.
  - Safe: the caller has excluded a VF and the callee only asserts it with
    `xe_gt_assert(gt, !IS_SRIOV_VF(...))`, as
    `xe_gt_mcr_unicast_read_any()` under `probe_has_flat_ccs()`; the assert
    is compiled out without `CONFIG_DRM_XE_DEBUG`.
- **Potentially unsafe usage**: calling `xe_pcode_read()` on a path a VF
  can reach.
  - Unsafe: when the output is used without being initialised first; with
    `xe->info.skip_pcode` `pcode_mailbox_rw()` returns 0 and leaves the
    output untouched.
  - Safe: the output is initialised before the call, as `max_freq_show()`
    in `xe_vram_freq.c` does.
  - Safe: the caller is never reached on a VF, as the hwmon callbacks,
    since `xe_hwmon_register()` returns early for a VF.
- Setup skipped for a VF needs the same test in its teardown:
  `xe_pm_runtime_init()` and `xe_pm_runtime_fini()` both return early.
