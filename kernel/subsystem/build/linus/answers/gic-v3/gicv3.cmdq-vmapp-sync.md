- `its_build_vmapp_cmd()` computes `valid_vpe()` once at entry; that value
  is returned for a map on either version and for an unmap on GICv4.0.
- Only the unmap branch under `is_v4_1(its)` overwrites it with NULL.
- The version test is per ITS: `is_v4_1(its)` checks `GITS_TYPER_VMAPP` in
  the `typer` of the ITS receiving the command, not
  `gic_rdists->has_rvpeid`.
- On GICv4.0 the VSYNC after an unmap is still skipped when `valid_vpe()`
  returns NULL.
