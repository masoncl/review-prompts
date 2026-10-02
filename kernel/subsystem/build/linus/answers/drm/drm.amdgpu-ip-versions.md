- `amdgpu_ip_version()` in `drivers/gpu/drm/amd/amdgpu/amdgpu.h`: masks off the
  low 8 bits of `adev->ip_versions[ip][inst]`, which are the variant (bits 7:4)
  and the sub-revision (bits 3:0).
- Instance: not left out; it is the `inst` argument.
- PSP firmware version: `adev->psp.sos.fw_version`, a `struct psp_bin_desc`
  member of `struct psp_context`.
- `sos_fw_version` is not a field; that name is only a sysfs attribute in
  `amdgpu_ucode.c` that reads `psp.sos.fw_version`.
- Gate pattern: test the IP version, then compare `fw_version` with a literal
  minimum for that IP.

| Function in `amdgpu_psp.c` | IP tested | Firmware tested | When the gate fails |
|---|---|---|---|
| `psp_update_fw_reservation()` | `MP0_HWIP` | `sos.fw_version` | returns 0, sends nothing |
| `amdgpu_ptl_perf_monitor_ctrl()` | `GC_HWIP` | `sos.fw_version` | returns `-EOPNOTSUPP` |
| `psp_load_p2s_table()` | `MP0_HWIP` | `sos.fw_version` | returns 0, skips the load |
| `psp_xgmi_peer_link_info_supported()` | `MP0_HWIP` | XGMI TA `bin_desc.fw_version` | returns `false` |

- Minimum versions are per IP: in `psp_update_fw_reservation()` the threshold
  for MP0 14.0.3 is lower than the one for 14.0.2.
- `psp_xgmi_peer_link_info_supported()`: also true for any MP0 at or above
  `IP_VERSION(13, 0, 6)`, with no firmware version test.
- `psp_xgmi_peer_link_info_supported()` does not test capability flags.
- XGMI TA capability flags: `psp_xgmi_initialize()` stores them in
  `xgmi_ta_caps` and, except on an SR-IOV VF, derives
  `supports_ext_link_info` from them; `psp_xgmi_get_topology_info()` uses the
  latter to choose between two commands.
- `psp_cmd_submit_buf()`: returns 0 when the firmware answers with a non-zero
  `resp.status`, except on timeout or for a ucode load on an SR-IOV VF.
- A caller that needs to know the command was rejected has to read
  `cmd->resp.status`, as `psp_get_fw_reservation_info()` does for
  `PSP_ERR_UNKNOWN_COMMAND`.
