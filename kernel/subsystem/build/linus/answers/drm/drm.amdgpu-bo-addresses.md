- `amdgpu_bo_gpu_offset()` for VRAM: `vram_start` plus the resource offset, an
  MC address; `vram_base_offset` is not part of it.
- `amdgpu_bo_gpu_offset()` for GTT: the AGP aperture address when
  `amdgpu_gmc_agp_addr()` finds one, otherwise `gart_start` plus the offset.
- `amdgpu_bo_gpu_offset()` warning for an unlocked, unpinned BO: does not fire
  for `ttm_bo_type_kernel`.
- `amdgpu_gmc_pd_addr()` at `CHIP_VEGA10` and later: a PDE, the address from
  `amdgpu_gmc_get_pde_for_bo()` with flag bits in the low bits.
- `amdgpu_gmc_pd_addr()` below `CHIP_VEGA10`: returns `amdgpu_bo_gpu_offset()`
  unchanged.
- PDE address for a VRAM page directory: the MC address minus `vram_start`
  plus `vram_base_offset`; for example `gmc_v9_0_get_vm_pde()` calls
  `amdgpu_gmc_vram_mc2pa()` for it, and `gmc_v12_0_get_vm_pde()` open-codes
  the same sum.
- PDE address for a GTT page directory: `dma_address[0]`, not a GART address.
- PDE flags: come from `amdgpu_ttm_tt_pde_flags()`, which overwrites the
  `AMDGPU_PTE_VALID` that `amdgpu_gmc_pd_addr()` starts with; GTT adds
  `AMDGPU_PTE_SYSTEM`.
- Debugfs: the per-client file `vm_pagetable_info`, read by
  `amdgpu_pt_info_read()` in `amdgpu_debugfs.c`, prints `pd_address` as
  `amdgpu_gmc_pd_addr()` of the root BO.
- `pd_address` in that file at `CHIP_VEGA10` and later: has flag bits set and
  is not an MC address.
- `amdgpu_amdkfd_gpuvm_get_process_page_dir()`: returns the stored
  `amdgpu_gmc_pd_addr()` value, shifted right by `AMDGPU_GPU_PAGE_SHIFT` below
  `CHIP_VEGA10`.
