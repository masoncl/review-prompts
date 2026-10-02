- virtio-fs: one `struct fuse_dev` per `struct virtio_fs_vq`, installed on
  the same channel in `virtio_fs_fill_super()`; these never pass through
  `fuse_dev_release()`, so `fuse_dev_put()` unlinks them.
- `struct fuse_pqueue`: embedded, as `pq` in `struct fuse_dev` and as `fpq`
  in `struct fuse_ring_queue`; only its hash array is allocated separately
  (`fuse_pqueue_alloc()`).
- `struct fuse_req`: points at its `struct fuse_chan` and takes no
  `struct fuse_conn` reference. Each `struct fuse_mount`, except CUSE's
  `cc->fm`, and each installed `struct fuse_dev` holds one.
- Last unmount: `fuse_conn_destroy()` calls `fuse_chan_abort()` and then
  `fuse_chan_wait_aborted()`, which waits for `num_waiting` to reach zero;
  that drain, not a reference, is what keeps requests from outliving the
  channel.
- `struct fuse_conn` has no inode table. `fuse_iget()` hashes inodes in
  their superblock with `iget5_locked()`, keyed by nodeid; code that has only
  a nodeid uses `fuse_ilookup()`, which tries every `struct fuse_mount` on
  `fc->mounts` and needs `fc->killsb` held.
- Two inodes share a nodeid when the server announces a submount: the mount
  point inode in the parent superblock and the root inode of the submount's
  superblock. `fuse_iget()` keeps the mount point out of the inode hash.
- `union fuse_file_args` (`ff->args`): one allocation that holds the OPEN
  reply and later the `struct fuse_release_args`. It is NULL for a directory
  when the server does not implement OPENDIR; see `fuse_file_open()`.
- `struct fuse_dentry` (`fs/fuse/dir.c`): hangs off the dentry in
  `dentry->d_fsdata`, set by `fuse_dentry_init()`.
- `struct fuse_ring`: hangs off `struct fuse_chan` (`ring`). Its queue array
  has `num_possible_cpus()` slots; a `struct fuse_ring_queue` is created by
  the first REGISTER on its slot or by `FUSE_IO_URING_CMD_ADD_QUEUE`.
- Once the ring is ready, io_uring requests bypass `fiq->pending` and every
  device's `pq`: they wait on the lists of a `struct fuse_ring_queue` and are
  tracked in its `fpq`. FORGET and INTERRUPT still go through
  `struct fuse_iqueue`; see `fuse_io_uring_ops` in `fs/fuse/dev_uring.c`.
- `struct fuse_sync_bucket`: serves syncfs only. `fuse_sync_fs_writes()` is
  its one waiter, and `fuse_writepage_add_to_bucket()` adds a write only
  when `fc->sync_fs` is set.
