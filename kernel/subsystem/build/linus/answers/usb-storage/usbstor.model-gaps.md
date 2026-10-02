- Models take DMA alignment to come from blk_queue_update_dma_alignment().
  That function is not in this tree; `usb_stor_host_template` sets
  `.dma_alignment = 511`.
- Models do not know that `uas_queuecommand_lck()` first returns
  `SCSI_MLQUEUE_DEVICE_BUSY` when `host_self_blocked` is set.
- Models do not know that `delay_use` is held in milliseconds:
  `usb_stor_probe2()` passes it to `msecs_to_jiffies()`, and
  `delay_use_set()` scales a bare number by 1000 and takes an "ms" suffix
  as is.
- Models do not know the `CONFIG_HIGHMEM` test in `usb_stor_probe1()`: with
  `CONFIG_HIGHMEM` enabled, a host controller without DMA or with
  `localmem_pool` gets `-EINVAL` through label `release`.
- Models do not know the LUN limit in `usb_stor_Bulk_max_lun()`: it returns 0
  for a byte above `US_BULK_MAX_LUN_LIMIT`.
- Models take queue callbacks to return int. `queuecommand_lck()` and
  `uas_queuecommand_lck()` return `enum scsi_qc_status`, with a literal 0 for
  success; see `DEF_SCSI_QCMD()` in `include/scsi/scsi_host.h`.
- Models do not know `kmalloc_obj()` and `kzalloc_obj()` from
  `include/linux/slab.h`; `associate_dev()` and, for example, `init_alauda()`
  allocate with them.
- Models name slave_alloc and slave_configure as template hooks.
  `struct scsi_host_template` has neither here; `usb_stor_host_template` sets
  `.sdev_init` and `.sdev_configure`.
