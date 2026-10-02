| Situation | Thaw callbacks run | `pm_hibernate_is_recovering()` |
|---|---|---|
| image created by `hibernation_snapshot()` | `PMSG_THAW`: noirq, early, main | false |
| `swsusp_arch_suspend()` returned an error | `PMSG_RECOVER`: noirq, early, main | true |
| late or noirq phase of `PMSG_FREEZE` or `PMSG_QUIESCE` failed and unwinds | `PMSG_RECOVER`: `->thaw_early`, after `->thaw_noirq` when the noirq phase failed; the caller picks the message for the main phase | true |
| any other failure from `dpm_suspend(PMSG_FREEZE)` on, before `swsusp_arch_suspend()`, with `in_suspend` 0 on entry | none; `PMSG_RESTORE` runs `->restore` | false |
| boot kernel, `hibernation_restore()` failed | `PMSG_RECOVER`: main, after noirq and early if those phases were reached | true |
| `hibernate_quiet_exec()`, whatever `func` returns | `PMSG_THAW`: noirq, early, main | false |

- `hibernate_quiet_exec()`: the system keeps running after its `PMSG_THAW`;
  `drivers/nvdimm/core.c` calls it.
- Outside the hibernation core: `do_suspend()` in `drivers/xen/manage.c`
  sends `PMSG_THAW` when the suspend was cancelled, and the system keeps
  running.
- `pm_hibernate_is_recovering()`: defined in `drivers/base/power/main.c`;
  it reads `pm_transition`, which only the six suspend and resume phase
  functions write and nothing clears.
- In `->prepare`, and in `->complete` when the caller goes straight to
  `dpm_complete()` after a failed `dpm_prepare()`, as
  `hibernation_snapshot()` does, `pm_hibernate_is_recovering()` reports the
  last phase of an earlier transition.
- `swsusp_write()` failure after a normal thaw: `hibernate()` sends no
  further device message; only the `PM_POST_HIBERNATION` notifier follows.
- **Potentially unsafe usage**: a `->thaw` that returns 0 without resuming
  the hardware.
  - Unsafe: when the system keeps running after the thaw, because nothing
    later resumes the device: `PMSG_RECOVER`, `PMSG_THAW` from
    `hibernate_quiet_exec()`, or `swsusp_write()` failing.
  - Unsafe: in `HIBERNATION_SUSPEND` mode, where `power_down()` calls
    `suspend_devices_and_enter()` and `->prepare` and `->suspend` run on
    the device next.
  - Unsafe: in `HIBERNATION_TEST_RESUME` mode unless `->freeze` accepts a
    device that is still frozen; `hibernation_restore()` sends
    `PMSG_QUIESCE` to the same kernel.
  - Unsafe: when `swsusp_write()` needs the device to reach the image.
  - Safe: when the message is `PMSG_THAW` from `hibernation_snapshot()`,
    `swsusp_write()` then succeeds, the mode is not suspend or
    test_resume, and the callbacks that run next accept a frozen device;
    `amdgpu_pmops_thaw()` in `drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c`
    skips only when `pm_hibernate_is_recovering()` and
    `pm_hibernation_mode_is_suspend()` are both false.
  - Safe: the callbacks that follow return early for the frozen device, as
    `amdgpu_pmops_prepare()`, `amdgpu_pmops_poweroff()` and
    `amdgpu_pci_shutdown()` do on `adev->in_s4 && adev->in_suspend`;
    `amdgpu_device_pm_notifier()` sets `in_s4`.
