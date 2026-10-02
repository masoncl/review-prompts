- `sysfs_file_kobj()`: reads `kn->__parent` with `rcu_dereference()` under
  `guard(rcu)()` and returns its `priv`; `struct kernfs_node` has no field
  named parent, and `kernfs_parent()` is not used here.
- Text table choice in `sysfs_add_file_mode_ns()`: looks only at
  `kobj->ktype->sysfs_ops` and `SYSFS_PREALLOC`; the attribute's own callbacks
  and its permission bits play no part.
- With a ktype whose `sysfs_ops` has both callbacks, for example
  `dev_sysfs_ops` or `kobj_sysfs_ops`, every text file gets
  `sysfs_file_kfops_rw` or `sysfs_prealloc_kfops_rw`.
- Binary attribute with no `mmap`, `read` or `write`: gets
  `sysfs_file_kfops_empty`.
- Open for a direction the table has no kernfs op for: `kernfs_fop_open()`
  returns `-EACCES`.
- The `-EINVAL` branches in `kernfs_file_read_iter()` and
  `kernfs_fop_write_iter()` are not reached with the sysfs tables, because
  that open has already failed.
- Text attribute with no callback of its own on a ktype that has the op: open
  succeeds when the mode has the bit; the read or write reaches the ktype
  dispatcher, which returns its own error, `-EIO` in `dev_attr_show()` and
  `kobj_attr_show()`.
- `sysfs_kf_write()` and `sysfs_kf_read()` call `ops->store` and `ops->show`
  with no NULL test; only the table choice keeps that safe.
