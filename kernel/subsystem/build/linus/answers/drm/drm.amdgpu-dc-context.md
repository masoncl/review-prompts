- `DC_FP_START()` and `DC_FP_END()`: defined in
  `drivers/gpu/drm/amd/display/amdgpu_dm/dc_fpu.h`, which `dc/os_types.h`
  includes under `CONFIG_DRM_AMD_DC_FP`.
- In a file built with `_LINUX_FPU_COMPILATION_UNIT`: both macros are
  `BUILD_BUG()`.
- `dc_fpu_begin()`: calls `preempt_disable()` itself, then `kernel_fpu_begin()`
  at depth 1; `dc_fpu.c` has no per-architecture branches.
- `dc_fpu_begin()` outside task context: `WARN_ON_ONCE(!in_task())` fires and
  the function carries on, so an interrupt handler must not open an FP
  section.
- `DC_RUN_WITH_PREEMPTION_ENABLED()` in `dc_fpu.h`: closes an open FP section
  around one statement and reopens it; `dml2_allocate_memory()` uses it for
  `vzalloc()`.

| Handler | Registered by | Context |
|---|---|---|
| `dm_vupdate_high_irq()` | DCE (only when `dc_supports_vrr()`) and DCN | interrupt |
| `dm_crtc_high_irq()` | `amdgpu_dm_dce110_register_irq_handlers()` only | interrupt |
| `dm_pflip_high_irq()` | `amdgpu_dm_dce110_register_irq_handlers()` only | interrupt |
| `dm_dcn_vertical_interrupt0_high_irq()` | DCN, under `CONFIG_DRM_AMD_SECURE_DISPLAY` | interrupt |
| `handle_hpd_irq()`, `handle_hpd_rx_irq()`, `dm_dmub_outbox1_low_irq()` | `INTERRUPT_LOW_IRQ_CONTEXT` | work item |

- DCN: `dm_vupdate_high_irq()` calls `dm_crtc_high_irq_handler()`, which
  handles vblank and delivers page-flip completion.
- DRR update from the interrupt handlers: `schedule_dc_vmin_vmax()` queues
  `dm_handle_vmin_vmax_update()`, which calls `dc_stream_adjust_vmin_vmax()`
  under the `dc_lock` mutex.
- The `set_drr` hook is still reached with the `event_lock` spinlock held, from
  `amdgpu_dm_commit_planes()` and `amdgpu_dm_update_freesync_state_on_stream()`.
- `generic_reg_wait()`: calls `msleep()` when `delay_between_poll_us` is 1000 or
  more, `udelay()` below that.
- **Unsafe usage**: a sleeping delay (`msleep()`, `usleep_range()`, `fsleep()`)
  in a hardware sequencer function that has a caller holding a spinlock,
  running from an `INTERRUPT_HIGH_IRQ_CONTEXT` handler or inside
  `DC_FP_START()`.
  - Safe: `udelay()`, or `generic_reg_wait()` with an interval below 1000.
  - Safe: defer the call to a work item, as `schedule_dc_vmin_vmax()` does.
