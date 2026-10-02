- `->destroy_inode` set and `->free_inode` NULL: `destroy_inode()` returns
  after the method and queues nothing; the filesystem frees the memory and
  must supply the RCU delay.
- Neither set: `i_callback()` calls `free_inode_nonrcu()` after the grace
  period.
- `i_fop`: shares a union with `free_inode`; `destroy_inode()` overwrites it
  before the grace period, so it must not be read through an RCU-only pointer.
- `i_dentry`: shares a union with `i_rcu`, which `call_rcu()` uses in
  `destroy_inode()`.
- Lockless hash probes are a second RCU reader: `find_inode()` and
  `find_inode_fast()`, when called with `hash_locked` false, walk the chain
  under `rcu_read_lock()` only, read `i_sb`, `i_ino`, the state and `i_count`,
  call the `test` callback and take `i_lock`; the memory of a hashed inode
  must outlive the grace period.
- `i_link` freed in `->free_inode`: see `shmem_free_in_core_inode()` in
  `mm/shmem.c`.
