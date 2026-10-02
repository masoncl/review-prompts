- Existing BO in `*bo_ptr`: `amdgpu_bo_create_reserved()` reserves it, binds
  GART, reads the address and maps it; it does not pin it again.
- `amdgpu_bo_pin()`: called only for a BO this call created.
- `size`, `align` and `domain`: not compared with the existing BO.
- `size == 0`: `amdgpu_bo_create_reserved()` calls `amdgpu_bo_unref(bo_ptr)` and
  returns 0, so an existing BO loses a reference without being unpinned and
  `*bo_ptr` becomes NULL.
- Success with `*bo_ptr == NULL` is therefore possible;
  `amdgpu_bo_create_kernel()` and `amdgpu_bo_create_kernel_at()` test for it.
- **Potentially unsafe usage**: calling either function with `*bo_ptr` not
  NULL.
  - Unsafe: when the target is uninitialised or points at a freed BO;
    `amdgpu_bo_reserve()` then dereferences it.
  - Safe: when it is the live BO from an earlier call, as in
    `gfx_v10_0_cp_gfx_load_pfp_microcode()`, whose `pfp_fw_obj` is set to NULL
    by `amdgpu_bo_free_kernel()` when that frees the BO.
  - Safe: when the wrapper clears it first, as `isp_kernel_buffer_alloc()` does.
- `isp_kernel_buffer_alloc()` in `amdgpu_isp.c`: writes `*bo = NULL` through the
  caller's `buf_obj` before calling `amdgpu_bo_create_kernel()`; it uses no
  local pointer.
- A BO the caller's handle held on entry to `isp_kernel_buffer_alloc()`: is
  overwritten, not freed.
- `isp_user_buffer_alloc()`: passes the address of an uninitialised local;
  `amdgpu_bo_create_isp_user()` assigns `*bo` before reading it.
