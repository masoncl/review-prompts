- `msm_context_vm()`: defined in `drivers/gpu/drm/msm/msm_drv.c`; returns NULL
  on failure, never an `ERR_PTR()`.
- `IS_ERR()` on its result: passes the NULL through; callers test `!vm`, as
  `msm_ioctl_gem_submit()` and `msm_ioctl_vm_bind()` do before
  `to_msm_vm(vm)->unusable`.
- Errno of the failure: lost. Callers return `UERR(ENOMEM, ...)` "no VM";
  `msm_gem_new_handle()` returns `-EINVAL`; `adreno_get_param()` accepts NULL.
- A failed creation is not cached: `ctx->vm` stays NULL and the next call
  tries again.
- Creation lock: `ctx->ctxlock` held for write, not a static mutex. The static
  `init_lock` in the same file belongs to `load_gpu()`.
- `msm_gpu_create_private_vm()` fallback to `gpu->vm`: only when
  `kernel_managed` is true. For a VM_BIND context a failing
  `create_private_vm` hook yields NULL from `msm_context_vm()`.
- `priv->gpu == NULL`: `msm_gpu_create_private_vm()` returns NULL, so callers
  may call `msm_context_vm()` before they test `priv->gpu`.
- `MSM_PARAM_EN_VM_BIND`: handled in `adreno_set_param()` in
  `drivers/gpu/drm/msm/adreno/adreno_gpu.c`, not in `msm_ioctl_set_param()`.
  The `-EINVAL` in that case tests for a missing `create_private_vm` hook; it
  does not compare `ctx->vm` with `gpu->vm`.
- **Potentially unsafe usage**: reading `ctx->vm` directly instead of calling
  `msm_context_vm()`.
  - Unsafe: on a path that needs a VM and can run before the first
    `msm_context_vm()` call on that context; the pointer is NULL and
    `to_msm_vm()` users dereference it.
  - Safe: `adreno_set_param()` for `MSM_PARAM_EN_VM_BIND`; it must not create
    the VM, and it holds `ctx->ctxlock` for read, which excludes creation
    under the write lock in `msm_context_vm()`.
  - Safe: `a6xx_set_pagetable()`; a `struct msm_gem_submit` exists only after
    `msm_ioctl_gem_submit()` got a non-NULL VM for the same context, and the
    queue holds a context reference from `msm_submitqueue_create()`.
  - Safe: `msm_gem_close()`; NULL means the context has no VM and so nothing
    to unmap. The NULL test is required: `put_iova_spaces()` with a NULL `vm`
    matches every VM and tears down other contexts' mappings.
  - Safe: `msm_submitqueue_close()`; it returns when `ctx->vm` is NULL, and
    it runs from `msm_postclose()`, after which no ioctl can create the VM.
  - Safe: `__msm_context_destroy()`; last reference, and `drm_gpuvm_put()`
    accepts NULL.
- `msm_kms_init_vm()` with no IOMMU on the MDP/DPU device or `mdss_dev`: logs
  "no IOMMU, bailing out" and returns `ERR_PTR(-ENODEV)`.
- `msm_kms_init_vm()` has no NULL return; every failure is an `ERR_PTR()`.
- Display init without IOMMU fails: the callers return `PTR_ERR(vm)`, dpu
  from `hw_init` (`dpu_kms_hw_init()`), mdp4 and mdp5 from `kms_init`
  (`mdp4_kms_init()`, `mdp5_kms_init()`); `msm_drm_kms_init()` fails, and
  `msm_drm_init()` unwinds through `msm_drm_uninit()`.
- No fallback to physically contiguous scanout: nothing under
  `drivers/gpu/drm/msm` has a vram carveout member or allocator.
- `kms->vm` NULL tests in the kms destroy paths (for example
  `mdp4_destroy()`'s `if (kms->vm)`): cover destroy after `kms_init` or
  `hw_init` failed before the VM was stored, not a running no-IOMMU mode.
- MMU constructor for display: `msm_iommu_disp_new()`, which wraps
  `msm_iommu_new()` and installs the display fault handler.
