- Written request: only in the preamble of
  `Documentation/filesystems/locking.rst` and in the comment under
  `struct dentry_operations` in `include/linux/dcache.h`; the latter names
  both `locking.rst` and `vfs.rst`.
- `locking.rst` preamble: also asks the patch to convert the instances in the
  tree itself, to list dubious cases at the end of the file, and not to turn
  the file into a log.
- `Documentation/filesystems/porting.rst`: no text in the tree asks for an
  entry; it is a list with the newest entry last, entries separated by
  `---`.
- `porting.rst` tags: `**mandatory**`, `**recommended**` and
  `**informational**`, plus one entry tagged `**highly recommended**` and one
  tagged `**strongly recommended**`; `**informational**` is used for a
  change that needs no conversion, such as a lock that callers now hold.
- `locking.rst` and `vfs.rst`: each holds its own copy of the prototypes, so a
  prototype change edits both.
- Document copies are not all in step with the headers (for example
  `setlease` in `locking.rst` against `include/linux/fs.h`); check a patch
  against the header, not the document.
- `locking.rst` sections beyond the five method tables:
  `struct xattr_handler`, `struct file_system_type`,
  `struct file_lock_operations`, `struct lock_manager_operations`,
  `struct block_device_operations`, `struct dquot_operations`,
  `struct vm_operations_struct`.
- `Documentation/filesystems/api-summary.rst`: holds only `kernel-doc::`
  directives, so updating the kernel-doc comment in the source is enough.
- `Documentation/filesystems/mount_api.rst`: holds a copy of
  `struct fs_context_operations`.
- `Documentation/filesystems/mmap_prepare.rst`: covers the `mmap_prepare`
  hook.
- Path-creation helpers used outside `fs/`: `start_creating_path()` and
  `end_creating_path()`, for example in `net/unix/af_unix.c` and
  `drivers/base/devtmpfs.c`; `porting.rst` records the renames.
- drivers/misc/ibmasm is not in this tree.
- `fs/internal.h` helpers: have callers outside `fs/`; files under
  `io_uring/` and `block/bdev.c` include `../fs/internal.h`, search for that
  include. For example `filename_renameat2()` is called from
  `io_uring/fs.c`.
- Direct `f_op->` callers outside `fs/`: not found by a search for callers of
  the `vfs_` helpers; search for `f_op->` instead. For example
  `drivers/block/loop.c`, `drivers/block/zloop.c`,
  `drivers/target/target_core_file.c`, `io_uring/rw.c`, `ipc/shm.c`,
  `kernel/acct.c`, `drivers/gpu/drm/i915/gem/i915_gem_shmem.c`.
- Char-device multiplexers: call `f_op->open()` themselves after
  `replace_fops()`; search for `replace_fops(`. For example
  `drivers/char/misc.c`, `sound/core/sound.c`, `drivers/gpu/drm/drm_drv.c`.
- Rust: code that fills a `bindings::file_operations` with `extern "C"`
  functions, for example `rust/kernel/miscdevice.rs` and
  `rust/kernel/debugfs/file_ops.rs`; a changed method prototype has to be
  changed there too.
- `tools/testing/vma/include/dup.h`: holds its own copy of
  `struct file_operations` with `mmap` and `mmap_prepare`.
- Method tables implemented outside `fs/` in files that define no
  `struct file_system_type`: for example `block/fops.c`,
  `drivers/dax/device.c`, `drivers/video/fbdev/core/fb_defio.c`,
  `mm/swap_state.c`.
- To list implementers outside `fs/`: search for `struct inode_operations`,
  `struct super_operations`, `struct address_space_operations`,
  `struct dentry_operations` and `struct file_system_type` definitions with
  `fs/` excluded.
