- Names: the RPL-U macro is `INTEL_RPLU_IDS()`; the display descriptor type
  is `struct subplatform_desc`. There is no INTEL_ADLP_RPLU_IDS() or
  struct intel_subplatform_info.
- `struct xe_subplatform_desc`: defined in
  `drivers/gpu/drm/xe/xe_pci_types.h`.
- Nested id macro (for example `INTEL_MTL_U_IDS()` inside `INTEL_MTL_IDS()`,
  `INTEL_DG2_G10_IDS()` inside `INTEL_DG2_IDS()`): new ids reach every table
  that expands the platform macro.
- Sibling id macro (for example `INTEL_WCL_IDS()`, `INTEL_RPLU_IDS()`,
  `INTEL_ADLN_IDS()`): needs its own line in each table that should match
  it: `intel_display_ids[]`, `pciidlist[]` in `drivers/gpu/drm/xe/xe_pci.c`,
  and where relevant `drivers/gpu/drm/i915/i915_pci.c`,
  `arch/x86/kernel/early-quirks.c` and `drivers/vfio/pci/xe/main.c`.
- Reason for a display subplatform: either code tests the subplatform bit in
  `display->platform`, for example `display->platform.meteorlake_u`, or the
  entry carries its own `STEP_INFO()` map, which `get_pre_gmdid_step()`
  prefers over the platform's. For example `alderlake_p_raptorlake_p` and
  `dg2_g10` have a step map and no `display->platform.` test in the tree.
- Own id macro without a subplatform: `INTEL_ARL_H_IDS()` and
  `INTEL_ARL_S_IDS()` have none in display; only `INTEL_ARL_U_IDS()` is
  folded into `meteorlake_u`.
- Display and xe sets differ:

| Variant | Display | xe |
|---|---|---|
| WCL | subplatform `pantherlake_wildcatlake` | plain `ptl_desc`, no subplatform |
| ADL-N | subplatform `alderlake_p_alderlake_n` | own platform, `adl_n_desc` |
| RPL-P | subplatform `alderlake_p_raptorlake_p` | `adl_p_desc`, no subplatform |
| MTL-U, ARL-U | subplatform `meteorlake_u` | plain `mtl_desc` |
| BMG G21 | none | `XE_SUBPLATFORM_BATTLEMAGE_G21` |

- PHY example: `intel_encoder_is_c10phy()` in
  `drivers/gpu/drm/i915/display/intel_cx0_phy.c` returns true for
  `phy <= PHY_B` on `display->platform.pantherlake_wildcatlake` and only for
  `PHY_A` on other `display->platform.pantherlake`.
- WCL display IP: also has its own `gmdid_display_map[]` entry (30.02), so
  in-tree code tests either the subplatform bit or
  `DISPLAY_VERx100(display) == 3002`.
