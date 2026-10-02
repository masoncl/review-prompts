- There is no fuse_queue_forget() here; `fuse_chan_queue_forget()` in
  `fs/fuse/dev.c` does that. Its first argument is `fc->chan`, a
  `struct fuse_chan *`, not the `struct fuse_conn *`.
- `fuse_alloc_forget()`: defined in `fs/fuse/dev.c`, declared in
  `fs/fuse/dev.h`; `kzalloc_obj()` with `GFP_KERNEL_ACCOUNT`.
- `fuse_iget()`: takes no forget link. A caller that allocated a link frees
  it with `kfree()` when `fuse_iget()` succeeds, or queues it when it returns
  NULL.
- Count raised without `fuse_iget()`: `fuse_dentry_revalidate()` and the
  existing-dentry branch of `fuse_direntplus_link()` do `fi->nlookup++` under
  `fi->lock` themselves.
- `fuse_dentry_revalidate()`: raises `fi->nlookup` before it tests
  `fuse_invalid_attr()` and `fuse_stale_inode()`, so a reply that fails them
  is still counted on the inode and released at eviction.
- FORGET with count 1 is queued in `fuse_dentry_revalidate()` when the reply
  has another node id, or when `FUSE_ATTR_SUBMOUNT` in the reply differs from
  `IS_AUTOMOUNT()` of the inode.
- Reply rejected with `-EIO` in `fuse_lookup_name()`, `create_new_entry()`
  and `fuse_create_open()`: the link is freed and no FORGET is sent.
- `fuse_create_open()` on that `-EIO` path: sends no RELEASE either, only
  `fuse_file_free()`. It queues a FORGET only when `fuse_iget()` returns
  NULL, after RELEASE through `fuse_sync_release()`.
- Failure after `fuse_iget()` succeeded, such as an error from
  `d_splice_alias()` in `fuse_lookup()` or `create_new_entry()`: no FORGET is
  queued; the count stays in `fi->nlookup` and goes out at eviction.
- There is no fuse_forget_inode() here; `fuse_evict_inode()` queues
  `fi->forget` itself, only if the superblock has `SB_ACTIVE` and
  `fi->nlookup` is nonzero.
- Submount point made by `fuse_iget()`: `fi->nlookup` is not raised. The one
  count is in `fi->submount_lookup`, with its own preallocated link, and
  `fuse_cleanup_submount_lookup()` queues the FORGET when the last reference
  is dropped.
- `fuse_force_forget()` in `fs/fuse/readdir.c`: an ordinary request with
  `force` and `noreply`, allocated with `__GFP_NOFAIL` in `fuse_chan_send()`.
  It does not use a `struct fuse_forget_link` or the forget list.
- **Unsafe usage**: touching or freeing a `struct fuse_forget_link` after it
  was passed to `fuse_chan_queue_forget()`.
  - Unsafe: both `send_forget` implementations own the link from then on.
    `fuse_dev_queue_forget()` frees it at once when `fiq->connected` is clear,
    and `virtio_fs_send_forget()` always frees it.
  - Safe: clear the pointer after queuing, as `fuse_evict_inode()` does with
    `fi->forget`, because `fuse_free_inode()` calls `kfree(fi->forget)`.
  - Safe: `kfree()` only on the paths that did not queue, as
    `fuse_lookup_name()` does.
- **Unsafe usage**: calling `fuse_chan_queue_forget()` with a link that may
  be NULL.
  - Unsafe: it writes `forget->forget_one` with no NULL test.
  - Safe: fail with `-ENOMEM` before the request is sent when
    `fuse_alloc_forget()` returns NULL, as `create_new_entry()` does.
