- `alloc_dax()`: returns the device alive; `dax_dev_get()` sets `DAXDEV_ALIVE`
  when `iget5_locked()` hands back an `I_NEW` inode.
- Filesystem lookups that take a reference: `fs_dax_get_by_bdev()`
  (`xa_load()` on `dax_hosts`, then `igrab()`) and `fs_dax_get()` (`igrab()`);
  there is no dax_get_by_host here.
- `kill_dax()` and `put_dax()`: test only for NULL, while `alloc_dax()` fails
  with `ERR_PTR()`. `pmem_attach_disk()` stores the pointer only on success, so
  `pmem_release_disk()` passes NULL when DAX was refused with `-EOPNOTSUPP`.
