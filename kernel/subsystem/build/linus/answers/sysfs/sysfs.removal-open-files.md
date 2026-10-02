- `kernfs_drain_open_files()`: walks the list under the hashed node mutex
  only; it does not take `of->mutex`. `kernfs_release_file()` asserts the
  hashed mutex.
- Trigger: `kernfs_should_drain_open_files()` tests the counters `nr_mmapped`
  and `nr_to_release` of `struct kernfs_open_node`, not the node flags; an
  open file that never called mmap does not trigger the unmap.
- `of->vm_ops`: left as it is; the drain clears `of->mmapped` and decrements
  `nr_mmapped`.
- Unmap target: `file_inode(of->file)->i_mapping`. VMAs are linked to
  `vm_file->f_mapping` (`vma_link_file()` in `mm/vma.c`), and
  `sysfs_kf_bin_open()` replaces `f_mapping` when `struct bin_attribute` has
  `f_mapping` set (PCI resource files use `iomem_get_mapping()`), so this
  unmap does not reach mappings of those files.
- `of->released`: set by the drain's release, only on a node with
  `KERNFS_HAS_RELEASE`, and never cleared; `kernfs_get_active_of()` then fails
  for every later operation on that open file.
- `kernfs_show()` with show false: runs the same drain, so hiding a node also
  zaps its mappings and, on a node with `KERNFS_HAS_RELEASE`, releases its
  open files; the released open files stay dead after the node is shown
  again.
