- `ledtrig_flash_ctrl()` and `ledtrig_torch_ctrl()`: no caller in this tree.
- `ledtrig_disk_activity()`: the only caller is `ata_qc_complete()` in
  `drivers/ata/libata-core.c`; no other block driver calls it.
- `ledtrig_cpu()` idle callers: only `arch_cpu_idle_enter()` and
  `arch_cpu_idle_exit()` in `arch/arm/kernel/process.c`.
- `CPU_LED_IDLE_START`: sent from `do_idle()` after `local_irq_disable()`.
- `CPU_LED_IDLE_END`: sent from `do_idle()` after `cpuidle_idle_call()` or
  `cpu_idle_poll()` has re-enabled local interrupts.
- `suspend_cpu()` in `drivers/firmware/psci/psci_checker.c`: also calls
  `arch_cpu_idle_enter()` and `arch_cpu_idle_exit()`, both with local
  interrupts disabled.
- `CONFIG_LEDS_TRIGGER_CPU`: depends on `!PREEMPT_RT` in
  `drivers/leds/trigger/Kconfig`.
- Per-CPU triggers: `ledtrig_cpu_init()` registers them only for CPUs 0 to 7.
- `ledtrig_cpu()` on a CPU numbered 8 or higher: `_trig` is NULL, so
  `led_trigger_event()` returns at once; the CPU still counts toward the
  shared `cpu` trigger.
- `ledtrig_backlight_blank()`: a hook of the same family, called from
  `drivers/video/fbdev/core/fbmem.c`; it takes
  `ledtrig_backlight_list_mutex`, so unlike the other hooks it may sleep.
