- `sector_buf`: a member of `struct ata_device`, reached as
  `dev->sector_buf`; `struct ata_port` has no such member.
- ap->ncq_sense_buf: not in this tree; the two-sector buffer is
  `ncq_sense_log_buf` in `struct ata_cdl`, reached through `dev->cdl`, used by
  `ata_eh_get_ncq_success_sense()`.
- `ata_log_supported()`: reads the log directory into `dev->gp_log_dir` and
  caches it there; it does not touch `dev->sector_buf`.
- Memory type is defined by `sg_set_buf()` in `include/linux/scatterlist.h`:
  it calls `virt_to_page()` on `buf`, and under `CONFIG_DEBUG_SG` it does
  `BUG_ON(!virt_addr_valid(buf))`; this holds for PIO commands too.
- Lifetime: `buf` is needed only until `ata_exec_internal()` returns, on a
  timeout as well; `__ata_qc_complete()` unmaps it before the return.
- **Unsafe usage**: passing a buffer outside the kernel linear map (a stack
  array under `CONFIG_VMAP_STACK`, `vmalloc()` memory) as `buf`.
  - Safe: `dev->sector_buf` with `sectors` of 1, as
    `ata_identify_page_supported()` does; `struct ata_device` lives inside the
    port or PMP link allocation, made with `kzalloc_obj()` in
    `ata_port_alloc()` and `kzalloc_objs()` in `sata_pmp_init_links()`, so it
    passes the `virt_addr_valid()` test in `sg_set_buf()`.
  - Safe: an own `kzalloc()` buffer of the transfer length, freed after the
    call on failure too, as `ata_dev_config_cpr()` and
    `zpodd_get_mech_type()` do.
  - Safe: a buffer inside a `kzalloc_obj()` structure, as
    `ata_dev_init_cdl_resources()` does with `cdl->desc_log_buf`.
