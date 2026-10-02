- Outside callers: found by searching for `mfd_add_devices()`,
  `devm_mfd_add_devices()` and `mfd_add_hotplug_devices()` outside
  `drivers/mfd/`. For example `drivers/misc/cardreader/rtsx_pcr.c`,
  `drivers/soc/samsung/exynos-pmu.c` and
  `drivers/gpu/drm/amd/amdgpu/amdgpu_acp.c`.
- No file under `sound/`, `drivers/pci/`, `drivers/gpio/` or
  `drivers/platform/chrome/` calls any of those three functions.
- `select MFD_CORE` outside `drivers/mfd/Kconfig` does not mark a caller. For
  example `GPIO_VX855` and `GPIO_RDC321X` in `drivers/gpio/Kconfig` select it
  for child drivers that register nothing.
- `mfd_get_cell()`: inline, so a child driver that only calls it, such as
  `drivers/platform/chrome/cros_kbd_led_backlight.c`, links without
  `MFD_CORE`.
- The select belongs on the symbol that builds the calling file: the `bool`
  sub-options `DRM_AMD_ACP` and `DRM_AMD_ISP` of the amdgpu module for the
  amdgpu files, `POLARFIRE_SOC_SYSCONS` for the two files in
  `drivers/soc/microchip/`.
- `MFD_NVEC`: defined in `drivers/staging/nvec/Kconfig`, not in
  `drivers/mfd/Kconfig`, despite its name.
