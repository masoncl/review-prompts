| Job | Where in this tree | Easy to miss |
|---|---|---|
| Buddy allocator | `drivers/gpu/buddy.c`, `include/linux/gpu_buddy.h`, `CONFIG_GPU_BUDDY` | The API is `struct gpu_buddy`, `gpu_buddy_init()`, `gpu_buddy_alloc_blocks()`. `drivers/gpu/drm/drm_buddy.c` and `include/drm/drm_buddy.h` still exist but hold only `drm_buddy_print()` and `drm_buddy_block_print()`. There is no drm_buddy_init() and no struct drm_buddy. |
| Compute accelerator core | `drivers/accel/drm_accel.c`, `include/drm/drm_accel.h` | No drm_accel.c under `drivers/gpu/drm/`; `drivers/gpu/drm/Makefile` links the file into `drm.o` under `CONFIG_DRM_ACCEL`. |
| Atomic core | `drivers/gpu/drm/drm_atomic.c`, `include/drm/drm_atomic.h` | There is no struct drm_atomic_state here; the type is `struct drm_atomic_commit`, with `drm_atomic_commit_alloc()` and `drm_atomic_commit_put()`. |
| GPU scheduler | `drivers/gpu/drm/scheduler/` | Run-queue code, for example `drm_sched_rq_add_entity()` and `drm_sched_rq_select_entity()`, is defined in `sched_rq.c`; `sched_main.c` and `sched_entity.c` only call it. |
| Locking helper for many buffer objects | `drivers/gpu/drm/drm_exec.c` | `drivers/gpu/drm/ttm/ttm_execbuf_util.c` still exists beside it. |
| Vblank handling | `drivers/gpu/drm/drm_vblank.c`, `drm_vblank_work.c` | `drm_vblank_helper.c` is a third file, built into `drm_kms_helper`, with the vblank-timer and atomic enable/disable helpers. |
| In-kernel clients | `drivers/gpu/drm/drm_client.c` and `drivers/gpu/drm/clients/` | `drm_client_sysrq.c` is built with the other `drm_client` files under `CONFIG_DRM_CLIENT`. |
| Panic screen | `drivers/gpu/drm/drm_panic.c`, `drm_panic_qr.rs` | Drawing primitives are in `drm_draw.c` (`CONFIG_DRM_DRAW`), shared with `clients/drm_log.c`. |
| Rust abstractions | `rust/kernel/drm/` | Includes `gpuvm/` and `gem/shmem.rs`. The buddy binding is outside it, in `rust/kernel/gpu/buddy.rs`. C shims are `rust/helpers/drm.c`, `rust/helpers/drm_gpuvm.c` and `rust/helpers/gpu.c`. `drivers/gpu/drm/nova/` is built from `drivers/gpu/Makefile`, not `drivers/gpu/drm/Makefile`. |
