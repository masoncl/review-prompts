| Kind | `pgmap->type`, set in | VMA | Inode | Folio |
|---|---|---|---|---|
| fsdax | `MEMORY_DEVICE_FS_DAX`; `pmem_attach_disk()`, `fs/fuse/virtio_fs.c`, `drivers/s390/block/dcssblk.c` | `vma_is_fsdax()` | `IS_DAX()`, not `S_ISCHR()` | `folio_is_fsdax()` |
| device DAX, `DAXDRV_DEVICE_TYPE` | `MEMORY_DEVICE_GENERIC`; `dev_dax_probe()` | `vma_is_dax()` and not `vma_is_fsdax()` | `IS_DAX()` and `S_ISCHR()` | no helper; `folio_is_fsdax()` false |
| fsdev, `DAXDRV_FSDEV_TYPE` | `MEMORY_DEVICE_FS_DAX`; `fsdev_dax_probe()` in `drivers/dax/fsdev.c` | none on the char device: `fsdev_fops` has no mmap handler | char device; `fsdev_open()` does not set `S_DAX` | `folio_is_fsdax()` true |
| kmem, `DAXDRV_KMEM_TYPE` | no pgmap used; `__add_memory_driver_managed()` in `dax_kmem_do_hotplug()` | ordinary | none | ordinary |

- `enum dax_driver_type` in `drivers/dax/bus.h`: three values, not two.
- `pgmap->type` follows the bound driver, not the device: on a static region
  `dev_dax_probe()` and `fsdev_dax_probe()` write the type into the same
  bus-owned `dev_dax->pgmap`.
- `folio_is_fsdax()` true: does not prove a block-device filesystem owns the
  folio; an fsdev-bound DAX-bus device gives the same answer.
- `folio_is_fsdax()` and `is_fsdax_page()`: defined in
  `include/linux/memremap.h`, not gated on `CONFIG_FS_DAX`.
- Device-DAX folio: no helper exists, and `MEMORY_DEVICE_GENERIC` alone does
  not identify one; `drivers/xen/unpopulated-alloc.c` and
  `drivers/hv/mshv_vtl_main.c` use that type with no `struct dax_device`.
- Device-DAX inode: `dax_dev_get()` sets `S_IFCHR` and `S_DAX` on the
  pseudo-fs inode; `dax_open()` sets `S_DAX` on the opened inode and points
  its `i_mapping` at the mapping of the pseudo-fs inode.
- `vma_is_dax()`: calls `file_is_dax()`, which tests
  `file->f_mapping->host`; the `S_ISCHR()` test in `vma_is_fsdax()` uses
  `file_inode()` instead.
- Without `CONFIG_FS_DAX`: `S_DAX` is 0 in `include/linux/fs.h`, so
  `IS_DAX()`, `file_is_dax()`, `vma_is_dax()` and `dax_mapping()` are false
  for device DAX as well.
