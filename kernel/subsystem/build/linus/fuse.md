# FUSE Subsystem

## Main structures

### Objects and how they relate

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

## Where to look

**Source files**

- Four files in `fuse-y` of `fs/fuse/Makefile` are built unconditionally and
  hold code that is not in `fs/fuse/dev.c`, `fs/fuse/file.c` or
  `fs/fuse/inode.c`:

  | File | Side | Holds |
  |---|---|---|
  | `fs/fuse/req.c` | filesystem | `__fuse_simple_request()`, `fuse_simple_background()`, `fuse_simple_notify_reply()`: fill credentials, test `fc->conn_error`, hand off to the channel |
  | `fs/fuse/notify.c` | filesystem | `fuse_notify()` and the `FUSE_NOTIFY_*` handlers |
  | `fs/fuse/poll.c` | filesystem | `fuse_file_poll()`, `fuse_notify_poll_wakeup()`, `fuse_end_polls()` |
  | `fs/fuse/req_timeout.c` | transport | `fuse_check_timeout()`, `fuse_init_server_timeout()`, `fuse_request_expired()` |

- Transport files are `fs/fuse/dev.c`, `fs/fuse/dev_uring.c` and
  `fs/fuse/req_timeout.c`: none of them includes `fs/fuse/fuse_i.h`, so none
  can dereference `struct fuse_conn`, `struct fuse_mount` or
  `struct fuse_inode`.
- `fs/fuse/virtio_fs.c` and `fs/fuse/cuse.c` include both sides' headers; each
  creates its own channel and connection.
- `fs/fuse/backing.c`: built with `fs/fuse/passthrough.c` under
  `CONFIG_FUSE_PASSTHROUGH`.
- `fuse_backing_files_init()` and `fuse_backing_files_free()` in
  `fs/fuse/backing.c` have no stub in `fs/fuse/fuse_i.h`; a call from
  unconditional code needs `IS_ENABLED(CONFIG_FUSE_PASSTHROUGH)` around it, as
  in `fuse_conn_init()`.
- `fs/fuse/dax.c`: `CONFIG_FUSE_DAX` depends on `CONFIG_VIRTIO_FS`, but
  `dax.o` links into `fuse.o`, not `virtiofs.o`.
- `fs/fuse/sysctl.c`: built only under `CONFIG_SYSCTL`; the variables it
  exposes are defined in files that are always built:
  `fuse_default_req_timeout` and `fuse_max_req_timeout` in
  `fs/fuse/req_timeout.c`, `fuse_max_pages_limit` in `fs/fuse/inode.c`.
- `fs/fuse/iomode.c` and `fs/fuse/trace.c`: built unconditionally.

**Private headers**

- `struct fuse_chan` is the transport object; it is defined in
  `fs/fuse/fuse_dev_i.h`, reached as `fc->chan`, and points back with
  `fch->conn`.

| Header | Defines | Included by |
|---|---|---|
| `fs/fuse/fuse_i.h` | `struct fuse_conn`, `struct fuse_mount`, `struct fuse_inode`, `struct fuse_file` | filesystem files; not `fs/fuse/dev.c`, `fs/fuse/dev_uring.c`, `fs/fuse/req_timeout.c` |
| `fs/fuse/args.h` | `struct fuse_args`, `struct fuse_args_pages` | `fs/fuse/fuse_i.h`, and directly `fs/fuse/dev.c`, `fs/fuse/dev_uring.c` |
| `fs/fuse/dev.h` | `struct fuse_chan_param`; every other struct it names is only forward-declared | both sides |
| `fs/fuse/fuse_dev_i.h` | `struct fuse_chan`, `struct fuse_dev`, `struct fuse_req`, `struct fuse_iqueue`, `struct fuse_iqueue_ops`, `struct fuse_pqueue`, `struct fuse_copy_state`, `struct fuse_forget_link`, `enum fuse_req_flag` | transport files, plus `fs/fuse/cuse.c`, `fs/fuse/virtio_fs.c`, `fs/fuse/trace.c` |

- `fs/fuse/dev.c` and `fs/fuse/dev_uring.c` get `fs/fuse/fuse_dev_i.h`
  through `fs/fuse/dev_uring_i.h`.
- Filesystem files such as `fs/fuse/inode.c`, `fs/fuse/dir.c`,
  `fs/fuse/file.c` and `fs/fuse/control.c` include `fs/fuse/dev.h` and not
  `fs/fuse/fuse_dev_i.h`: to them `struct fuse_chan`, `struct fuse_dev` and
  `struct fuse_req` are opaque.
- Filesystem code reads and sets channel state through functions in
  `fs/fuse/dev.h`, for example `fuse_chan_num_waiting()`,
  `fuse_chan_max_background_set()`, `fuse_dev_is_installed()`; a patch that
  writes `fc->chan->` in such a file does not compile.
- `fs/fuse/dev.h` also declares what the transport calls back on the
  filesystem side with an opaque `struct fuse_conn *`: `fuse_conn_get()`,
  `fuse_conn_put()`, `fuse_conn_get_id()`, `fuse_end_polls()`,
  `fuse_notify()`, `fuse_backing_open()`, `fuse_backing_close()`.
- `no_interrupt`, `io_uring` and `timeout` are fields of `struct fuse_chan`,
  not of `struct fuse_conn`.
- `struct fuse_dev` has `chan` and `struct fuse_req` has `chan`; neither has a
  pointer to `struct fuse_conn` or `struct fuse_mount`.
- Copy helpers are split: `fuse_copy_one()`, `fuse_copy_folio()` and
  `fuse_copy_finish()` are declared in `fs/fuse/dev.h` so that
  `fs/fuse/notify.c` can call them; `fuse_copy_init()`, `fuse_copy_args()` and
  `fuse_copy_out_args()` are declared in `fs/fuse/fuse_dev_i.h`.

**Entry points**

| Job | Start at | File |
|---|---|---|
| Mounting | `fuse_get_tree()`, then `fuse_fill_super()`, `fuse_fill_super_common()`, `fuse_send_init()` | `fs/fuse/inode.c` |
| Send and wait | `fuse_simple_request()` (inline, `fs/fuse/fuse_i.h`), `__fuse_simple_request()` | `fs/fuse/req.c` |
| Send and wait, transport half | `fuse_chan_send()`, then `__fuse_request_send()`, `request_wait_answer()` | `fs/fuse/dev.c` |
| Send, no wait | `fuse_simple_background()` in `fs/fuse/req.c`, then `fuse_chan_send_bg()` | `fs/fuse/dev.c` |
| Read a request | `fuse_dev_read()`, `fuse_dev_splice_read()`, then `fuse_dev_do_read()` | `fs/fuse/dev.c` |
| Write a reply | `fuse_dev_write()`, `fuse_dev_splice_write()`, then `fuse_dev_do_write()` | `fs/fuse/dev.c` |
| Notification from the server | `fuse_notify()`, called from `fuse_dev_do_write()` | `fs/fuse/notify.c` |
| io_uring fetch and commit | `fuse_uring_cmd()` | `fs/fuse/dev_uring.c` |
| Abort | `fuse_chan_abort()` | `fs/fuse/dev.c` |

- `fuse_dev_is_installed()`: the test for "this device is mounted"; `fud->chan`
  is NULL before mount and `FUSE_DEV_CHAN_DISCONNECTED` after release.
- `fuse_send_init()`: returns `int`; with `fc->sync_init` it sends INIT with
  `fuse_simple_request()` and calls `process_init_reply()` itself, otherwise
  `process_init_reply()` is the `end` callback of a background request.
- Reply helpers in `fuse_dev_do_write()` are `fuse_request_find()`,
  `fuse_copy_out_args()` and `fuse_request_end()`; there are no unprefixed
  forms.
- `fuse_chan_abort()` clears `fch->connected`, `fiq->connected` and the
  `fpq->connected` of each device on `fch->devices`; `struct fuse_conn` has no
  `connected` field.

## Connection, channel and device

**Connection and channel state**

- `struct fuse_conn` has no `connected`, `iq`, `devices`, `bg_lock`,
  `bg_queue`, `num_background`, `active_background`, `max_background`,
  `blocked`, `blocked_waitq`, `initialized` or `num_waiting`; all are in
  `struct fuse_chan`, reached as `fc->chan` (back pointer `fch->conn`).

| State | Lives in | Protected by |
|---|---|---|
| `iq` (`struct fuse_iqueue`) | channel | `fiq->lock` |
| `devices`, `connected`, the stores that publish `ring` and `ring->queues[qid]` | channel | `fch->lock` |
| `max_background`, `num_background`, `active_background`, `bg_queue`, `blocked` | channel | `fch->bg_lock` |
| `initialized` | channel | none; `smp_store_release()` / `smp_load_acquire()` |
| `minor`, `max_write`, `max_pages` | both, one copy each | none |
| `max_read`, `max_pages_limit`, `congestion_threshold`, feature bits | connection | none |
| `polled_files`, `backing_files_map`, `curr_bucket` | connection | `fc->lock` |
| `mounts` | connection | `fc->killsb` |

- `fch->connected`: cleared only in `fuse_chan_abort()`, holding `fch->lock`
  and `fch->bg_lock`; `fuse_get_req()` reads it with no lock,
  `fuse_request_queue_background()` under `fch->bg_lock`.
- There is no fuse_set_initialized() here; `fuse_chan_set_initialized()`
  copies a non-NULL `struct fuse_chan_param` into the channel, then does
  `smp_store_release(&fch->initialized, 1)`.
- Channel copies of `minor`, `max_write`, `max_pages`: read by `fs/fuse/dev.c`
  and `fs/fuse/dev_uring.c`; filesystem code reads the `struct fuse_conn`
  copies.
- `fch->abort_with_err`: per-abort argument of `fuse_chan_abort()`;
  `fc->abort_err` is the INIT feature bit that `fuse_conn_abort_write()`
  passes in.
- Lock order in `fuse_chan_abort()`: `fch->lock` outermost; inside it
  `fch->bg_lock`, `fpq->lock` then `req->waitq.lock`, `fiq->lock`, and
  `fc->lock` through `fuse_end_polls()`.

**Mounts sharing a connection**

- `fm->sb` is never cleared; it is written only by
  `fuse_fill_super_common()` and `fuse_fill_super_submount()`.
- Teardown: `fuse_mount_remove()` unlinks `fm->fc_entry` under
  `down_write(&fc->killsb)`, called from `fuse_sb_destroy()` and
  `virtio_kill_sb()` before the superblock is killed; a mount found on
  `fc->mounts` under `down_read()` with `sb` set therefore has a live
  superblock.
- Mounts on `fc->mounts` with `sb == NULL`: the first mount between
  `fuse_conn_init()` and fill_super, and CUSE's `cc->fm` always, so
  `fuse_ilookup()` finds nothing on a CUSE connection.
- `fc->auto_submounts`: written only by `virtio_fs_get_tree()`.
- Mounting again with a device fd that is already installed: `fuse_get_tree()`
  reuses the existing superblock through `sget_fc()` with
  `fuse_test_super()`; no second superblock or `struct fuse_mount` joins the
  connection, and `fuse_set_no_super()` gives `-ENOTCONN` if none matches.
- Notify handlers that take `fc->killsb` are in `fs/fuse/notify.c`, not
  `fs/fuse/dev.c`; `fuse_epoch_work()` in `fs/fuse/dir.c` is the work-item
  user.
- **Potentially unsafe usage**: dereferencing `fm->sb` without `fc->killsb`.
  - Unsafe: when the mount was reached through the connection (`fc->mounts`,
    or the out pointer of `fuse_ilookup()`) from a device write or a work
    item; the superblock can be killed once `fuse_mount_remove()` returns.
  - Safe: with `down_read(&fc->killsb)` held from before `fuse_ilookup()`
    until the last use and the `iput()`, as `fuse_notify_retrieve()` does.
  - Safe: when the mount came from `get_fuse_mount()` on an inode the VFS
    caller holds, as `fuse_access()` does.
  - Safe: in `process_init_reply()`, on the mount the INIT request carries
    (`ia->fm`); INIT is counted in `fch->num_waiting`, and
    `fuse_conn_destroy()` waits for that in `fuse_chan_wait_aborted()`
    before the superblock is killed.

**Automatic submounts**

- `fuse_iget()` sets `S_AUTOMOUNT`; there is no fuse_get_attr here.
- `fuse_iget()` conditions: `fc->auto_submounts`, `FUSE_ATTR_SUBMOUNT` in
  `attr->flags`, and `S_ISDIR(attr->mode)`.
- Mountpoint inode: made with `new_inode()`, never hashed, `fi->nlookup` not
  incremented; the lookup is held by `fi->submount_lookup` with count 1.
- `fuse_dentry_automount()`: only creates the context with
  `fs_context_for_submount()`, stores the mountpoint `struct fuse_inode` in
  `fsc->fs_private` and calls `fc_mount()`.
- `fuse_get_tree_submount()` allocates the `struct fuse_mount`, takes the
  connection reference and links the mount under
  `down_write(&fc->killsb)`.
- Route to `fuse_get_tree_submount()`: `virtio_fs_init_fs_context()` calls
  `fuse_init_fs_context_submount()` for `FS_CONTEXT_FOR_SUBMOUNT`;
  `fuse_init_fs_context()` has no such branch.
- Submount root: built by `fuse_iget()` from `fuse_fill_attr_from_inode()`,
  which sets no `flags`, so the root is hashed in the new superblock and
  `fuse_fill_super_submount()` undoes the `nlookup` increment.
- `refcount_inc(&sl->count)` is the last step of
  `fuse_fill_super_submount()`, after every failure return.
- There is no fuse_queue_forget() here; `fuse_cleanup_submount_lookup()`
  calls `fuse_chan_queue_forget()` with nlookup 1 on the last put.
- `fuse_dentry_revalidate()` increments `fi->nlookup` of the mountpoint inode
  on a successful re-LOOKUP; `fuse_evict_inode()` then sends that count as a
  second FORGET, separate from the shared one.
- `fuse_evict_inode()` drops the shared count only while `SB_ACTIVE` is set.
- Unmount still drops it: `.drop_inode` is `inode_just_drop()` and
  `generic_shutdown_super()` runs `shrink_dcache_for_umount()` before it
  clears `SB_ACTIVE`, so the root is evicted while the flag is set.
- `fuse_free_inode()` does not free `fi->submount_lookup`.

**Connection reference count**

- Holders of `fc->count`:
  - the first `struct fuse_mount`, which owns the initial count from
    `fuse_conn_init()`
  - each submount, taken in `fuse_get_tree_submount()`
  - each installed `struct fuse_dev`, taken in `fuse_dev_install_with_pq()`
  - `fuse_ctl_file_conn_get()` for one control-file operation
  - `fuse_uring_stop_queues()` while `async_teardown_work` is pending,
    dropped in `fuse_uring_async_stop_queues()`
  - each open CUSE file, from `cuse_open()` to `cuse_release()`
- CUSE: `cuse_channel_open()` drops the initial count right after
  `fuse_dev_alloc_install()`, so the device holds the long-lived reference.
- Device reference: dropped in `fuse_dev_release()`; dropped in the last
  `fuse_dev_put()` instead when the device was never released through a file,
  as in `virtio_fs_free_devs()`. There is no fuse_dev_free() here.
- `fuse_notify_retrieve()` and `fs/fuse/virtio_fs.c` do not call
  `fuse_conn_get()`.
- `struct fuse_chan` has no count of its own; once passed to
  `fuse_conn_init()` it is freed only with the connection.
- Last `fuse_conn_put()`, in order:
  1. `fuse_dax_conn_free()` under `CONFIG_FUSE_DAX`
  2. `cancel_work_sync(&fc->epoch_work)`
  3. `fuse_chan_release()`: `fiq->ops->release` if set, then
     `cancel_delayed_work_sync(&fch->timeout.work)` if a timeout is armed
  4. `put_pid_ns()`
  5. free `fc->curr_bucket`
  6. `fuse_backing_files_free()` under `CONFIG_FUSE_PASSTHROUGH`
  7. `call_rcu(&fc->rcu, delayed_release)`
- `delayed_release()`, after the grace period: `fuse_uring_destruct()`, then
  `fuse_chan_free()`, then `put_user_ns()`, then `fc->release()`; so ring,
  channel, connection.
- `fuse_free_conn()` is a plain `kfree()`; `cuse_fc_release()` frees the
  enclosing `struct cuse_conn`.
- Last `fuse_conn_put()` can sleep (steps 2 and 3; virtiofs's release takes
  `virtio_fs_mutex`).
- `fuse_chan_free()` warns if `fch->devices` is not empty;
  `fuse_uring_destruct()` warns if ring entries are still queued.
- `fuse_mount_destroy()` does not abort or wait; `fuse_conn_destroy()` does
  (DESTROY when `fc->destroy` and `fc->conn_init` are set,
  `fuse_chan_abort()`, `fuse_chan_wait_aborted()`), and `fuse_sb_destroy()`
  calls it only when `fuse_mount_remove()` reports the last mount.
- `fuse_get_tree()` and `virtio_fs_get_tree()` call `fuse_mount_destroy()` on
  the fresh mount when `fsc->s_fs_info` is still set, that is when no new
  superblock consumed it.

**Connection feature bits**

- `fc->conn_error` is tested in `fuse_req_prep()` in `fs/fuse/req.c`, for
  requests without `args->force`, before the request waits for
  `fch->initialized`; `fuse_get_req()` tests only `fch->connected` and
  returns `-ENOTCONN`.
- `fuse_send_init()` is the other reader of `fc->conn_error`.
- `fc->sync_fs` is cleared at run time, by `fuse_sync_fs()` on `-ENOSYS`.
- **Potentially unsafe usage**: storing to a one-bit field of
  `struct fuse_conn` once requests can run.
  - Unsafe: when losing the store changes behaviour; the stores take no lock
    and neighbouring bits share a word, so a concurrent store to another bit
    can undo it.
  - Safe: the bit only caches a `-ENOSYS` reply and the path that finds it
    clear sends the request again, as `fuse_file_open()` does with
    `fc->no_open`.
  - Safe: in `process_init_reply()`; `fuse_get_req()` holds every request
    without `args->force` until `fuse_chan_set_initialized()`.
  - Safe: before the device is installed, as `fuse_fill_super_common()` and
    `virtio_fs_get_tree()` do.
- `connected`, `initialized` and `no_interrupt` are not bit-fields but
  full-width members of `struct fuse_chan`: `connected` is written under
  `fch->lock`, `initialized` with release and acquire, `no_interrupt` is a
  `bool`.

**Device object life cycle**

- `file->private_data` is never NULL on an open device file:
  `fuse_dev_open()` allocates the `struct fuse_dev`, with `ref` 1 and no
  `pq.processing` array.
- States of `fud->chan`:
  1. NULL after `fuse_dev_open()`
  2. the channel, set by `cmpxchg()` from NULL in
     `fuse_dev_install_with_pq()` under `fch->lock`
  3. `FUSE_DEV_CHAN_DISCONNECTED`, set by `xchg()` in `fuse_dev_release()`
- No other change: `fuse_dev_release()` goes to state 3 from state 1 as well
  as from state 2, and an install after release fails.
- Install callers: `fuse_dev_install()` (mount, under `fuse_mutex`; virtiofs;
  CUSE through `fuse_dev_alloc_install()`) and `fuse_dev_ioctl_clone()`.
- `fuse_dev_ioctl_clone()`: takes no `fuse_mutex`; returns `-EINVAL` when the
  `cmpxchg()` fails.
- Sync INIT: there is no FUSE_DEV_SYNC_INIT pointer value;
  `FUSE_DEV_IOC_SYNC_INIT` sets `fud->sync_init`, allowed only while
  `fud->chan` is NULL.
- `fuse_get_dev()`: never returns NULL; `ERR_PTR(-EPERM)` when not installed,
  but with `fud->sync_init` it sleeps interruptibly on `fuse_dev_waitq` until
  installed.
- `__fuse_get_dev()`: returns NULL when not installed and never sleeps; the
  write paths use it and return `-EPERM`.
- `fuse_dev_release()`: when the old value was a channel, ends the requests
  on `fpq->processing`, unlinks the device, aborts if `fch->devices` became
  empty, and drops the connection reference; `struct fuse_conn` and
  `struct fuse_chan` have no dev_count field.
- `struct fuse_dev` is freed by the last `fuse_dev_put()`, which need not be
  the one in `fuse_dev_release()`; `fuse_opt_fd()` takes a second `fud->ref`
  with `fuse_dev_grab()` and does not keep the file, and `fuse_free_fsc()`
  drops it.
- `fuse_dev_release()` takes `fch->lock` before `list_del()` so that a
  concurrent `fuse_dev_install_with_pq()` has finished its `list_add_tail()`.
- First read of `fud->chan`: through `fuse_dev_chan_get()`, which is
  `smp_load_acquire()`.
- **Potentially unsafe usage**: dereferencing the value of `fud->chan`.
  - Unsafe: when the caller holds only `fud->ref` and not the open file, as a
    mount context does; the value can be `FUSE_DEV_CHAN_DISCONNECTED`, or a
    channel whose connection reference `fuse_dev_release()` already dropped.
  - Safe: compare only, as `fuse_dev_is_installed()` and `fuse_dev_verify()`
    do.
  - Safe: in a file operation of the device file after `fuse_get_dev()` or
    `__fuse_get_dev()` succeeded, as `fuse_dev_do_read()` does with a plain
    `fud->chan`; release cannot run during the operation.
  - Safe: in the last `fuse_dev_put()`, which tests for NULL and
    `FUSE_DEV_CHAN_DISCONNECTED` first; a real pointer there means the device
    still holds its connection reference.
- **Unsafe usage**: testing the result of `fuse_get_dev()` with `!fud`.
  - Safe: `IS_ERR()` for `fuse_get_dev()`, as `fuse_dev_read()` does; a NULL
    test for `__fuse_get_dev()`, as `fuse_dev_write()` does.

## Mounting and the INIT exchange

**Mount setup**

- Order in `fuse_get_tree()` and below:
  1. `fuse_dev_chan_new()`: channel, with `pq_prealloc` and
     `fuse_dev_fiq_ops`.
  2. `fc`, then `fm`, then `fuse_conn_init()`, which links `fc->chan` and
     `fch->conn`.
  3. superblock, through `get_tree_bdev()`, `sget_fc()` or
     `get_tree_nodev()`.
  4. in `fuse_fill_super_common()`: `fuse_dax_conn_alloc()`,
     `fuse_bdi_init()`, options, root inode and `d_make_root()`.
  5. under `fuse_mutex`: `fuse_dev_is_installed()` test,
     `fuse_ctl_add_conn()`, `fuse_conn_list`, `sb->s_root`, then
     `fuse_dev_install()`.
  6. `fuse_send_init()`, whose result `fuse_fill_super()` returns.
- `struct fuse_dev`: allocated at open of the device by `fuse_dev_open()`;
  `fuse_fill_super_common()` allocates none.
- `fuse_opt_fd()`: checks `f_op` and `fsc->user_ns` at option parse and
  keeps a `struct fuse_dev` reference in `ctx->fud` (`fuse_dev_grab()`).
- The mount holds no reference on the device file; `fuse_free_fsc()` drops
  `ctx->fud` with `fuse_dev_put()`.
- "Attached" means `fud->chan` is set; `fuse_dev_install()` also moves
  `pq_prealloc` to the device and takes a `fuse_conn_get()` reference.
- `fuse_dev_install()` returns void: if `fud->chan` is already set or is
  `FUSE_DEV_CHAN_DISCONNECTED` (file closed meanwhile), it calls
  `fuse_chan_abort()`, and the mount then fails in `fuse_send_init()`.
- Failure inside `fuse_fill_super_common()`: only `dput()` of the root and
  `fuse_dax_conn_free()`; there is no fuse_dev_free() and no device step to
  undo, because the attach is last.
- Failure of `fuse_send_init()`: `sb->s_root` is already set, so
  `fuse_sb_destroy()` runs `fuse_conn_destroy()`; an installed device stays
  attached to the aborted channel until its file is closed.
- Channel ownership: `__free(fuse_chan_free)` in `fuse_get_tree()` until
  `no_free_ptr()`; after that `delayed_release()` frees it with
  `fuse_chan_free()`.

**INIT reply processing**

- `process_init_reply()` ends in `fuse_chan_set_initialized()`: with a
  `struct fuse_chan_param` when accepted, with NULL when refused; there is
  no fuse_set_initialized().
- `fch->minor`, `fch->max_write`, `fch->max_pages`: copies that
  `fs/fuse/dev.c` and `fs/fuse/dev_uring.c` use; they are set only by an
  accepted reply and stay 0 after a refusal.
- `fc->minor`: stored as the server sent it, not clamped to
  `FUSE_KERNEL_MINOR_VERSION`.
- Major mismatch: refuses the reply; the kernel never sends a second INIT.
- Reply refused when: request error; `arg->major != FUSE_KERNEL_VERSION`;
  `FUSE_MAP_ALIGNMENT` fails `fuse_dax_check_alignment()` (`CONFIG_FUSE_DAX`);
  `FUSE_ALLOW_IDMAP` without `fc->default_permissions`.
- The last two refusals come after feature bits and `fm->sb` fields were
  set; those are not rolled back.
- `FUSE_DEV_IOC_SYNC_INIT`: sets `fud->sync_init`; returns `-EINVAL` once
  `fud->chan` is set; `fuse_fill_super_common()` copies it to
  `fc->sync_init`.
- Synchronous INIT: `process_init_reply()` runs in the mounting task,
  called by `fuse_send_init()` after `fuse_simple_request()` returns.
- `fuse_send_init()` returns `-ENOTCONN` when `fc->conn_error` is set after
  it ran `process_init_reply()` itself: sync INIT refused or failed, or the
  background send failed to queue.
- Background INIT that was queued: `fuse_send_init()` returns 0; a later
  refusal does not fail the mount.
- `virtio_fs_fill_super()`: ignores the return value of `fuse_send_init()`.

**Request size limits**

- Default page count: the constant is `FUSE_DEFAULT_MAX_PAGES_PER_REQ`.
- `fuse_max_pages_limit`: variable in `fs/fuse/inode.c`; its sysctl is in
  `fs/fuse/sysctl.c`, range 1 to 65535, built only with `CONFIG_SYSCTL`.
- `fc->max_write`: floor is the literal 4096; `process_init_reply()` does
  not cap it by `fc->max_pages`.
- `FUSE_MIN_READ_BUFFER`: 8192; it is the floor of the server's read
  buffer, not of `max_write`.
- `fuse_dev_do_read()`: tests `fch->max_write`, which is 0 until an INIT
  reply is accepted, so until then only `FUSE_MIN_READ_BUFFER` applies.
- Header room in that test: `sizeof(struct fuse_in_header)` plus
  `sizeof(struct fuse_write_in)`; there is no FUSE_BUFFER_HEADER_SIZE.
- io_uring payload: `fuse_uring_create()` sizes it as the largest of
  `FUSE_MIN_READ_BUFFER`, `fch->max_write` and `fch->max_pages` pages.
- `fc->name_max`: the file name limit; `FUSE_NAME_LOW_MAX` (1024) from
  `fuse_conn_init()`.
- `fc->name_max` becomes `FUSE_NAME_MAX` (`PATH_MAX - 1`) only when the
  reply has `FUSE_MAX_PAGES` and the resulting `fc->max_pages` is above 1.
- statfs: `f_namelen` is the server's `namelen`, copied by
  `convert_fuse_statfs()`; it neither sets nor reports `fc->name_max`.
- `fc->name_max` is tested in three places: `fuse_lookup_name()`,
  `fuse_notify_inval_entry()` and `fuse_notify_delete()`, each
  `-ENAMETOOLONG`; create, mkdir and rename have no test of their own.
- Readdir entries: tested against the constant `FUSE_NAME_MAX`, not
  `fc->name_max`; failure is `-EIO` (`parse_dirfile()` in
  `fs/fuse/readdir.c`).

**Unmount order**

- `fuse_kill_sb_anon()`: `fuse_sb_destroy()`, then `kill_anon_super()`,
  then `fuse_mount_destroy()`.
- `fuse_conn_destroy()`: called from `fuse_sb_destroy()`, before the
  superblock is shut down; `fuse_mount_destroy()` only does
  `fuse_conn_put()` and frees `fm`.
- DESTROY is sent only when both `fc->destroy` and `fc->conn_init` are set.
- Unmount passes `false` as `abort_with_err`: a blocked device read then
  returns `-ENODEV`; only the abort file in `fs/fuse/control.c` passes
  `fc->abort_err`.
- Eviction: `generic_shutdown_super()` clears `SB_ACTIVE` only after
  `shrink_dcache_for_umount()`, so inodes dropped with their dentries still
  reach `fuse_chan_queue_forget()` in `fuse_evict_inode()`;
  `fuse_dev_queue_forget()` frees the link, because the abort already
  cleared `fiq->connected`.
- `fuse_umount_begin()`: skipped only by `fc->no_force_umount`; a mount
  with `fc->destroy` set, such as fuseblk, is aborted too.
- An open device keeps the connection and channel allocated after unmount,
  through the reference `fuse_dev_install()` took.

**Protocol header**

- `FUSE_KERNEL_MINOR_VERSION`: 46 in this tree; the last changelog entry
  is 7.46.
- `fuse_copy_out_args()` in `fs/fuse/dev.c` defines the reply size rule: a
  reply longer than expected is `-EINVAL`; a shorter one is `-EINVAL`
  unless `out_argvar` is set, and then only the last argument may shrink.
- `fuse_adjust_compat()` in `fs/fuse/dev.c`: applies the compat sizes for
  STATFS, entry-out, attr-out, CREATE and MKNOD from `fch->minor`; the
  call sites in `fs/fuse/dir.c` do not.
- `fuse_adjust_compat()` runs only in `fuse_chan_send()`; a request sent
  with `fuse_chan_send_bg()` is not adjusted.
- Compat sizes set at the call site: `FUSE_COMPAT_WRITE_IN_SIZE` in
  `fuse_write_args_fill()` on `fc->minor < 9`;
  `FUSE_COMPAT_SETXATTR_IN_SIZE` in `fuse_setxattr()` when
  `fc->setxattr_ext` is clear, an INIT flag, not the minor.
- `FUSE_COMPAT_INIT_OUT_SIZE` and `FUSE_COMPAT_22_INIT_OUT_SIZE`: defined
  for servers; no code in `fs/fuse` uses them.
- **Unsafe usage**: enlarging a reply structure and expecting the new
  `sizeof()` from every server.
  - Unsafe: an older server sends the old size; `fuse_copy_out_args()`
    returns `-EINVAL` to its write and the request ends with `-EIO`.
  - Safe: shrink the expected size for older minors, as
    `fuse_adjust_compat()` does with `FUSE_COMPAT_ENTRY_OUT_SIZE`.
  - Safe: set `out_argvar` on a zeroed buffer, as `fuse_new_init()` does
    for `struct fuse_init_out`.

**Adding an INIT flag**

- Bits 0 to 43 are all defined; the highest is
  `FUSE_HAS_IO_URING_BUFPOOL`.
- A flag at bit 32 or above is defined as the full value `(1ULL << n)`,
  not relative to `flags2`; `fuse_new_init()` and `process_init_reply()`
  do the shift by 32.
- State that `fs/fuse/dev.c` needs: add it to `struct fuse_chan_param` and
  set it in `fuse_chan_set_initialized()`, as `io_uring_enabled` is.
- **Potentially unsafe usage**: enabling a feature in
  `process_init_reply()` whose flag `fuse_new_init()` offers only under a
  condition.
  - Unsafe: when nothing tests the condition again;
    `process_init_reply()` does not mask the reply with the offered flags,
    so a server can set a bit the kernel never sent.
  - Safe: test the condition again at the reply, as `FUSE_PASSTHROUGH` does
    with `IS_ENABLED(CONFIG_FUSE_PASSTHROUGH)` and `FUSE_OVER_IO_URING`
    with `fuse_uring_enabled()`.
  - Safe: when every user of the bit tests the condition first, as
    `fuse_should_enable_dax()` tests `fc->dax_mode` and `fc->dax` before
    `fc->inode_dax`.

## Access and credentials

**Namespaces and credentials**

- `fuse_fill_creds()` in `fs/fuse/req.c`: the only place that fills request
  credentials. It writes `args->uid`, `args->gid` and `args->pid` in
  `struct fuse_args`; `fuse_args_to_req()` in `fs/fuse/dev.c` copies them to
  the header.
- There is no fuse_force_creds() here, and `fuse_get_req()` does not touch
  credentials.
- `fc->user_ns`: the `user_ns` argument of `fuse_conn_init()`.
  `fuse_get_tree()` passes `fsc->user_ns`; CUSE passes
  `file->f_cred->user_ns`.
- `/dev/fuse` fd opened in another user namespace: rejected by
  `fuse_opt_fd()` while the `fd=` parameter is parsed.
- `user_id=` and `group_id=`: `fs_param_is_uid()` and `fs_param_is_gid()`
  convert with `current_user_ns()`; `fuse_parse_param()` then requires a
  mapping in `fsc->user_ns`.
- Reply uid and gid: `make_kuid()` and `make_kgid()` results are stored in
  the inode unchecked; `fuse_invalid_attr()` tests only mode and size.
- `fuse_fill_creds()` chooses by `SB_I_NOIDMAP` on `fm->sb`, not by whether
  the mount in use is idmapped. `fm->sb` NULL counts as `SB_I_NOIDMAP` set.

| Request | `SB_I_NOIDMAP` set | `SB_I_NOIDMAP` clear |
|---|---|---|
| not `force` | `from_kuid()`/`from_kgid()` of fsuid/fsgid; `-EOVERFLOW` if either is unmapped | ids from `mapped_fsuid()`/`mapped_fsgid()` with the idmap passed; no `-EOVERFLOW`; with `&invalid_mnt_idmap` both are `FUSE_INVALID_UIDGID` |
| `force`, not `nocreds` (for example `fuse_flush()`) | `from_kuid_munged()`/`from_kgid_munged()` | `FUSE_INVALID_UIDGID` |
| `force` and `nocreds` | uid and gid not written | uid and gid not written |

- `args->pid`: written for every row above, before the `force` test.
- `fuse_simple_background()` and `fuse_simple_notify_reply()`: always pass
  `&invalid_mnt_idmap`.
- `FS_ALLOW_IDMAP`: unconditional in `fs_flags` of `fuse_fs_type`,
  `fuseblk_fs_type` and the type in `fs/fuse/virtio_fs.c`.
- `SB_I_NOIDMAP`: set by `fuse_sb_defaults()`, cleared only by
  `process_init_reply()`, tested by `can_idmap_mount()` in `fs/namespace.c`.
- `FUSE_ALLOW_IDMAP` without `fc->default_permissions`:
  `process_init_reply()` fails the connection (`fc->conn_error = 1`).
- `FUSE_POSIX_ACL` in the same reply sets `fc->default_permissions` before
  that test, so it satisfies it without the mount option.
- `fuse_simple_idmap_request()`: three call sites, all in `fs/fuse/dir.c`:
  `create_new_entry()`, `fuse_create_open()`, `fuse_rename_common()`.
- `fuse_rename2()`: passes the real idmap only with `RENAME_WHITEOUT`.
- `fuse_link()`: passes `&invalid_mnt_idmap`, through `create_new_nondir()`
  to `create_new_entry()`.
- getattr, setattr and permission requests go through
  `fuse_simple_request()`; the idmap is applied to their payload or result,
  in `iattr_to_fattr()`, `fuse_fillattr()` and `generic_permission()`.
- **Potentially unsafe usage**: sending a request that creates an inode
  through `fuse_simple_request()`.
  - Unsafe: when the server uses the header uid and gid as the owner of the
    new inode; with `SB_I_NOIDMAP` clear it receives `FUSE_INVALID_UIDGID`.
  - Safe: `fuse_simple_idmap_request()` with the idmap the VFS passed, as
    `fuse_mkdir()` does through `create_new_entry()`; `fuse_fill_creds()`
    defines the mapping.
  - Safe: `FUSE_LINK`, which creates no inode; `fuse_link()` passes
    `&invalid_mnt_idmap`.

**Access by other users**

- `fuse_permissible_uidgid()`: compares euid, suid, uid with `fc->user_id`
  and egid, sgid, gid with `fc->group_id`. It does not compare fsuid or fsgid.
- `current_in_userns(fc->user_ns)`: tested only when `fc->allow_other` is
  set. Without `allow_other` the user namespace is not tested.
- `allow_sys_admin_access` (module parameter in `fs/fuse/dir.c`, default
  off): with it, `capable(CAP_SYS_ADMIN)` overrides a failed test in either
  branch.
- Callers: search for `fuse_allow_current_process` in `fs/fuse`; they are in
  `fs/fuse/dir.c`, `fs/fuse/inode.c`, `fs/fuse/xattr.c` and
  `fs/fuse/ioctl.c`.
- Not callers: `fuse_lookup()`, `fuse_open()`, `fuse_dir_open()`,
  `fuse_atomic_open()`, `fuse_get_link()`, `fuse_access()`,
  `fuse_xattr_get()`, `fuse_xattr_set()`, `fuse_get_acl()`, `fuse_set_acl()`.
- There is no fuse_open_common() here.
- Open: the test runs because `may_open()` in `fs/namei.c` calls
  `inode_permission()`, which reaches `fuse_permission()`.
- `fuse_ioctl_common()`: the one file operation that runs the test on every
  call. CUSE calls `fuse_do_ioctl()` directly and skips it.
- Fileattr get and set: tested in `fuse_priv_ioctl_prepare()`.

| Denied caller in | Result |
|---|---|
| `fuse_getattr()`, `request_mask` zero | 0; only `stat->dev` set, `stat->result_mask = 0`; no request |
| `fuse_getattr()`, otherwise | `-EACCES` |
| `fuse_statfs()` | 0; only `buf->f_type = FUSE_SUPER_MAGIC`; no request |
| other callers | `-EACCES` |

- **Potentially unsafe usage**: an inode or superblock operation that sends
  a request without calling `fuse_allow_current_process()`.
  - Unsafe: when the VFS reaches the operation without a prior
    `inode_permission()` on an inode of this connection; a task that fails
    the test then waits on the server.
  - Safe: when the VFS calls `inode_permission()` on the inode or its parent
    first, since `fuse_permission()` runs the test before it sends a
    request; for example `fuse_unlink()` after `may_delete_dentry()`,
    `create_new_entry()` after `may_create_dentry()`.
  - Safe: when the operation runs the test itself before it sends, as
    `fuse_setattr()`, `fuse_listxattr()` and `fuse_statfs()` do.

**Limits on the server**

- `process_init_limits()`: the clamp to `max_user_bgreq` and
  `max_user_congthresh` is lifted by `capable(CAP_SYS_ADMIN)`, not
  `CAP_SYS_RESOURCE`.
- `request_wait_answer()`, request without `args->abort_on_kill`: a fatal
  signal ends the wait only while the request is still `FR_PENDING`. Once
  `FR_PENDING` is clear, for example after the server has read the request,
  the task waits in an uninterruptible `wait_event()`.
- After that point the wait ends when the request is ended, for example by
  a reply, by `fuse_chan_abort()` (which the request timeout calls) or by
  `fuse_dev_release()` of the device that read it; a signal does not end it.
- `args->force` in `fuse_chan_send()`: sets `FR_FORCE` unless
  `args->abort_on_kill` is set, so the killable wait is skipped.
  `fuse_flush()` sets `args.force`, so it is not killable.
- Request timeout: `fuse_check_timeout()` in `fs/fuse/req_timeout.c`, state
  in `fch->timeout`. `struct fuse_conn` has no `timeout` field, and there is
  no FUSE_DEFAULT_REQ_TIMEOUT.
- `fuse_release()`: calls `write_inode_now(inode, 1)` first when
  `fc->writeback_cache` is set, so the closing task waits for writeback.
  Only the `FUSE_RELEASE` request is asynchronous.
- Writeback: there is no tmp_page copy and no NR_WRITEBACK_TEMP. The
  page-cache folio itself is under writeback
  (`fuse_iomap_writeback_range()`), so `folio_wait_writeback()` on a FUSE
  folio waits for the server.
- `mapping_writeback_may_deadlock_on_reclaim()`: called only in
  `mm/vmscan.c`. `mm/migrate.c` does not test it and calls
  `folio_wait_writeback()` in `MIGRATE_SYNC` mode.
- `fuse_sync_fs()`: returns 0 unless `fc->sync_fs`, which is set for fuseblk
  in `fuse_fill_super_common()` and in `fs/fuse/virtio_fs.c`.
- `SB_I_UNTRUSTED_MOUNTER`: set in `fuse_sb_defaults()`, only when
  `sb->s_user_ns` is not `init_user_ns`.
- `SB_I_NODEV`: set by `alloc_super()` in `fs/super.c` when `s_user_ns` is
  not `init_user_ns`. `fs/fuse` forces neither nosuid nor nodev.
- **Potentially unsafe usage**: a synchronous `fuse_simple_request()` from
  the final `fput()` of a file.
  - Unsafe: when the server is a local process; release requests set
    `args->force`, so the task waits in `request_wait_answer()` with no
    signal escape.
  - Safe: `fuse_simple_background()` with `args->end` set, as
    `fuse_file_put()` does when `sync` is false.
  - Safe: when `fc->auto_submounts` is set, which only
    `virtio_fs_get_tree()` does; `fuse_file_release()` passes it as `sync`.
  - Safe: `fuse_sync_release()` on the error path of an open or create, as
    in `fuse_open()`; the caller is the opener and the function warns if
    `ff->count` is above 1.

## Sending a request

**Send functions**

- Layout: `fuse_simple_request()` is an inline in `fs/fuse/fuse_i.h` around
  `__fuse_simple_request()`; that, `fuse_simple_background()` and
  `fuse_simple_notify_reply()` are in `fs/fuse/req.c`.
- Each runs `fuse_req_prep()` and then the transport half in `fs/fuse/dev.c`:
  `fuse_chan_send()`, `fuse_chan_send_bg()`, `fuse_chan_send_notify_reply()`.
- `fuse_simple_notify_reply()`: not static; called by `fuse_retrieve()` in
  `fs/fuse/notify.c`.
- `-ECONNREFUSED` and `-EOVERFLOW`: returned by `fuse_req_prep()` and
  `fuse_fill_creds()`, before any request is allocated, on all three paths.
- `fuse_get_req()`: fails only with `-EINTR`, `-ENOTCONN` or `-ENOMEM`.
- Reply with arguments of the wrong length on `/dev/fuse`: the requester gets
  `-EIO`; `-EINVAL` goes to the server's write, see `fuse_dev_do_write()`.
- `fuse_simple_notify_reply()` with the input queue disconnected: returns 0;
  `fuse_dev_queue_req()` ends the request with `-ENOTCONN`, delivered through
  `end`.
- `fuse_simple_notify_reply()` returns `-ENOTCONN` only when `fuse_get_req()`
  finds `connected` clear in `struct fuse_chan`; it never returns `-ENODEV`.
- Forgets: sent by `fuse_chan_queue_forget()` with no `struct fuse_req`, not by
  `fuse_simple_background()`; the exception is `fuse_force_forget()` in
  `fs/fuse/readdir.c`, a `fuse_simple_request()` with `force` and `noreply`.

**Flags on request arguments**

- `fuse_req_prep()` in `fs/fuse/req.c`: returns `-ECONNREFUSED` when
  `fc->conn_error` is set and `force` is clear, then calls
  `fuse_fill_creds()`.
- `force`, background: `fuse_chan_send_bg()` allocates with the caller's gfp
  and returns `-ENOMEM` on failure; `FR_FORCE` is not set.
- `force`, notify reply: ignored by `fuse_chan_send_notify_reply()`, which
  always calls `fuse_get_req()` and so can sleep and fail.
- `nocreds` without `force`: warns, then fills credentials as if the flag were
  clear.
- `noreply`: read only by `fuse_chan_send()`; `fuse_chan_send_notify_reply()`
  never sets `FR_ISREPLY`, whatever the flag says.
- `FR_ISREPLY` is tested in `fuse_dev_do_read()` and in
  `fs/fuse/virtio_fs.c`.
- `abort_on_kill`: read only on the sync path; set only by `fuse_send_init()`
  when `fc->sync_init`.
- `abort_on_kill`, fatal signal during the wait: `request_wait_answer()` calls
  `fuse_chan_abort()` and then waits uninterruptibly for `FR_FINISHED`; the
  request is not dequeued with `-EINTR`.
- Warnings, complete list for these four flags:
  - `WARN_ON(args->nocreds)` in `fuse_fill_creds()` when `force` is clear;
    reached from all three send functions.
  - `WARN_ON(args->force && !args->nocreds)` in `fuse_simple_background()` and
    in `fuse_simple_notify_reply()`.
  - No warning involves `noreply` or `abort_on_kill`.

**Blocking in request allocation**

- `fuse_get_req()`: takes `(fch, for_background)`; it has no idmap or
  credential handling.
- Sleep conditions in `fuse_block_alloc()`, any one of:
  - `initialized` is clear;
  - `for_background` and `blocked`;
  - `io_uring` and `connected` set and `fuse_uring_ready()` false; this one
    blocks foreground requests too.
- Without `CONFIG_FUSE_IO_URING`: `fuse_uring_conn_init()` is an empty stub, so
  `io_uring` stays 0 and the third condition is never true.
- `blocked`: follows `max_background`, not `congestion_threshold`.
- The wait: `wait_event_state_exclusive()` with
  `TASK_KILLABLE | TASK_FREEZABLE`; only a fatal signal ends it, and the
  sleeper can be frozen.
- After the sleep: only `connected` is tested; `fc->conn_error` was tested by
  `fuse_req_prep()` before the sleep and is not tested again.
- Ordering on `initialized`: `smp_load_acquire()` in `fuse_block_alloc()` pairs
  with `smp_store_release()` in `fuse_chan_set_initialized()`.
- Wakers of `blocked_waitq`:
  - `fuse_chan_set_initialized()`: wakes all; called from
    `process_init_reply()` and `fuse_chan_abort()`.
  - `fuse_chan_abort()`: wakes all, after clearing `blocked`.
  - `fuse_request_bg_finish()`: wakes one; called by `fuse_request_end()` and
    `fuse_uring_req_end()`.
  - `fuse_chan_max_background_set()`: `wake_up_nr()` for the free slots.
  - `fuse_put_request()`: wakes one for an unsent `FR_BACKGROUND` request, only
    when `blocked` is clear.
  - `fuse_get_req()`: wakes one only on its `-ENOMEM` path with
    `for_background`, without testing `blocked`.
  - `fuse_uring_do_register()`: wakes all when the ring becomes ready.
  - `fuse_uring_cmd()`: clears `io_uring` and wakes all when registration
    fails.
  - `fuse_drop_waiting()`: wakes all for `fuse_chan_wait_aborted()`.

**Background request accounting**

- `congestion_threshold`: field of `struct fuse_conn`, not under `bg_lock`;
  `fs/fuse/control.c` uses `READ_ONCE()` and `WRITE_ONCE()`.
- `fuse_chan_num_background()`: lockless `READ_ONCE()`; this is what
  `fuse_handle_readahead()` and `fuse_writepages()` compare with
  `congestion_threshold`.
- No congestion state is set or cleared anywhere in `fs/fuse`.
- `fuse_request_queue_background()` when connected and the ring is not ready:
  always appends to `bg_queue`, then calls `flush_bg_queue()`.
- `fuse_request_queue_background()` returning false: `fuse_chan_send_bg()`
  drops the request and returns `-ENOTCONN`; it does not call `end`.
- `fuse_request_bg_finish()`: clears `blocked` when `num_background` equals
  `max_background` before the decrement.
- `fuse_chan_max_background_set()`: recomputes `blocked` as
  `num_background >= max_background`; used by `process_init_limits()` and the
  control file.
- With the ring ready, `fuse_request_queue_background()` hands over to
  `fuse_uring_queue_bq_req()`:
  - same `num_background` and `blocked` accounting under `bg_lock`;
  - the request waits on the per-queue `fuse_req_bg_queue`, not on `bg_queue`;
  - `fuse_uring_flush_bg()` lets one background request per queue go active
    even when `active_background` has reached `max_background`;
  - `fuse_uring_queue_bq_req()` tests `queue->stopped`, not `connected`, and
    returns false when set.
- `fuse_uring_req_end()`: calls `fuse_request_bg_finish()` itself, which clears
  `FR_BACKGROUND`, so `fuse_request_end()` skips its background branch.

**Completion callback**

- Signature: `void (*end)(struct fuse_args *args, int error)` in
  `fs/fuse/args.h`; no `struct fuse_mount` argument, so the callback takes it
  from its container, as `process_init_reply()` does.
- `may_block`: read only by `virtio_fs_requests_done_work()`; it does not
  decide whether `end` may sleep on any other transport.
- `may_block` setters: `fuse_async_req_send()` from `io->should_dirty`, and
  `fuse_file_put()` for the async release of a DAX inode.
- Lock state: call sites of `fuse_request_end()` drop their queue spinlock
  first; see `fuse_chan_abort()`, which calls `fuse_dev_end_requests()` after
  unlocking.
- Abort contexts: `fuse_chan_abort()` runs `end` with `-ECONNABORTED`, also
  from the `fuse_check_timeout()` worker.
- `fuse_simple_notify_reply()` returning 0: `end` may already have run in the
  caller's task with `-ENOTCONN`, from `fuse_dev_queue_req()`.
- `fuse_simple_background()`: `end` is not run in the caller's task;
  `fuse_send_writepage()` relies on it, calling under `fi->lock`, which
  `fuse_writepage_end()` takes.
- **Unsafe usage**: setting `end` on a request sent with
  `fuse_simple_request()`; `fuse_args_to_req()` sets `FR_ASYNC` whenever `end`
  is set, on the sync path too, and `fuse_request_end()` wakes the waiter
  before it calls `end`, so `args` can be gone.
  - Safe: leave `end` NULL and call the function after the send returns, as
    the sync branch of `fuse_file_put()` does with `fuse_release_end()`.
- **Potentially unsafe usage**: a `send_req` op of `struct fuse_iqueue_ops`
  calling `fuse_request_end()` on the request it was given.
  - Unsafe: for an `FR_BACKGROUND` request; `flush_bg_queue()` calls `send_req`
    under `bg_lock`, which `fuse_request_end()` takes, and the sender may hold
    a lock that `end` takes.
  - Safe: `virtio_fs_send_req()` puts a failed request on `fsvq->end_reqs`, and
    `virtio_fs_request_dispatch_work()` ends it.
  - Safe: `fuse_dev_queue_req()` ends a request only when `fiq->connected` is
    clear; `fuse_chan_abort()` clears `connected` of `struct fuse_chan` and
    empties `bg_queue` before it clears `fiq->connected`, so no background
    request reaches that branch.
  - Safe: `fuse_uring_queue_fuse_req()` ends a request only for a missing or
    stopped queue; `is_ring_ready()` requires every queue before `fiq->ops` is
    switched, and `queue->stopped` is set by `fuse_uring_abort()`, which
    `fuse_chan_abort()` calls after it emptied `bg_queue`, so no background
    request reaches those branches.

## Request state

**Request flag bits**

- `FR_SYNC_WAKEUP`: `__fuse_request_send()` sets it;
  `fuse_dev_queue_req()` takes it with `test_and_clear_bit()` before
  `fiq->lock` and uses it to pick `wake_up_sync()`.
- `FR_URING`: set under `queue->lock` of `struct fuse_ring_queue` in
  `fuse_uring_queue_fuse_req()` and `fuse_uring_queue_bq_req()`; never
  cleared; `request_wait_answer()` tests it with no lock.
- `FR_ASYNC`: set by `fuse_args_to_req()` when `args->end` is set; it has
  nothing to do with io_uring.
- `FR_FORCE`: set by `fuse_chan_send()` only when `args->force` is set and
  `args->abort_on_kill` is not; its only test is in `request_wait_answer()`.
- `FR_BACKGROUND`: cleared by `fuse_request_bg_finish()`, which asserts
  `fch->bg_lock`.
- `FR_PENDING`: set in `fuse_request_init()`; set again only by
  `fuse_chan_resend()` under `fiq->lock`.
- `FR_PENDING` cleared under `fiq->lock`: by `fuse_dev_do_read()` and
  `fuse_chan_abort()`.
- `FR_PENDING` cleared with no lock: where the request is on no list, for
  example `fuse_dev_queue_req()` when `fiq->connected` is clear, and
  `virtio_fs_send_req()`.
- `fuse_remove_pending_req()`: tests `FR_PENDING` under the list lock and
  leaves it set.
- `FR_LOCKED`: `lock_request()` and `unlock_request()` change it under
  `req->waitq.lock`; `fuse_dev_do_write()` sets it and both device paths
  clear it under `fpq->lock`; `fuse_chan_abort()` tests it under both.
- `FR_LOCKED` on the read path: first set by `lock_request()` inside
  `fuse_copy_fill()`, so a request just added to `fpq->io` is not yet locked.
- `FR_SENT`: `fuse_dev_do_read()` sets it under `fpq->lock`;
  `fuse_dev_do_write()` and `fuse_chan_resend()` clear it under `fpq->lock`;
  `fuse_dev_end_requests()` clears it with no lock, on a private list.
- `FR_ABORTED` and `FR_PRIVATE`: set only in `fuse_chan_abort()`, only on
  requests found on `fpq->io`, under `fpq->lock` plus `req->waitq.lock`.
- `FR_PRIVATE`: set only if `FR_LOCKED` is clear; resend and release do not
  set it.
- `FR_PENDING` (initial), `FR_WAITING`, `FR_BACKGROUND`, `FR_FORCE`,
  `FR_ISREPLY`, `FR_ASYNC`: set with `__set_bit()`, not an atomic bitop,
  before the request is queued; `__clear_bit()` is used for `FR_ISREPLY`
  before queueing and for `FR_WAITING` at the last put.

**Lists a request is on**

- Between `fiq->pending` and `fpq->io`: `fuse_dev_do_read()` holds the
  request on no list and under no lock while it tests the buffer size.
- Abort in that window: cannot reach the request; the reader's test of
  `fpq->connected` under `fpq->lock` ends it with -ECONNABORTED.
- `struct fuse_pqueue`: one per `struct fuse_dev`; `fuse_dev_do_write()`
  searches only the `fpq->processing` of the device written to.
- Lookup: there is no request_find(); the function is
  `fuse_request_find()` in `fs/fuse/dev.c`, which `fuse_dev_do_write()`
  calls under `fpq->lock`.
- `fch->devices`: walked under `fch->lock`, with `fpq->lock` nested inside,
  in `fuse_chan_abort()`, `fuse_chan_resend()` and `fuse_check_timeout()`.
- `fiq->lock`: nests inside `fch->bg_lock`, since `flush_bg_queue()` calls
  `fiq->ops->send_req()` with `fch->bg_lock` held.
- Private lists: `to_end` in `fuse_chan_abort()` and `fuse_dev_release()`,
  `to_queue` in `fuse_chan_resend()`; filled under the source list's lock;
  `fuse_dev_end_requests()` consumes them with no lock, and
  `fuse_chan_resend()` splices `to_queue` onto `fiq->pending` under
  `fiq->lock`.
- `fpq->io` insertion: `list_add()` on read and `list_move()` on write, both
  at the head; `fpq->processing` and `fiq->pending` are filled at the tail,
  except that `fuse_chan_resend()` splices at the head of `fiq->pending`.

**Request identifiers**

- Resend function: there is no fuse_resend(); `fuse_chan_resend()` in
  `fs/fuse/dev.c` does it, called by `fuse_notify_resend()` in
  `fs/fuse/notify.c`.
- Resent request: keeps its id; `fuse_chan_resend()` ORs
  `FUSE_UNIQUE_RESEND` into `req->in.h.unique` under `fiq->lock`.
- Reply after a resend: `fuse_request_find()` compares the whole id, so a
  reply with the id read before the resend fails with -ENOENT.
- `fuse_req_hash()`: masks only `FUSE_INT_REQ_BIT`, so the resent request
  lands in the bucket of the new id.
- `fiq->reqctr`: a plain `u64` under `fiq->lock` on every transport;
  `fuse_request_assign_unique()`, used by virtiofs and fuse-over-io-uring,
  calls `fuse_get_unique()`.
- Interrupted request on resend: requeued like any other;
  `fuse_chan_resend()` only unlinks its `req->intr_entry`.
- INTERRUPT after a resend: `fuse_read_interrupt()` builds both ids from
  `req->in.h.unique` at read time, so they carry `FUSE_UNIQUE_RESEND`.
- `fiq->connected` clear in `fuse_chan_resend()`: the requests go to
  `fuse_dev_end_requests()` before `FR_PENDING` is ever set.
- Scope of resend: only the `fpq->processing` buckets of devices on
  `fch->devices`; requests on `fpq->io` are left alone.

**Waiting for a reply**

- First wait, `wait_event_interruptible()`: a signal never makes the task
  return; it sets `FR_INTERRUPTED` and the task goes on to the next wait.
- `queue_interrupt()` after the first wait: called only if `FR_SENT` is
  already set; otherwise `fuse_dev_do_read()` queues the interrupt.
- Second wait: `wait_event_killable()`; skipped only when `FR_FORCE` is set.
- `args->abort_on_kill`: on a fatal signal the task calls
  `fuse_chan_abort()` on the whole channel, then waits uninterruptibly.
- `args->abort_on_kill` with `args->force`: `fuse_chan_send()` leaves
  `FR_FORCE` clear, so the killable wait still runs; `fuse_send_init()` sets
  this for a synchronous INIT.
- Killed while pending: `fuse_remove_pending_req()` takes `fiq->lock`, or
  for `FR_URING` the `queue->lock` of `req->ring_queue`.
- Killed-pending request: never passes through `fuse_request_end()`;
  `FR_FINISHED` stays clear, `FR_PENDING` stays set, error is -EINTR.
- Return with no server reply, request ended by the kernel, on `/dev/fuse`:

| Case | Where | Error |
|---|---|---|
| `fiq->connected` clear at queue time | `fuse_dev_queue_req()` | -ENOTCONN |
| read buffer smaller than the request | `fuse_dev_do_read()` | -EIO; -E2BIG for `FUSE_SETXATTR` |
| `fpq->connected` clear at read | `fuse_dev_do_read()` | -ECONNABORTED |
| copy to the server fails | `fuse_dev_do_read()` | -EIO |
| `FR_ISREPLY` clear (`args->noreply`) | `fuse_dev_do_read()`, after the copy | 0 |
| abort, or release of the device | `fuse_dev_end_requests()` | -ECONNABORTED |

**Interrupt requests**

- `queue_interrupt()`: takes no lock and touches no list; it returns
  -EINVAL if `FR_INTERRUPTED` is clear, else calls
  `fiq->ops->send_interrupt()` and returns 0.
- `fuse_dev_queue_interrupt()`: under `fiq->lock`, queues only if
  `req->intr_entry` is empty and `FR_SENT` is set.
- `FR_SENT` test under `fiq->lock`: orders the queueing against
  `fuse_chan_resend()`, which clears `FR_SENT` under `fpq->lock` and then
  unlinks `req->intr_entry` under `fiq->lock`.
- Resent request with `FR_INTERRUPTED`: gets its INTERRUPT when it is read
  again, from the `FR_INTERRUPTED` test in `fuse_dev_do_read()`.
- -EAGAIN reply to an INTERRUPT: `fuse_dev_do_write()` returns the result of
  `queue_interrupt()`, so the write fails with -EINVAL if `FR_INTERRUPTED`
  is clear.
- Interrupt reply lookup: uses `fpq->processing`, so a reply for a request
  that is no longer there fails with -ENOENT.
- virtiofs: `virtio_fs_send_interrupt()` is empty.

**Request timeouts**

- Timeout: exists; the code is in `fs/fuse/req_timeout.c`, the state is
  `fch->timeout.req_timeout` and `fch->timeout.work` in `struct fuse_chan`.
- `fuse_init_server_timeout()`: called only from `process_init_reply()`,
  for a reply with no error and a matching major, so no limit runs before
  the INIT reply.
- Limit, in order:
  1. `request_timeout` of the INIT reply if `FUSE_REQUEST_TIMEOUT` is set,
     else 0.
  2. If 0, `fuse_default_req_timeout`.
  3. `min_not_zero()` with `fuse_max_req_timeout`: a non-zero maximum alone
     turns the timeout on.
  4. If still 0, no work is queued.
  5. Raised to at least `FUSE_TIMEOUT_TIMER_FREQ` seconds; not rounded.
- Work queue: `system_percpu_wq`, re-queued every
  `FUSE_TIMEOUT_TIMER_FREQ` seconds.
- `fuse_check_timeout()`: tests only the first entry of each list, with
  `fuse_request_expired()`.
- Lists tested: `fiq->pending`, `fch->bg_queue`, then for each device on
  `fch->devices` its `fpq->io` and every `fpq->processing` bucket.
- Ring queues: `fuse_uring_request_expired()` tests four lists per queue
  under `queue->lock`; it is a stub returning false without
  `CONFIG_FUSE_IO_URING`.
- `fch->num_waiting` zero: the check re-arms without looking at any list.
- `fch->connected` clear: the check returns without re-arming.
- Expiry: calls `fuse_chan_abort()` with `abort_with_err` false and does not
  re-arm.
- Cancel: `fuse_chan_abort()` uses `cancel_delayed_work()`;
  `fuse_chan_release()` uses `cancel_delayed_work_sync()`.

**Aborting a connection**

- Names: there is no fuse_abort_conn() or fuse_wait_aborted();
  `fuse_chan_abort()` and `fuse_chan_wait_aborted()` in `fs/fuse/dev.c` take
  a `struct fuse_chan`.
- Helpers: `fuse_chan_set_initialized()`, `fuse_end_polls()` and
  `fuse_dev_end_requests()` do the jobs of fuse_set_initialized(),
  end_polls() and end_requests().
- Order of the lists: `fpq->io`, then `fpq->processing`, then
  `fch->bg_queue` flushed through `flush_bg_queue()` (on `/dev/fuse` into
  `fiq->pending`), then `fiq->pending`.
- `fch->blocked`: cleared, not set, together with
  `fch->max_background = UINT_MAX`, under `fch->bg_lock`.
- Second call: does nothing to the lists once `fch->connected` is clear.
- Device read after abort: -ECONNABORTED if `fch->abort_with_err`, else
  -ENODEV; there is no fc->aborted.
- `abort_with_err`: only `fuse_conn_abort_write()` passes a value other
  than false, namely `fc->abort_err`.
- Device write after abort: -ENOENT for a reply, -EINVAL for a
  notification; not -ENODEV.
- Callers: search for `fuse_chan_abort(`; the ones easy to miss are
  `request_wait_answer()` for `args->abort_on_kill` and `fuse_dev_install()`
  when the install fails.
- `fs/fuse/dev_uring.c`: does not call `fuse_chan_abort()`;
  `fuse_uring_abort()` is called by it, after `fch->lock` is dropped.
- `fuse_dev_release()` of a device that is not the last: ends that device's
  `fpq->processing` requests with -ECONNABORTED and does not abort.
- `fuse_chan_wait_aborted()`: called only from `fuse_conn_destroy()`, right
  after the abort.
- Wake-up for `fuse_chan_wait_aborted()`: `fuse_drop_waiting()` wakes
  `fch->blocked_waitq` only when `fch->num_waiting` reaches 0 and
  `fch->connected` is clear, so the wait must follow an abort.

**Ending a request**

- `FR_FINISHED`: may already be set; the call then only drops one reference.
- Double end: `fuse_chan_abort()` relies on it for a request it took from
  `fpq->io`, and takes a reference of its own for that second call.
- `WARN_ON()` for `FR_PENDING` and `FR_SENT`: runs only on the first call;
  it warns and the function goes on.
- `FR_LOCKED`: not tested by `fuse_request_end()`; `fuse_dev_do_read()` and
  `fuse_dev_do_write()` clear it under `fpq->lock` before they call.
- `fuse_dev_end_requests()`: sets -ECONNABORTED and clears `FR_SENT`, not
  `FR_PENDING`; `fuse_chan_abort()` clears `FR_PENDING` under `fiq->lock`
  before it splices.
- `req->intr_entry`: unlinked by `fuse_request_end()` only if
  `FR_INTERRUPTED` is set; `fuse_request_free()` warns if it is still linked.
- Reference consumed: the one from `fuse_request_alloc()`; a background
  request has no other, so it is freed inside the call, after `args->end`.
- Sync request: survives the call through the reference taken in
  `__fuse_request_send()`, dropped by `fuse_chan_send()`.
- **Unsafe usage**: reading `req` after `fuse_request_end()` returns,
  without a reference of one's own.
  - Safe: `fuse_dev_do_read()` takes `__fuse_get_request()` under
    `fpq->lock` before it sets `FR_SENT`, since a reply can end the request
    once that lock is dropped, and drops it after its `FR_INTERRUPTED` test.
  - Safe: `fuse_chan_send()` reads `req->out.h.error` under the reference
    from `__fuse_request_send()`.

## Device read and write

**Reading a request**

- Transport state: `fuse_dev_do_read()` reads it from `struct fuse_chan`
  (`fud->chan`), not `struct fuse_conn`: `fch->max_write`,
  `fch->abort_with_err`, and `fch->minor` in `fuse_read_forget()`.
- Buffer minimum: the larger of `FUSE_MIN_READ_BUFFER` and
  `sizeof(struct fuse_in_header) + sizeof(struct fuse_write_in) +
  fch->max_write`; smaller gives `-EINVAL` before anything is dequeued.
- Forgets and requests both queued: `fiq->forget_batch` lets 8 request reads
  through, then 16 forget reads, then repeats.
- Interrupt or single forget: `fuse_read_interrupt()` and
  `fuse_read_single_forget()` make no size test; the minimum at entry is the
  only bound.
- Batch forget: `fuse_read_batch_forget()` limits the count to what fits in
  `nbytes`; the rest stay queued.
- Request larger than the buffer: the requester gets `-EIO` (`-E2BIG` for
  `FUSE_SETXATTR`); the read does not fail, it goes to `restart` and returns
  the next item, or waits.
- `fpq->connected` clear before the request goes on `fpq->io`: the request
  ends with `-ECONNABORTED` and the read returns `-ECONNABORTED`, whatever
  `fch->abort_with_err` holds.
- `fpq->connected` clear after the copy: the read returns `-ECONNABORTED` if
  `fch->abort_with_err`, else `-ENODEV`.
- Copy error: the requester gets `-EIO`; the read returns the copy's own
  error.
- `FR_INTERRUPTED` set when the request reaches `FR_SENT`: the read calls
  `queue_interrupt()`; it does not end the request.

**Notifications from the server**

- State test: in `fuse_dev_do_write()`, not in `fuse_notify()`; `-EINVAL`
  unless `fch->initialized` and `fch->connected` (fields of
  `struct fuse_chan`).
- `fch->initialized`: set by `fuse_chan_set_initialized()`, which
  `process_init_reply()` calls for a failed INIT too, and `fuse_chan_abort()`
  calls after clearing `fch->connected`.
- The test is lockless and made once; a handler can run while
  `fuse_chan_abort()` runs.
- Only `fuse_dev_do_write()` calls `fuse_notify()`; virtio-fs and the io_uring
  commit path deliver no notifications.
- `fuse_copy_finish()`: `fuse_dev_do_write()` calls it after `fuse_notify()`
  returns, so a handler may return without it; for example
  `fuse_notify_store()` and `fuse_notify_prune()` have no call of their own.
- Handlers that call `fuse_copy_finish()` themselves do so after their last
  copy and before they take a lock, for example `fuse_notify_inval_inode()`
  before `fc->killsb`.
- `fuse_ilookup()`: warns unless `fc->killsb` is held; the inode is kept by
  the reference it returns, dropped with `iput()`.
- Kinds other than `FUSE_NOTIFY_INVAL_ENTRY` and `FUSE_NOTIFY_DELETE`:

| Code | Held while the inode is used |
|---|---|
| `FUSE_NOTIFY_POLL` | no inode; `fc->lock` in `fuse_notify_poll_wakeup()` |
| `FUSE_NOTIFY_INVAL_INODE` | `fc->killsb` read; `fi->lock` only around the `attr_version` bump; no `inode_lock()`, also for the range case |
| `FUSE_NOTIFY_STORE` | `fc->killsb` read, held across the copy from the server; folio lock per folio; `fi->lock` inside `fuse_write_update_attr()`; no `inode_lock()` |
| `FUSE_NOTIFY_RETRIEVE` | `fc->killsb` read; folio references only, no folio lock |
| `FUSE_NOTIFY_PRUNE` | `fc->killsb` read, taken per batch of 512 node ids; inode reference only |
| `FUSE_NOTIFY_RESEND` | no inode; `fch->lock` with `fpq->lock` nested, then `fiq->lock` alone |
| `FUSE_NOTIFY_INC_EPOCH` | no inode, no lock; `atomic_inc()` on `fc->epoch`, `schedule_work()` if `inval_wq` |

**Copying and abort**

- `fuse_chan_abort()`: never waits for `FR_LOCKED`; it sets `FR_ABORTED`,
  skips a locked request and leaves it on `fpq->io` for the copier to end.
- `FR_ABORTED`: set in one place, the walk of `fpq->io` in
  `fuse_chan_abort()`; a request on no `fpq->io` gets no protection from
  `lock_request()`.
- Before the copy: test `fpq->connected` under `fpq->lock`, then put the
  request on `fpq->io`; a request added after the abort walked the list is
  never ended by it.
- Read side: `fuse_dev_do_read()` does not set `FR_LOCKED`; the first
  `fuse_copy_fill()` does, after its `unlock_request()` has tested
  `FR_ABORTED`.
- Write side: `fuse_dev_do_write()` sets `FR_LOCKED` under `fpq->lock` when
  it moves the request to `fpq->io`.
- References: the copier takes none for the copy; `fuse_chan_abort()` takes
  one with `__fuse_get_request()` for each unlocked request it takes from
  `fpq->io`, so the copier's later `fuse_request_end()` has a reference to
  drop.
- After the copy, both sides: under `fpq->lock` clear `FR_LOCKED` and test
  `fpq->connected`; to end the request, call `list_del_init()` only if
  `FR_PRIVATE` is clear, then call `fuse_request_end()` outside the lock.
- `fuse_dev_do_write()`: tests `fpq->connected`, not `FR_ABORTED`, and calls
  `fuse_request_end()` on every path once it has moved the request to
  `fpq->io`.
- Steps that may sleep run between `unlock_request()` and `lock_request()`:
  `iov_iter_get_pages2()`, `pipe_buf_confirm()`, `alloc_page()` in
  `fuse_copy_fill()`; `pipe_buf_try_steal()` in `fuse_try_move_folio()`.
- `struct fuse_copy_state`: has no is_kaddr field; `is_uring`,
  `skip_folio_copy` and `ring.copied_sz` serve the io_uring copy.
- io_uring: `setup_fuse_copy_state()` sets `cs->req`, but its requests are
  never on `fpq->io`, so `lock_request()` cannot fail there.
- **Unsafe usage**: using `req->args` or its folios after `lock_request()`
  or `unlock_request()` returned `-ENOENT`.
  - Unsafe: `fuse_chan_abort()` may have handed the request to
    `fuse_dev_end_requests()`, which may already have woken the requester
    that owns the args.
  - Safe: stop copying and run the end sequence, touching only `req->flags`
    and `req->list` under `fpq->lock`, as the `out_end` path of
    `fuse_dev_do_read()` does.

**Splice and moved folios**

- `page_replace`: set only by `fuse_send_readpages()` in `fs/fuse/file.c`,
  the readahead path; `fuse_do_readfolio()` does not set it, so its reply is
  copied.
- Pipe buffer: `fuse_try_move_folio()` tests
  `buf->len == folio_size(oldfolio)`; it does not test `buf->offset`.
- Previous buffer: `fuse_copy_folio()` tries a move only when `cs->len` is 0,
  so the data must start at a pipe buffer boundary.
- Large stolen folio: `folio_test_large(newfolio)` falls back to the copy.
- `fuse_check_folio()`: rejects a mapped folio, a non-NULL `mapping`, or any
  flag in `PAGE_FLAGS_CHECK_AT_PREP` outside the set it lists; `PG_lru`,
  `PG_active`, `PG_workingset`, `PG_reclaim`, `PG_waiters`, `PG_locked`,
  `PG_referenced`, `LRU_GEN_MASK` and `LRU_REFS_MASK` are tolerated.
- `fuse_check_folio()`: makes no reference count test; the sole-owner test
  is in the pipe's `try_steal` operation, for example
  `generic_pipe_buf_try_steal()`.
- Uptodate: `fuse_try_move_folio()` clears it on the stolen folio before the
  check, so it never causes a fallback.
- Abort: `lock_request()` runs before `replace_page_cache_folio()`; on
  `-ENOENT` the page cache is unchanged, the stolen folio is unlocked and the
  function returns `-ENOENT`.
- No `FR_ABORTED` test follows the replace.
- On success the request stays locked and `cs->len` is 0.
- Old folio: no test for a changed slot or truncation; the folio lock held by
  the read path is what keeps it in the mapping.
- New folio: stays locked after the move; `fuse_readpages_end()` ends the
  read through `iomap_finish_folio_read()` on `ap->folios[i]`.
- **Unsafe usage**: setting `page_replace` on a request whose folios are not
  locked page cache folios with a reference owned by the folio array.
  - Safe: `fuse_send_readpages()`, whose folios come locked from readahead
    with a `folio_get()` from `fuse_handle_readahead()`;
    `replace_page_cache_folio()` asserts both folios locked with
    `VM_BUG_ON_FOLIO()`, and `fuse_try_move_folio()` unlocks the old folio
    and drops the array's reference.
- **Unsafe usage**: using a folio pointer saved before the request, after a
  `page_replace` request has ended.
  - Safe: read the folio back from `ap->folios[i]`, as `fuse_readpages_end()`
    does; `fuse_try_move_folio()` stores the new folio there.

**Transport callbacks**

- Three tables implement `struct fuse_iqueue_ops`: `fuse_dev_fiq_ops`,
  `virtio_fs_fiq_ops`, and `fuse_io_uring_ops` in `fs/fuse/dev_uring.c`
  (built with `CONFIG_FUSE_IO_URING`).
- `fuse_io_uring_ops`: installed with `WRITE_ONCE(fiq->ops, ...)` in
  `fuse_uring_do_register()` once the ring is ready; `send_req` is
  `fuse_uring_queue_fuse_req()`.
- `fuse_io_uring_ops`: `send_forget` and `send_interrupt` are
  `fuse_dev_queue_forget()` and `fuse_dev_queue_interrupt()`, so forgets and
  interrupts still go out through a read of the device.
- Background requests queued once the ring is ready: bypass `send_req`;
  `fuse_request_queue_background_uring()` sets `in.h.len`, assigns the
  identifier and calls `fuse_uring_queue_bq_req()`.
- Locks at entry: `fuse_send_one()` holds no `fiq->lock`; `flush_bg_queue()`
  calls it under `fch->bg_lock`.
- `FR_PENDING`: set by `fuse_request_init()`, not by `send_req`.
- Identifier: use `fuse_request_assign_unique()` or, under `fiq->lock`,
  `fuse_request_assign_unique_locked()`; they skip `FUSE_NOTIFY_REPLY` and
  fire `trace_fuse_request_send()`, which a bare `fuse_get_unique()` does
  not.
- `fuse_uring_queue_fuse_req()`: keeps `FR_PENDING` set while the request
  waits on `queue->fuse_req_queue`; `fuse_uring_add_req_to_ring_ent()`
  clears it.
- `fuse_uring_queue_fuse_req()` with the queue stopped: error `-ENOTCONN`.
- virtio-fs, any error other than `-ENOSPC`, `-ENOMEM` included:
  `req->out.h.error` gets the return value of `virtio_fs_enqueue_req()`, not
  `-EIO`, and the request goes on `fsvq->end_reqs`.
- **Unsafe usage**: a `send_req` op leaving `FR_PENDING` set on a request
  that it puts on a list the lock chosen in `request_wait_answer()` does not
  protect.
  - Safe: `fuse_dev_queue_req()` queues on `fiq->pending` under `fiq->lock`,
    the lock `fuse_remove_pending_req()` is given.
  - Safe: `fuse_uring_queue_fuse_req()` sets `FR_URING` and
    `req->ring_queue`, so `fuse_uring_remove_pending_req()` takes
    `queue->lock`.
  - Safe: `virtio_fs_send_req()` clears `FR_PENDING` before it queues the
    request anywhere.

## The io-uring transport

**Enabling io-uring**

- Channel fields: `io_uring`, `ring`, `initialized`, `connected`,
  `blocked_waitq` and the background counters are in `struct fuse_chan`
  (`fs/fuse/fuse_dev_i.h`), written `fch->...`; `ring` exists only under
  `CONFIG_FUSE_IO_URING`; `struct fuse_ring` points back with `chan`.
- `process_init_reply()`: only sets `io_uring_enabled` in
  `struct fuse_chan_param`, when the reply has `FUSE_OVER_IO_URING` and
  `fuse_uring_enabled()` is true.
- `fuse_uring_conn_init()`: called from `fuse_chan_set_initialized()` in
  `fs/fuse/dev.c`, before `fch->initialized` is stored.
- `fuse_uring_conn_init()`: calls `fuse_uring_create()` and sets
  `fch->io_uring` only if that returned a ring.
- `fuse_uring_create()`: returns NULL on allocation failure or when
  `fch->connected` is 0; the connection then stays on the device path.
- `fuse_uring_register()`: does not create the ring; returns `-EINVAL` when
  `fch->ring` is NULL.
- `fuse_uring_cmd()`: returns `-EOPNOTSUPP` when its test finds
  `fch->io_uring` 0, whatever `enable_uring` holds.
- `is_ring_ready()`: walks all `ring->nr_queues` queues and skips the queue that
  just registered; there is no nr_queues_ready counter.
- Request with `force`: `fuse_chan_send()` and `fuse_chan_send_bg()` skip
  `fuse_get_req()`; if `fuse_send_one()` runs for it before ready, it lands on
  `fiq->pending` through `fuse_dev_queue_req()` and is served by a read of the
  device.
- `fuse_new_init()`: offers `FUSE_HAS_IO_URING_BUFPOOL` together with
  `FUSE_OVER_IO_URING`.

**Ring commands**

- Checks before dispatch, in order: `IO_URING_F_CANCEL`; `IO_URING_F_SQE128`
  missing gives `-EINVAL`; `fuse_get_dev()` error; `fch->initialized` 0 gives
  `-EAGAIN`; `fch->abort_with_err` gives `-ECONNABORTED`; `fch->connected` 0
  gives `-ENOTCONN`; `fch->io_uring` 0 gives `-EOPNOTSUPP`.

| Input | Return of `fuse_uring_cmd()` |
|---|---|
| `IO_URING_F_CANCEL` | 0 |
| `FUSE_IO_URING_CMD_REGISTER` | `-EIOCBQUEUED`, or errno |
| `FUSE_IO_URING_CMD_COMMIT_AND_FETCH` | `-EIOCBQUEUED`, or errno |
| `FUSE_IO_URING_CMD_ADD_QUEUE` | 0 or errno; command is never held |
| `FUSE_IO_URING_CMD_ADD_BUFPOOL` | 0 or errno; command is never held |
| any other `cmd_op` | `-EINVAL` |

- `FUSE_IO_URING_CMD_COMMIT_AND_FETCH`: returns `-EIOCBQUEUED` also when
  `fuse_uring_send()` has already completed the command inline.
- Failed `FUSE_IO_URING_CMD_REGISTER`: clears `fch->io_uring` and wakes
  `fch->blocked_waitq`; a failure of the other three commands does not.
- `FUSE_IO_URING_CMD_REGISTER` that finds `fch->connected` clear in
  `fuse_uring_do_register()`: the new entry is freed and the return is
  `-ECONNABORTED`.
- `-EACCES`: not returned by `fs/fuse/dev_uring.c`; `fuse_uring_add_queue()`
  returns `-EPERM` for `FUSE_URING_ZERO_COPY` without `CAP_SYS_ADMIN`.
- CQE of a held command: 0 after a request was copied, `-ENOTCONN` from cancel
  or teardown, `-ECANCELED` from cancelled task work; a copy error is never
  posted.
- Copy failure in `fuse_uring_send_in_task()`: the request is ended, the next
  one is tried, and with none waiting the command stays held.
- Notify replies: `fuse_chan_send_notify_reply()` calls `fuse_send_one()`, so
  they go through the ring once `fiq->ops` is `fuse_io_uring_ops`.
- Still read or written on the device: forgets and interrupts
  (`fuse_io_uring_ops`), `FUSE_INIT`, `force` requests sent before ready, and
  notifications written by the server.

**Ring entry states**

- There is no FRRS_FUSE_REQ_COMMIT state and no ent_release list.

| State | List | `ent->cmd` |
|---|---|---|
| `FRRS_INVALID` | none | NULL after allocation; set after a failed copy |
| `FRRS_AVAILABLE` | `ent_avail_queue` | set |
| `FRRS_FUSE_REQ` | `ent_w_req_queue` | set |
| `FRRS_USERSPACE` | `ent_in_userspace` | NULL |
| `FRRS_COMMIT` | `ent_commit_queue` | set, the commit command |
| `FRRS_TEARDOWN` | local list in `fuse_uring_stop_list_entries()` | as before |
| `FRRS_RELEASED` | `ent_released` | NULL |

- `ent->cmd`: cleared in `fuse_uring_send()`, under `queue->lock`, just before
  `io_uring_cmd_done()`; the entry holds the command through the whole copy.
- `FRRS_INVALID` after a failed copy: `fuse_uring_prepare_send()` unlinks the
  entry; the caller then puts it back with `fuse_uring_get_next_fuse_req()`.
- `fuse_uring_cancel()` on `FRRS_AVAILABLE`: unlinks and frees the entry; it
  does not move it to `ent_in_userspace`.
- Cancelled task work on `FRRS_FUSE_REQ`: `fuse_uring_send_in_task()` unlinks
  and frees the entry; it never reaches `FRRS_RELEASED`.
- Request in `FRRS_FUSE_REQ`: on no list and reachable only through
  `ent->fuse_req`; `req->ring_entry` is not set yet.
- `fuse_uring_add_to_pq()`: called from `fuse_uring_send()`, so the request
  enters `queue->fpq.processing` at the move to `FRRS_USERSPACE`.
- `ent->payload` and `ent->buf_id` of a pool queue: written under
  `queue->lock` by `fuse_uring_select_buffer()` and
  `fuse_uring_recycle_buffer()`, which assert it; `ent->zero_copied` is written
  without it.

**Choosing a queue**

- `fuse_uring_task_to_queue()`: only `task_cpu(current)`; no NUMA or
  neighbour fallback.
- Missing queue, foreground: `fuse_uring_queue_fuse_req()` ends the request
  with `-EINVAL`.
- Missing or stopped queue, background: `fuse_uring_queue_bq_req()` returns
  false and `fuse_chan_send_bg()` returns `-ENOTCONN`.
- `fuse_uring_flush_bg()`: asserts `queue->lock` and `fch->bg_lock`; it takes
  neither.
- `fch->blocked`: set in `fuse_uring_queue_bq_req()` when `num_background`
  reaches `max_background`.

**Commit and fetch**

- There is no fuse_uring_next_fuse_req() here;
  `fuse_uring_get_next_fuse_req()` assigns the next request and the caller
  calls `fuse_uring_send()`.
- Entry of a commit: taken from `req->ring_entry`; nothing compares it with the
  `qid` of the SQE beyond the lookup in that queue's `fpq`.
- `fuse_uring_cmd_index_ok()`: tested under `queue->lock` before the lookup;
  with a registered buffer pool the SQE must carry `IORING_URING_CMD_FIXED` and
  the pool's `buf_index`, else `-EINVAL`.
- Entry not in `FRRS_USERSPACE`: `fuse_uring_commit_fetch()` recycles the pool
  buffer, calls `zero_copy_unregister()` with the new command, ends the request
  with `-EIO` and returns `-EIO`.
- Reply header: checked in `fuse_uring_commit()` by
  `fuse_uring_out_header_has_err()`, not in `fuse_uring_copy_from_ring()`.
- `fuse_uring_out_header_has_err()`: tests `unique` and `error` only; no
  opcode test.
- Bad header or failed copy: the request ends with that error, the fetch still
  runs, and the handler returns `-EIOCBQUEUED`.
- No further request: the entry stays `FRRS_AVAILABLE` on `ent_avail_queue`
  with the command held and already marked cancelable.
- Buffer-pool queue with a request waiting and no free buffer:
  `fuse_uring_ent_assign_req()` returns NULL, same outcome as no request.

**Context of ring copies**

- `fuse_uring_send_in_task()`: signature is `(struct io_tw_req, io_tw_token_t)`;
  it gets no issue flags and uses the constant
  `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS`, which is `IO_URING_F_COMPLETE_DEFER`.
- There is no IO_URING_F_TASK_DEAD here; the callback tests `tw.cancel`, set
  from `io_should_terminate_tw()` in `io_uring/tw.h`.
- `tw.cancel` is true for an exiting task, a kernel thread and a dying ring, so
  the fallback worker never copies.
- `tw.cancel` branch: unlinks the entry, recycles its buffer, completes the
  command with `-ECANCELED`, ends the request with `-ECANCELED`, frees the
  entry and drops `ring->queue_refs`.
- There is no fuse_uring_send_next_to_ring() here; the commit path calls
  `fuse_uring_get_next_fuse_req()` then `fuse_uring_send()`.

| Path | Task | Issue flags used |
|---|---|---|
| request meets an available entry | server, task work | `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` |
| fetch after commit | server, in `fuse_uring_cmd()` | flags of that call, unchanged |
| `fuse_uring_entry_teardown()` | aborting task or worker | `IO_URING_F_UNLOCKED` |
| `fuse_uring_cancel()` | io_uring cancel | flags of that call |

- Issue flags also reach `io_buffer_register_bvec()`,
  `io_buffer_unregister()` and `io_uring_cmd_import_fixed()` through
  `fuse_uring_prepare_send()` and `fuse_uring_req_end()`.
- `io_ring_submit_lock()` in `io_uring/io_uring.h`: takes `ctx->uring_lock`
  only with `IO_URING_F_UNLOCKED`, so the flags must match the real lock state.

**Payload buffers**

- Two ways: `FUSE_PAYLOAD_PER_ENT`, each entry registers its own payload
  buffer; `FUSE_PAYLOAD_BUFPOOL`, entries borrow from `struct fuse_bufpool` of
  the queue.
- `FUSE_PAYLOAD_UNSET`: state of a new queue; left once and never changed
  again.
- `FUSE_PAYLOAD_BUFPOOL`: set by `fuse_uring_add_bufpool()` under
  `queue->lock`, only from `FUSE_PAYLOAD_UNSET`, else `-EINVAL`.
- `FUSE_PAYLOAD_PER_ENT`: set by `fuse_uring_create_ring_ent()` at the first
  REGISTER that passes its payload tests on a queue that has no pool.
- `fuse_uring_add_bufpool()`: needs an existing queue, else `-EINVAL`;
  REGISTER creates a queue implicitly, `FUSE_IO_URING_CMD_ADD_QUEUE`
  explicitly.
- Pool layout: `nr_bufs` is `bufpool.len` divided by `ring->max_payload_sz`;
  buffer `id` starts at `base_uaddr + id * buf_size`.
- Registered pool: the ADD_BUFPOOL command had `IORING_URING_CMD_FIXED`;
  `registered_index` is its `buf_index`.
- Registered pool: `fuse_uring_import_payload()` uses
  `io_uring_cmd_import_fixed()` with `ent->cmd`, else `import_ubuf()`.
- REGISTER on a pool queue: the payload iovec must have NULL base and zero
  length, else `-EINVAL`; only the header iovec is used.
- Buffer taken: `fuse_uring_select_buffer()`, under `queue->lock`, when a
  request is assigned to the entry.
- Callers of `fuse_uring_select_buffer()`: `fuse_uring_prep_buffer()` on the
  send paths, `fuse_uring_next_req_update_buffer()` on the fetch path.
- Buffer taken only if `fuse_uring_req_has_copyable_payload()` is true; an
  entry without a buffer has `ent->payload.iov_base` NULL.
- No free buffer: `-ENOBUFS`; the request stays on `fuse_req_queue` and the
  entry stays available.
- Buffer kept: from assignment through `FRRS_USERSPACE` and the reply copy, and
  reused if the next request has a payload.
- Buffer given back: `fuse_uring_recycle_buffer()`, under `queue->lock`, when
  the fetch finds no request, when the next request has no payload, on the
  `-EIO` commit path and in cancelled task work.
- `fuse_uring_args_to_ring()`: tells the server the buffer through `offset` in
  `struct fuse_uring_ent_in_out`.

**Payloads without a copy**

- The path exists: the folios of a request are registered as an io_uring
  buffer of the server, at index `ent->zero_copy_index`.
- Queue: `queue->zero_copy` is set only by `FUSE_IO_URING_CMD_ADD_QUEUE` with
  `FUSE_URING_ZERO_COPY`, which needs `CAP_SYS_ADMIN`, else `-EPERM`.
- Queue: a zero-copy queue must use a buffer pool; REGISTER without one gets
  `-EINVAL` from `fuse_uring_create_ring_ent()`.
- `ent->zero_copy_index`: read from `ent_zero_copy_buf_index` at REGISTER;
  non-zero on a queue without zero copy gives `-EINVAL`.
- Request: `can_zero_copy_req()` needs `queue->zero_copy`, `args->zero_copy`,
  opcode `FUSE_READ` or `FUSE_WRITE`, and `in_pages` or `out_pages`.
- `args->zero_copy`: set in `fuse_read_args_fill()` and
  `fuse_write_args_fill()` from `FOPEN_IO_URING_ZERO_COPY` of the open file.
- `fuse_uring_set_up_zero_copy()`: takes one `folio_get()` per folio and calls
  `io_buffer_register_bvec()`; on failure the request ends with that error.
- Copy state: `skip_folio_copy` makes `fuse_copy_args()` skip the folio data;
  other arguments are still copied to the payload buffer.
- Zero-copied write: `payload_sz` sent to the server still includes the size
  of the page argument.
- Server notice: `FUSE_URING_ENT_ZERO_COPY` in `flags` of
  `struct fuse_uring_ent_in_out`.
- Unregister: `zero_copy_unregister()` calls `io_buffer_unregister()` from
  `fuse_uring_req_end()`, after `queue->lock` is dropped and before
  `fuse_request_end()`.
- Folio release: `fuse_zero_copy_release()` drops the extra references when
  io_uring drops the last reference on the buffer node (`io_free_rsrc_node()`,
  `io_buffer_unmap()`).
- `fs/fuse/dev_uring.c` drops only the references it took, in
  `fuse_zero_copy_release()`; the request's own folio references are not
  touched.

**Ring lock order**

- Order, outer to inner: `fi->lock`, `queue->lock`, `fch->bg_lock`.
- `fi->lock` outside `queue->lock`: `fuse_send_writepage()` runs under
  `fi->lock` and reaches `fuse_uring_queue_bq_req()` through
  `fuse_simple_background()`.
- `fch->lock`: outer to `fch->bg_lock` in `fuse_chan_abort()`; no function in
  `fs/fuse/dev_uring.c` takes it or `queue->lock` while it has taken the other.
- `fuse_uring_do_register()`: drops `fch->lock` before
  `fuse_uring_prepare_cancel()` and before it takes `queue->lock`.
- `fuse_chan_abort()` and `fuse_check_timeout()`: drop `fch->lock` before
  `fuse_uring_abort()` and `fuse_uring_request_expired()`.
- `fuse_request_end()` called from `fuse_uring_req_end()`: takes no
  `fch->bg_lock`, because `FR_BACKGROUND` is already clear.
- `fuse_request_end()` from `fuse_dev_end_requests()` or
  `fuse_uring_stop_fuse_req_end()`: still takes `fch->bg_lock` for a request
  with `FR_BACKGROUND` set.
- `ctx->uring_lock`, a mutex: `io_uring_cmd_mark_cancelable()`,
  `io_buffer_unregister()` and `io_uring_cmd_done()` may take it, so they run
  after `queue->lock` is dropped.
- `queue->stopped`: written under `queue->lock` in
  `fuse_uring_abort_end_requests()`.

**Publishing ring pointers**

| Object | Store | Loads |
|---|---|---|
| `fch->ring` | `smp_store_release()` under `fch->lock` | `smp_load_acquire()` in the three setup handlers; `READ_ONCE()` in `fuse_uring_ready()`; plain elsewhere |
| `ring->queues[qid]` | `smp_store_release()` under `fch->lock` | `smp_load_acquire()` in `fuse_uring_add_bufpool()`; plain in `fuse_uring_create_queue()`; `READ_ONCE()` elsewhere |
| `ring->ready` | `smp_store_release()` after `WRITE_ONCE()` of `fiq->ops` | `smp_load_acquire()` in `fuse_uring_ready()` |

- `fuse_uring_create()`: has no test for an existing ring; it runs once, from
  `fuse_uring_conn_init()`, before `fch->initialized` is stored with release.
- `fuse_uring_create_queue()` when the slot is taken: frees its queue; returns
  the existing one for REGISTER and `-EEXIST` for
  `FUSE_IO_URING_CMD_ADD_QUEUE`.
- Lifetime: pointers stay until `fuse_uring_destruct()`, which
  `delayed_release()` runs after the last `fuse_conn_put()`; a reader needs
  the `struct fuse_conn` behind `fch->conn` kept alive for the whole use.
- **Unsafe usage**: using `ring->queues[qid]` without a NULL test.
  - Safe: test `qid < ring->nr_queues`, load once, test for NULL, as
    `fuse_uring_commit_fetch()` does; a slot stays NULL until its queue is
    created.
  - Safe: after `fuse_uring_ready()`, `fuse_uring_task_to_queue()` still tests
    and its callers handle NULL.
- **Potentially unsafe usage**: plain load of `fch->ring`.
  - Unsafe: when nothing orders the load after `fuse_uring_create()`; the
    reader may see the pointer before `nr_queues` and `queues`.
  - Safe: after `smp_load_acquire()` of `fch->initialized`, as
    `fuse_uring_commit_fetch()` is reached through `fuse_uring_cmd()`.
  - Safe: after taking and dropping `fch->lock` with `connected` cleared, as
    `fuse_uring_abort()` is reached from `fuse_chan_abort()`;
    `fuse_uring_create()` tests `connected` under that lock.
- **Potentially unsafe usage**: touching the lists or `stopped` of a queue
  without `queue->lock`.
  - Unsafe: while a command, a request or teardown can still reach the queue;
    every list move runs under `queue->lock`, see the assert in
    `fuse_uring_add_req_to_ring_ent()`.
  - Safe: take `queue->lock` first, then test `queue->stopped`, as
    `fuse_uring_queue_fuse_req()` does.
  - Safe: in `fuse_uring_destruct()`, which runs from `delayed_release()`
    after the last `fuse_conn_put()`; each installed device and a pending
    `async_teardown_work` hold a connection reference.

**Reading the submission entry**

- `io_uring_sqe128_cmd()`: macro in `include/linux/io_uring/cmd.h`; returns
  `sqe->cmd` cast to the type, with a `BUILD_BUG_ON()` against the command area
  of a 128-byte SQE.
- Every read of the command area in `fs/fuse/dev_uring.c` goes through
  `io_uring_sqe128_cmd()`; none uses `io_uring_sqe_cmd()`.
- `io_uring_cmd_prep()`: stores the pointer into the submission ring
  (`ioucmd->sqe = sqe`); it copies only `cmd_op`, `uring_cmd_flags` and, with
  `IORING_URING_CMD_FIXED`, `buf_index`.
- `io_uring_cmd_sqe_copy()` in `io_uring/uring_cmd.c`: copies the entry and
  repoints `ioucmd->sqe`; called through `io_req_sqe_copy()` in
  `io_uring/io_uring.c` on `-EAGAIN`, on the fallback path and for links.
- Inline issue that returns `-EIOCBQUEUED`: no copy is made, `cmd->sqe` keeps
  pointing at the ring slot.
- `io_req_uring_cleanup()`: can set `ioucmd->sqe` to NULL at completion; not
  with `IO_URING_F_UNLOCKED`.
- **Unsafe usage**: reading `cmd->sqe` after the issue call returned, from task
  work, cancel or teardown.
  - Safe: read inside the call chain of `fuse_uring_cmd()`, as
    `fuse_uring_cmd_index_ok()` does; store what is needed later in
    `struct fuse_ring_ent`.
  - Safe: `cmd->cmd_op` and `cmd->flags` at any time; `io_uring_cmd_prep()`
    copied them.
  - Safe: `io_uring_cmd_import_fixed()` in task work; it uses `req->buf_index`
    copied at prep.
- **Unsafe usage**: reading one SQE field twice, to check and then to use.
  - Safe: one `READ_ONCE()` into a local, as `fuse_uring_commit_fetch()` does;
    `io_get_sqe()` hands out `ctx->sq_sqes`, shared with userspace.
- **Unsafe usage**: reading through the pointer from `io_uring_sqe128_cmd()`
  when `IO_URING_F_SQE128` was not tested.
  - Safe: after the test in `fuse_uring_cmd()`; `struct fuse_uring_cmd_req` is
    larger than the command area of a 64-byte entry.
  - Safe: the cancel call runs before that test and reads only the pdu.

**Ring teardown**

- `fuse_uring_cancel()` on `FRRS_AVAILABLE`: unlinks the entry and clears
  `ent->cmd` under `queue->lock`, then completes the command with `-ENOTCONN`.
- `fuse_uring_cancel()` then frees the entry and drops `ring->queue_refs`,
  waking `stop_waitq` at 0; in any other state it does nothing.
- `ring->queue_refs`: incremented per entry in `fuse_uring_create_ring_ent()`.
- `ring->queue_refs` is decremented in `fuse_uring_stop_list_entries()`,
  `fuse_uring_cancel()`, the cancel branch of `fuse_uring_send_in_task()` and
  the abort branch of `fuse_uring_do_register()`.
- `fuse_uring_teardown_entries()`: takes entries from `ent_in_userspace` and
  `ent_avail_queue` only.
- Count above 0 after a pass: the entries left are in another state, for
  example on `ent_w_req_queue` or `ent_commit_queue`, or off-list after a
  failed copy; a later pass picks them up.
- `fuse_uring_stop_queues()`: does not wait for `ring->queue_refs`; with
  entries left it takes `fuse_conn_get()` and schedules
  `async_teardown_work`.
- `fuse_uring_async_stop_queues()`: at count 0 wakes `stop_waitq` and calls
  `fuse_conn_put()`.
- `fuse_uring_wait_stopped_queues()`: the sleeper; called from
  `fuse_chan_wait_aborted()`, which `fuse_conn_destroy()` calls.
- `fuse_uring_destruct()` also frees `queue->bufpool`.
- **Potentially unsafe usage**: `kfree()` of a ring entry outside
  `fuse_uring_destruct()`.
  - Unsafe: where a command whose pdu points at the entry can still be on the
    cancelable list, as in teardown; `fuse_uring_cancel()` reads `ent->queue`
    before it takes any lock.
  - Safe: in `fuse_uring_cancel()`, after `io_uring_cmd_done()` took the
    command off that list; the cancel runs under `ctx->uring_lock`
    (`io_uring_try_cancel_uring_cmd()` asserts it).
  - Safe: in the cancel branch of `fuse_uring_send_in_task()`, after
    `io_uring_cmd_done()`; task work runs under `ctx->uring_lock`.
  - Safe: in `fuse_uring_do_register()` when `fch->connected` is 0, before
    `fuse_uring_prepare_cancel()` has set the pdu.
  - Safe: park the entry on `ent_released` with `FRRS_RELEASED`, as
    `fuse_uring_entry_teardown()` does.
- **Unsafe usage**: calling `io_uring_cmd_mark_cancelable()` on a command
  whose pdu does not hold the entry.
  - Safe: `fuse_uring_prepare_cancel()` stores the entry in the pdu and then
    marks the command, as `fuse_uring_do_register()` and
    `fuse_uring_commit_fetch()` use it for each new command;
    `uring_cmd_to_ring_ent()` in the cancel trusts the pdu.
- **Unsafe usage**: freeing an entry outside destruct without dropping
  `ring->queue_refs`.
  - Safe: `atomic_dec_and_test()` and wake `stop_waitq`, as
    `fuse_uring_cancel()` does; `fuse_uring_wait_stopped_queues()` waits for 0.

## Inodes and lookup counts

**Inode identity**

- Hash key: the node id alone, as both hash value and compare argument of
  `iget5_locked()` in `fuse_iget()`. `inode->i_ino` is not the key; it is
  `fuse_squash_ino(attr->ino)`, set in `fuse_change_attributes_common()`.
- Submount points (`fc->auto_submounts`, `FUSE_ATTR_SUBMOUNT`, `S_ISDIR()`):
  `fuse_iget()` makes them with `new_inode()` and never hashes them, so each
  call returns a new inode.
- `fuse_stale_inode()` in `fs/fuse/fuse_i.h`: a pure test, changes nothing.
- `fuse_make_bad()`: only sets `FUSE_I_BAD`. It does not call
  `remove_inode_hash()`; `fuse_iget()` does that itself, for a stale inode
  that is not the root.
- `FUSE_I_BAD` is never cleared.
- Inode marked bad outside `fuse_iget()` (`fuse_do_getattr()`,
  `fuse_do_setattr()`, `fuse_do_statx()`, `fuse_direntplus_link()`): stays
  hashed.
- `fuse_iget()` and `fuse_inode_eq()` do not test `fuse_is_bad()`: a hashed bad
  inode whose generation and type match the reply is returned again, with
  `nlookup` raised and attributes updated.
- Stale root: marked bad, kept in the hash, and `fuse_iget()` goes on to raise
  `nlookup` and update it.
- `fuse_lookup_name()` sets a nonzero generation to 0 for `FUSE_ROOT_ID`
  before `fuse_iget()`; a wrong type in the reply still marks the root bad.
- `fuse_dentry_revalidate()` does not call `fuse_make_bad()`; a stale or
  invalid reply only makes it return 0.
- Error for a bad inode: `-EIO` at every `fuse_is_bad()` test that returns an
  error. Within `fs/fuse`, `-ESTALE` is set only in the export paths
  `fuse_get_dentry()` and `fuse_get_parent()`, which do not test
  `fuse_is_bad()`.

**Locks of an inode**

- `fuse_lock_inode()` callers: only `fuse_lookup()` and
  `fuse_readdir_uncached()`.
- LOOKUP sent without `fi->mutex`: from `fuse_dentry_revalidate()`,
  `fuse_get_dentry()` and `fuse_get_parent()`. So without
  `fc->parallel_dirops` the server can still see parallel LOOKUPs in one
  directory.
- `fi->mutex`: no user other than `fuse_lock_inode()` and
  `fuse_unlock_inode()`; it guards no DAX or readdir-cache state.
- `fi->inval_mask`: not protected by `fi->lock`. Writers use
  `set_mask_bits()` (`fuse_invalidate_attr_mask()` holds no lock), readers use
  `READ_ONCE()`.
- `fi->state`: atomic bit operations, no lock needed.
  `FUSE_I_CACHE_IO_MODE` is changed only under `fi->lock`, which also guards
  `fi->iocachectr`, in `fs/fuse/iomode.c`.
- `struct fuse_inode` has no list or rbtree of in-flight writepages; the
  write state under `fi->lock` is `write_files`, `queued_writes`, `writectr`
  and `iocachectr`.
- `fi->rdc`, with `fi->rdc.lock`, shares a union with those write fields.
  `fi->rdc.lock` is initialised only in `fuse_init_dir()`, so it exists only
  on directories, and the write fields only on regular files.
- `fi->dax->sem`: an rw_semaphore in `struct fuse_inode_dax`, defined in
  `fs/fuse/dax.c`; `fi->dax` exists only under `CONFIG_FUSE_DAX` and is NULL
  unless `fc->dax` is set.

**Entries with attributes**

- `fuse_use_readdirplus()` in auto mode (`fc->readdirplus_auto`): true when
  `FUSE_I_ADVISE_RDPLUS` was set (test-and-clear, so one advice buys one
  request) and also true whenever `ctx->pos == 0`.
- `fc->do_readdirplus`: set only from the INIT reply. No error from
  `FUSE_READDIRPLUS` clears it; there is no fallback to `FUSE_READDIR`.
- `fuse_advise_use_readdirplus()` callers: `fuse_lookup()` on a positive
  result, and `fuse_dentry_revalidate()` only when the dentry has not expired
  and `FUSE_I_INIT_RDPLUS` was set on the child. Getattr never calls it.
- Existing dentry with the same node id, not stale, not bad:
  `fuse_direntplus_link()` does `fi->nlookup++` under `fi->lock` itself and
  calls `fuse_change_attributes()`; it does not call `fuse_iget()`.
- Existing dentry that is negative, has another node id, or is stale:
  `fuse_make_bad()` if stale, then `d_invalidate()` and a retry through
  `d_alloc_parallel()`.
- Existing dentry with the same node id, not stale, whose inode is bad:
  `-EIO`.
- `fuse_iget()` is reached only for a dentry that is `d_in_lookup()`.
- `d_splice_alias()` failure after `fuse_iget()`: `fuse_direntplus_link()`
  does `fi->nlookup--` before it returns the error, because the caller sends a
  FORGET for the same reply.
- `parse_dirplusfile()`: any nonzero return of `fuse_direntplus_link()`
  (`-EIO`, `-ENOMEM`, a `d_alloc_parallel()` error) leads to
  `fuse_force_forget()` for that node id. The error is then dropped; readdir
  itself still succeeds.
- Name with zero length, longer than `FUSE_NAME_MAX`, or containing `/`:
  `parse_dirplusfile()` returns `-EIO` at once. That entry and all entries
  after it get neither `nlookup` nor a FORGET.

**Checks on replies**

- `fuse_invalid_attr()`: tests only the file type (`fuse_valid_type()`) and
  `attr->size <= LLONG_MAX` (`fuse_valid_size()`, static in `fs/fuse/dir.c`).
  `nlink`, `blksize`, `uid`, `gid` and `rdev` are not checked.
- `fuse_lookup_name()`: does not call `invalid_nodeid()`. Zero means a
  negative entry; `FUSE_ROOT_ID` is accepted because the export paths look up
  `.` and `..`.
- `fuse_lookup()`: rejects a result with `FUSE_ROOT_ID` with `-EIO` only after
  `fuse_iget()` has run, then calls `iput()`.
- `create_new_entry()`: also requires the type in the reply to equal the
  requested type. For `FUSE_LINK` the requested type is `i_mode` of the
  existing inode.
- `fuse_create_open()`: requires `S_ISREG()` on the reply mode.
- `fuse_do_setattr()`: same checks as `fuse_do_getattr()`,
  `fuse_invalid_attr()` and `inode_wrong_type()`, then `fuse_make_bad()` and
  `-EIO`.
- `fuse_do_statx()`: does not call `fuse_invalid_attr()`. It checks size only
  if `STATX_SIZE` is in `sx->mask` and type only if `STATX_TYPE` is.
- `fuse_change_attributes_common()`: keeps `inode->i_mode & S_IFMT` and takes
  only the low 07777 bits from the reply, so an update cannot change the type
  of a live inode.
- **Unsafe usage**: passing `attr` from a reply to `fuse_iget()` before
  `fuse_invalid_attr()` has passed.
  - Unsafe: for a new inode `fuse_init_inode()` reaches `BUG()` when
    `attr->mode` is none of the seven types; `inode->i_size` is set from
    an unchecked `attr->size`.
  - Safe: `fuse_invalid_attr()` first, as `fuse_lookup_name()`,
    `create_new_entry()`, `fuse_create_open()` and `fuse_direntplus_link()`
    do.
  - Safe: `attr` not taken from a reply, as in `fuse_fill_super_submount()`,
    which builds it from a live inode with `fuse_fill_attr_from_inode()`.
- **Unsafe usage**: passing `attr` from a reply to `fuse_change_attributes()`
  before the size and the type against the inode were checked.
  - Unsafe: `fuse_change_attributes_i()` does `i_size_write()` with
    `attr->size`, which is negative as `loff_t` above `LLONG_MAX`.
  - Safe: `fuse_invalid_attr()` plus `inode_wrong_type()`, as
    `fuse_do_getattr()` does, or plus `fuse_stale_inode()`, as
    `fuse_dentry_revalidate()` and `fuse_direntplus_link()` do.
  - Safe: `fuse_valid_size()`, `fuse_valid_type()` and `inode_wrong_type()`
    under the `sx->mask` tests, as `fuse_do_statx()` does; it updates only
    when `sx->mask` has all of `STATX_BASIC_STATS`, which includes
    `STATX_SIZE` and `STATX_TYPE`.

**FORGET and lookup counts**

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

## Attributes

**Attribute versions**

- Staleness test: in `fuse_change_attributes_i()` (static, `fs/fuse/inode.c`),
  under `fi->lock`, not `fc->lock`.
- `fuse_get_attr_version()` and `fuse_get_evict_ctr()`: plain `atomic64_read()`,
  no lock.
- `fuse_change_attributes()`: has no `evict_ctr` parameter and passes 0; a
  non-zero `evict_ctr` reaches `fuse_change_attributes_common()` only through
  `fuse_iget()`.
- `evict_ctr` never drops a reply: attributes and `fi->i_time` are still
  applied.
- `evict_ctr` effect, in `fuse_change_attributes_common()`: `STATX_BASIC_STATS`
  stays set in `fi->inval_mask` when `evict_ctr` is non-zero,
  `fi->attr_version` is 0 and the counter has moved.
- `fuse_evict_inode()`: increments `fc->evict_ctr` only when the superblock has
  `SB_ACTIVE` and `inode->i_nlink > 0`.
- `fuse_dentry_revalidate()`: reads `attr_version` only, not `evict_ctr`.
- `create_new_entry()` and `fuse_create_open()`: pass 0, 0 to `fuse_iget()`, so
  the reply is applied with no version test.
- `FUSE_LINK` goes through `create_new_entry()` on an inode that already
  exists; `fuse_link()` itself changes neither nlink nor `fi->attr_version`.
- `fuse_do_setattr()`: samples `attr_version` before sending; if
  `fi->attr_version` is newer on reply it still applies the attributes, with a
  zero timeout.
- `fuse_do_setattr()` calls `fuse_change_attributes_common()` directly and does
  not test `FUSE_I_SIZE_UNSTABLE`.
- `fuse_update_ctime()` and `fuse_link_write_file()`: do not bump
  `fi->attr_version`; there is no fuse_write_update_size() in this tree.
- `fuse_write_update_attr()`: bumps on every call, also when nothing was
  written or the size did not grow.
- Bump sites: search `fs/fuse` for `atomic64_inc_return(&fc->attr_version)`;
  easy to miss are `fuse_aio_complete()`, `fuse_read_update_size()` and
  `fuse_truncate_update_attr()`.
- `FUSE_I_SIZE_UNSTABLE`: not set by `fuse_open()` with `O_TRUNC`, nor by
  `fuse_direct_io()`; `fuse_perform_write()` sets it only for an extending
  write.

**Attribute cache validity**

- `fi->i_time`: written only by `fuse_change_attributes_common()`; no
  invalidation helper touches it, staleness is marked in `fi->inval_mask` only.
- `fuse_invalidate_attr_mask()`: uses `set_mask_bits()`, not `atomic_or()`.
- Applying a reply: clears `STATX_BASIC_STATS` from `fi->inval_mask` (except
  when the `evict_ctr` test in `fuse_change_attributes_common()` fails), and
  `STATX_BTIME` only for a statx reply; other bits stay set.
- Refresh test in `fuse_update_get_attr()`:
  `request_mask & inval_mask & ~cache_mask`.
- Writeback cache, regular file: an invalid size, mtime or ctime bit alone
  never sends a request; expiry of `fi->i_time` still does.
- `fuse_get_cache_mask()`: 0 for anything that is not `S_ISREG()`, also with
  `fc->writeback_cache`.
- `fuse_do_setattr()` on a regular file under writeback cache: mtime and ctime
  come from the `struct iattr`, not the reply; size comes from the reply only
  for a truncate.
- `fuse_do_statx()`: applies the reply to the cache only if `sx->mask` holds
  all of `STATX_BASIC_STATS`.
- Page cache in `fuse_change_attributes_i()`: a size change truncates without
  `fc->auto_inval_data`; an mtime change invalidates only with it; both only
  when the cache mask is 0.

**Extended attributes and ACLs**

- `__fuse_get_acl()`: `-EOPNOTSUPP` becomes NULL only when `fc->no_getxattr` is
  set; otherwise it is returned as an error.
- `fuse_get_acl()` without `fc->posix_acl`: still asks the server, unless
  `fuse_no_acl()` is true; then it returns `-EOPNOTSUPP` without a request.
- `fuse_set_acl()`: stores nothing in the ACL cache and does not edit `i_mode`.
- `fuse_set_acl()` with `fc->posix_acl`: calls `forget_all_cached_acls()` and
  `fuse_invalidate_attr()` whatever the request returned, also on error.
- `fuse_setxattr()` and `fuse_removexattr()`: on success call only
  `fuse_update_ctime()`; the comment in `fuse_set_acl()` claims more.
- Without `fc->posix_acl`, a successful ACL set marks only `STATX_CTIME` stale;
  the cached mode stays valid.
- `FUSE_SETXATTR_ACL_KILL_SGID`: added only with `fc->posix_acl`.
- `SB_POSIXACL`: set by `fuse_fill_super_common()` on the superblock it fills,
  whatever `fc->posix_acl` is.
- Umask on create: skipped by `fc->dont_mask`, not by `fc->posix_acl`.

**Clearing setuid and setgid**

- `fc->handle_killpriv` (v1): `fuse_setattr()` treats it like v2, so chown is
  left to the server as well as write and truncate; `FATTR_KILL_SUIDGID` and
  `FUSE_OPEN_KILL_SUIDGID` are not sent.
- `fuse_cache_write_iter()`: calls `kiocb_modified()` in every mode, so
  `file_remove_privs_flags()` in `fs/inode.c` still runs under v1 and v2.
- `fuse_direct_write_iter()`: calls neither `kiocb_modified()` nor
  `file_remove_privs()`.
- `fuse_direct_io()`: sets `FUSE_WRITE_KILL_SUIDGID` on `!capable(CAP_FSETID)`
  without testing `fc->handle_killpriv_v2`; `fuse_send_write_pages()` tests
  both.
- Writeback requests: carry `FUSE_WRITE_CACHE` only, never
  `FUSE_WRITE_KILL_SUIDGID`.
- `fuse_send_open()`: tests `O_TRUNC` after stripping it when
  `fc->atomic_o_trunc` is clear, so `FUSE_OPEN_KILL_SUIDGID` needs that flag
  too.
- Without `fc->atomic_o_trunc` the truncate of an `O_TRUNC` open arrives as
  `FUSE_SETATTR`, with `FATTR_KILL_SUIDGID` when `fc->handle_killpriv_v2` is
  set and the caller lacks `CAP_FSETID`.
- `fuse_create_open()`: sets `FUSE_OPEN_KILL_SUIDGID` only when also
  `!(flags & O_EXCL)`; that test does not include `fc->atomic_o_trunc`.
- Chown under v2: `fuse_do_setattr()` sets `FATTR_KILL_SUIDGID` for every
  non-directory, with no `CAP_FSETID` test; truncate tests `CAP_FSETID`.
- `setattr_should_drop_suidgid()`: used in `fs/fuse` only by
  `fuse_cache_write_iter()`, not by `fuse_setattr()`; there is no
  fuse_open_common() here.
- `fuse_setattr()` early return on empty `ia_valid`: not reached from write or
  truncate, because `__remove_privs()` adds `ATTR_FORCE` and `do_truncate()`
  sets `ATTR_SIZE`.
- Write under v1 or v2, when `file_remove_privs_flags()` finds bits to kill: a
  `FUSE_SETATTR` without mode goes out before the write, and the mode in its
  reply becomes the cached mode.
- After a write or `O_TRUNC` open: only `FUSE_STATX_MODSIZE` is invalidated;
  nothing in `fs/fuse` invalidates `STATX_MODE` alone, and `i_mode` is not
  edited.
- `security.capability`: when the VFS passes `ATTR_KILL_PRIV`,
  `setattr_prepare()` in `fuse_do_setattr()` removes it through
  `fuse_removexattr()`, whatever the killpriv flags.

## Dentries and directories

**Dentry validity**

- `struct fuse_dentry` in `fs/fuse/dir.c`: holds both `time` and `epoch`
  (`u64`); the epoch is not in `dentry->d_time`, which nothing under
  `fs/fuse/` uses.
- Stale epoch (`fd->epoch < fc->epoch`) or bad inode: `fuse_dentry_revalidate()`
  returns 0 with no LOOKUP sent, in RCU walk too.
- Negative dentry that is expired or hit by a forcing flag: returns 0, never
  sends a LOOKUP; a negative dentry still inside its timeout returns 1.
- Forcing flags: `LOOKUP_EXCL`, `LOOKUP_REVAL` and `LOOKUP_RENAME_TARGET`
  each force the LOOKUP path on an unexpired dentry.
- The LOOKUP in revalidation: built with `fuse_lookup_init()` and sent with
  `fuse_simple_request()`; `fuse_lookup_name()` is not used here.
- Parent: taken from the `dir` and `name` arguments; revalidation does not
  call `dget_parent()`.
- Unexpired positive dentry in RCU walk: returns `-ECHILD` when
  `FUSE_I_INIT_RDPLUS` is set on the inode, 1 otherwise.
- Request errors: `-ENOMEM` (also from `fuse_alloc_forget()`) and `-EINTR`
  are returned as errors; any other error returns 0.
- Successful revalidation: resets `time`; `epoch` is not refreshed.
- `fuse_dentry_delete()`: reached at final `dput()` only while
  `DCACHE_OP_DELETE` is set; `fuse_dentry_settime()` clears the flag unless
  the time is 0 and `fc->delete_stale` is set.
- `fc->delete_stale`: set only in `fs/fuse/virtio_fs.c`; elsewhere an expired
  unused dentry stays cached after `dput()` unless `fuse_dentry_tree_work()`
  flagged it.

**Epoch and expired dentries**

- `fuse_notify_inc_epoch()` is in `fs/fuse/notify.c`; besides `atomic_inc()`
  it calls `schedule_work(&fc->epoch_work)` when `inval_wq` is non-zero.
- `fuse_epoch_work()`: calls `shrink_dcache_sb()` on the superblock found by
  looking up `FUSE_ROOT_ID`; that kills every unused dentry on the LRU, not
  only those with an old epoch.
- With `inval_wq` at 0: an epoch bump removes nothing; dentries fail at their
  next revalidation.
- Two things compare with `fc->epoch`: dentries (`fd->epoch <`, in
  `fuse_dentry_revalidate()`) and the readdir cache (`fi->rdc.epoch !=`, in
  `fuse_readdir_cached()`); inodes and attributes do not.
- Initial values: `fc->epoch` starts at 1, `fuse_dentry_init()` sets the
  dentry epoch to 0, so a dentry whose epoch is not set again after
  `fuse_dentry_init()` fails every revalidation.
- `fuse_dentry_set_epoch()`: a call separate from setting the timeout;
  `fuse_lookup()`, `fuse_create_open()` and `create_new_entry()` pass a value
  read from `fc->epoch` before the request is sent.
- Background removal of expired dentries: happens only while module parameter
  `inval_wq` (seconds, in `fs/fuse/dir.c`) is non-zero; the default is 0.
- `inval_wq` accepted values: 0, or `FUSE_DENTRY_INVAL_FREQ_MIN` (5) up to
  `USHRT_MAX`.
- `fuse_dentry_tree_add_node()`: returns at once when `inval_wq` is 0, so a
  dentry whose time was set while the parameter was 0 is not in the tree
  until its time is set again.
- `fuse_dentry_tree_work()`: does not call `d_invalidate()` or `d_drop()`; it
  sets `DCACHE_OP_DELETE`, calls `__move_to_shrink_list()` under `d_lock`,
  then `shrink_dentry_list()`. There is no d_dispose_if_unused() in this tree.
- Expired dentry that is still referenced: stays hashed and is only taken out
  of the tree; the `DCACHE_OP_DELETE` flag makes its final `dput()` drop it
  through `fuse_dentry_delete()`.
- Bucket lock in `fuse_dentry_tree_work()`: held across the whole bucket walk,
  including the `d_lock` section; released only at `need_resched()`.
- The tree: one static array `dentry_hash` shared by all connections, hashed
  by dentry pointer.

**Invalidation from the server**

- `fuse_reverse_inval_inode()`: returns only `-ENOENT` or 0; the result of
  `invalidate_inode_pages2_range()` is ignored.
- `fuse_reverse_inval_inode()`: also raises `fi->attr_version` and calls
  `forget_all_cached_acls()`.
- `fuse_invalidate_entry_cache()`: sets the dentry time to 0 through
  `fuse_dentry_settime()`; it does not unhash. The unhash is the
  `d_invalidate()` call in `fuse_reverse_inval_entry()`, skipped with
  `FUSE_EXPIRE_ONLY`.
- Expire-only flag: named `FUSE_EXPIRE_ONLY`; there is no
  FUSE_NOTIFY_EXPIRE_ENTRY in this tree.
- Unknown bits in `flags` of the entry notification: ignored, not rejected.
- `FUSE_NOTIFY_DELETE`: always passes flags 0, so it always calls
  `d_invalidate()`.
- `fuse_reverse_inval_entry()` errors before touching the dentry: `-ENOENT`
  (parent inode not cached, parent has no alias, or name not in the dcache)
  and `-ENOTDIR` (parent is not a directory).
- Entry and delete handlers: also return `-ENOMEM` from the name buffer
  allocation; `-ENAMETOOLONG` is tested after the minimum size test and
  before the exact size test.
- Delete errors `-ENOENT` (child nodeid mismatch), `-EBUSY` (mountpoint) and
  `-ENOTEMPTY`: returned after `fuse_dir_changed()`, `d_invalidate()` and the
  expiry have already been applied.
- Delete with child nodeid 0 or a negative dentry: behaves as invalidate entry
  and returns 0.
- `fuse_notify_prune()`: returns `-ENOMEM`, `-EINVAL` (size below the header,
  or size against count) or the error from `fuse_copy_one()`; the allocation
  comes first, before the size tests.

**Readdir cache**

- `FOPEN_CACHE_DIR` without a server reply: `fuse_file_open()` in
  `fs/fuse/file.c` defaults a directory to
  `FOPEN_KEEP_CACHE | FOPEN_CACHE_DIR` when `fc->no_opendir` is set or
  `FUSE_OPENDIR` returns `-ENOSYS`.
- `FOPEN_KEEP_CACHE` on a directory: only decides whether `fuse_dir_open()`
  calls `invalidate_inode_pages2()`; the mtime, iversion and epoch tests do
  not look at it.
- `fi->rdc.epoch`: a third key beside `mtime` and `iversion`; recorded when
  caching starts and compared with `fc->epoch`.
- Validity test in `fuse_readdir_cached()`: runs only when `ctx->pos` is 0; a
  reader in mid-stream does not test for a directory change.
- mtime refresh at position 0: `fuse_update_attributes()` is called only with
  `fc->auto_inval_data`.
- `fuse_rdc_reset()`: static in `fs/fuse/readdir.c`, called only from
  `fuse_readdir_cached()`; it resets the `rdc` fields and removes no pages.
- `fuse_dir_changed()`: does not touch `rdc`; it bumps the iversion, which the
  next reader at position 0 compares.
- `FUSE_NOTIFY_INVAL_INODE` on a directory with offset >= 0: drops the cached
  pages of the given range, so the next cached read of one of them hits the
  missing-page reset.
- Version mismatch between `ff->readdir.version` and `fi->rdc.version`: the
  stream restarts at the start of the cache and scans for `ctx->pos`; it does
  not by itself switch to an uncached read.
- `ff->readdir`: holds `pos`, `cache_off` and `version` only; it has no lock
  member in this tree.

## Open files

**Open file life cycle**

- Synchronous RELEASE at close: `fuse_file_release()` passes
  `fc->auto_submounts` to `fuse_file_put()`; only `fs/fuse/virtio_fs.c` sets
  that field.
- `fc->destroy`: not read on the release path; a fuseblk close sends RELEASE
  in the background.
- `fuse_sync_release()`: always synchronous; used on the error paths of
  `fuse_open()` and `fuse_create_open()`, and for every close of a CUSE file
  in `cuse_release()`.
- Inode pin: `fuse_prepare_release()` does the `igrab()` into `ra->inode`,
  when its own `sync` argument is false.
- The `sync` of `fuse_prepare_release()` and the `sync` of `fuse_file_put()`
  are separate: a virtiofs close pins the inode and still sends
  synchronously.
- `fuse_release_end()`: only `iput(ra->inode)` and `kfree(ra)`; there is no
  fuse_mount_put() in this tree.
- `ff->args`: NULL only for a directory on a server with `fc->no_opendir`;
  `fuse_file_open()` allocates it for every regular file, also with
  `fc->no_open`.
- `fc->no_open`: `fuse_file_put()` sends no RELEASE but still calls
  `fuse_release_end()`, so the inode stays pinned until the last reference
  drops.
- `fuse_file_get()`: three callers, `fuse_send_readpages()` (async only),
  `__fuse_write_file_get()` and `fuse_iomap_writeback_range()`; direct I/O,
  sync or async, takes no `struct fuse_file` reference.
- Writeback: each `struct fuse_writepage_args` gets its own reference in
  `fuse_iomap_writeback_range()`; the one from `fuse_write_file_get()`
  belongs to the walk and is dropped in `fuse_iomap_writeback_submit()`.
- `fuse_file_io_release()`: called from `fuse_file_put()` on the last
  reference and only when `ra->inode` is set, not from
  `fuse_file_release()`; the I/O mode count outlives `->release` while
  requests are in flight.
- `fuse_sync_release()` path: `ra->inode` is NULL, so
  `fuse_file_io_release()` is not called.
- `fuse_prepare_release()` does not fill `release_flags`, `lock_owner` or
  `args->end`; `fuse_file_release()` fills the first two when `ff->flock` is
  set, `fuse_file_put()` sets `args->end` in the background branch.
- `FUSE_RELEASE_FLUSH`: never set under `fs/fuse/`.
- `struct fuse_file` is freed with `kfree()`, with no RCU delay.

**Choosing the I/O path**

- Order of the tests, first match wins:

  | Operation | Order |
  |---|---|
  | read, write | `FUSE_IS_DAX(inode)`, `FOPEN_DIRECT_IO`, `fuse_file_passthrough(ff)`, page cache |
  | `fuse_file_mmap()` | `FUSE_IS_DAX(inode)`, `fuse_file_passthrough(ff)`, `FOPEN_DIRECT_IO`, page cache |
  | `fuse_splice_read()`, `fuse_splice_write()` | passthrough only without `FOPEN_DIRECT_IO`, else `filemap_splice_read()` or `iter_file_splice_write()` |

- `fuse_cache_read_iter()`: has no direct-read branch of its own; it may
  call `fuse_update_attributes()` and return its error, else it calls
  `generic_file_read_iter()`, which serves `IOCB_DIRECT` through
  `fuse_direct_IO()`.

**Inode I/O modes**

- Inode states by sign of `fi->iocachectr`: caching (> 0), neutral (0),
  uncached (< 0); there is no direct-I/O mode, and a `FOPEN_DIRECT_IO` open
  without `FOPEN_PASSTHROUGH` takes no count.
- Negative count: passthrough opens plus one per direct write that holds
  the shared inode lock, taken by `fuse_dio_lock()` with
  `fuse_inode_uncached_io_start(fi, NULL)` and dropped by
  `fuse_dio_unlock()`.
- Conflicting open: `fuse_file_io_open()` returns `-EIO` for every failure;
  the inner `-ETXTBSY`, `-EBUSY`, `-EINVAL` and `-ENOENT` reach only
  `pr_debug()`.
- Caching open against parallel direct writes that hold the count: does not
  fail; `fuse_file_cached_io_open()` sleeps in `wait_event()` until the
  count is no longer negative.
- Parallel direct write against caching mode: does not fail;
  `fuse_dio_lock()` retakes the inode lock exclusive.
- `fuse_file_mmap()`: returns the error of `fuse_file_cached_io_open()`
  unchanged, not `-EIO`.
- `fc->writeback_cache`: not tested in `fs/fuse/iomode.c`;
  `process_init_reply()` leaves `fc->passthrough` clear when the server set
  `FUSE_WRITEBACK_CACHE`, so a `FOPEN_PASSTHROUGH` open on such a mount gets
  `-EIO`.
- Server with `fc->no_open`: does not bypass io modes; `ff->args` is set for
  every regular file, so the `!ff->args` tests in `fs/fuse/iomode.c` do not
  fire and the open enters caching mode.

**File locks**

- `fc->no_lock` and `fc->no_flock`: written only in `process_init_reply()`
  in `fs/fuse/inode.c`; an `-ENOSYS` reply to a lock request does not set
  them.
- `fc->no_flock` for protocol minor < 17: follows `FUSE_POSIX_LOCKS`, not
  `FUSE_FLOCK_LOCKS`; for minor < 6 both kinds stay in the kernel.
- There is no flock field in `struct fuse_conn`; `fc->no_flock` is the gate
  and `ff->flock` is per open file.
- Local POSIX path: `posix_lock_file(file, fl, NULL)` and
  `posix_test_lock()`, not `locks_lock_file_wait()`.
- `fuse_setlk()`: only sends the request; it records nothing in the kernel
  lock lists.
- `fuse_setlk()`: has no test of `FL_CLOSE` or `FL_CLOSE_POSIX`.
- Pid sent to the server: the result of `pid_nr_ns()`, 0 when the task is
  not visible in `fc->pid_ns` or the type is `F_UNLCK`; `fuse_setlk()` has
  no `-EOVERFLOW` test for a pid of 0.
- `fuse_lock_owner_id()`: 32 XTEA rounds over the pointer, keyed by
  `fc->scramble_key`.
- Owner pointer: `fuse_lk_fill()` sends `fl->c.flc_owner` whatever the lock
  kind; for OFD locks `fcntl_setlk()` in `fs/locks.c` sets it to the
  `struct file`, and `struct fuse_lk_in` has no OFD marker.
- `fuse_flush()`: the request it builds is `FUSE_FLUSH` carrying
  `lock_owner`; it does not call `fuse_setlk()`.
- `fuse_flush()` returns before sending when the file has `FOPEN_NOFLUSH`
  and `fc->writeback_cache` is clear, and skips the request when
  `fc->no_flush` is set.
- `FUSE_RELEASE_FLOCK_UNLOCK`: set by `fuse_file_release()`, only when
  `ff->args` is non-NULL and `ff->flock` is set.
- `ff->flock`: set by `fuse_file_flock()` only after `fuse_setlk()` returns
  0.
- flock kept in the kernel (`fc->no_flock`): released at close by
  `locks_remove_flock()` in `fs/locks.c`, which calls `fuse_file_flock()`
  and so `locks_lock_file_wait()`.

**Ioctls on files**

- `FUSE_IOCTL_UNRESTRICTED`: passed only by `cuse_file_ioctl()` and
  `cuse_file_compat_ioctl()`, and only when `cc->unrestricted_ioctl` is set
  from `CUSE_UNRESTRICTED_IOCTL` in the CUSE init reply; no FUSE mount path
  passes it.
- Retry count in unrestricted mode: unbounded; there is no
  FUSE_IOCTL_MAX_RETRY in this tree, and `fuse_do_ioctl()` loops as long as
  the server sets `FUSE_IOCTL_RETRY`.
- `in_iovs`, `out_iovs` or their sum above `FUSE_IOCTL_MAX_IOV`: `-ENOMEM`,
  not `-EIO`.
- `fuse_verify_ioctl_iov()`: `-ENOMEM` when the running total of one
  direction exceeds `fc->max_pages << PAGE_SHIFT`.
- `fuse_verify_ioctl_iov()` runs only on iovecs from a `FUSE_IOCTL_RETRY`
  reply; restricted-mode iovecs skip it and are bounded by the
  `max_pages > fm->fc->max_pages` test.
- User copies: inline in `fuse_do_ioctl()` with `copy_folio_from_iter()` and
  `copy_folio_to_iter()`; there is no fuse_ioctl_copy_user() here.
- Entry point for files: `fuse_ioctl_common()` through `fuse_file_ioctl()`;
  there is no fuse_file_do_ioctl() here.
- `FS_IOC_GETFLAGS`, `FS_IOC_SETFLAGS`, `FS_IOC_FSGETXATTR`,
  `FS_IOC_FSSETXATTR`: not special-cased in `fuse_do_ioctl()`;
  `do_vfs_ioctl()` routes them to `fuse_fileattr_get()` and
  `fuse_fileattr_set()`, which use `fuse_priv_ioctl()` with a kernel buffer.
- `FS_IOC_MEASURE_VERITY` in restricted mode: `fuse_setup_measure_verity()`
  resizes the single iovec to `sizeof(struct fsverity_digest)` plus the
  caller's `digest_size`.
- `FS_IOC_ENABLE_VERITY` in restricted mode: `fuse_setup_enable_verity()`
  appends input iovecs for salt and signature from the caller's
  `struct fsverity_enable_arg`; each is limited to
  `FUSE_VERITY_ENABLE_ARG_MAX_PAGES` pages, else `-ENOMEM`.

## Cached I/O and writeback

**Buffered reads**

- `fuse_read_folio()` and `fuse_readahead()`: both go through iomap,
  `iomap_read_folio()` and `iomap_readahead()`, with `fuse_iomap_ops` and
  `fuse_iomap_read_ops`.
- `fuse_iomap_read_folio_range_async()`: the one read hook for both; with
  `ctx->rac` NULL it calls `fuse_do_readfolio()` synchronously, despite its
  name; with `ctx->rac` set it calls `fuse_handle_readahead()`.
- Unit of a read: a byte range of a folio, not a folio;
  `fuse_do_readfolio()` takes `off` and `len`, and each batch entry carries
  its range in `struct fuse_folio_desc`.
- `fuse_do_readfolio()`: does not mark the folio uptodate, unlock it or
  touch atime; on success `fuse_iomap_read_folio_range_async()` finishes
  the range with `iomap_finish_folio_read()`, and `fuse_read_folio()` calls
  `fuse_invalidate_atime()`.
- `fuse_read_folio()` when READ fails: returns 0 and leaves the folio not
  uptodate; it returns `-EIO` only for `fuse_is_bad()`.
- Failed readahead: there is no folio error flag;
  `iomap_finish_folio_read()` with an error ends the read with the folio not
  uptodate.
- `fuse_readahead()`: does not walk the window; `iomap_readahead()` does,
  and `fuse_readahead()` only sends the batch left in `data.ia`.
- `fuse_short_read()`: zeroes nothing; the tail is zeroed by
  `fuse_copy_folio()` in `fs/fuse/dev.c` because the READ sets
  `page_zeroing`; on virtio-fs `virtio_fs_request_complete()` does it.

**Buffered writes**

- `fuse_perform_write()`: always sends synchronous WRITEs.
- Writeback cache on: `fuse_cache_write_iter()` calls
  `iomap_file_buffered_write()` with `fuse_iomap_ops` and
  `fuse_iomap_write_ops`; it does not call `generic_file_write_iter()`, and
  there is no fuse_write_begin or fuse_write_end in this tree.
- `inode_lock()`: taken by `fuse_cache_write_iter()` itself, in both modes.
- Partial write to a non-uptodate range, writeback cache on:
  `fuse_iomap_read_folio_range()` reads the missing range synchronously.
- `fuse_fill_write_pages()`: never reads from the server.
- Uptodate on the write-through path: `fuse_fill_write_pages()` marks a
  folio uptodate at copy time when the whole folio was copied;
  `fuse_send_write_pages()` changes no uptodate state, whatever the reply.
- Folio locks across the WRITE: uptodate folios are unlocked before the
  send; only a last, non-uptodate folio stays locked
  (`ia->write.folio_locked`).
- `fc->handle_killpriv_v2` set and `setattr_should_drop_suidgid()` true:
  `writeback` stays false, so the write goes through `fuse_perform_write()`
  even with the writeback cache on.
- `IOCB_DIRECT` in `fuse_cache_write_iter()`: `generic_file_direct_write()`
  first; what is left goes through `fuse_perform_write()`, also with the
  writeback cache on.
- Dirty times: there is no FUSE_I_MTIME_DIRTY here; `fuse_write_inode()`
  calls `fuse_flush_times()` each time the VFS writes the inode.

**Data under writeback**

- Data in flight: the page-cache folio itself is in the WRITE; there is no
  temporary copy, no fi->writepages tree and no
  fuse_wait_on_page_writeback in this tree.
- Names: the file is taken with `fuse_write_file_get()`; the test for
  sending the pending request is `fuse_folios_need_send()`.
- `fuse_iomap_writeback_range()`: does no per-folio accounting;
  `iomap_writeback_folio()` starts folio writeback before it calls the hook.
- `fuse_writepage_finish()`: only calls `iomap_finish_folio_write()` per
  entry and wakes `fi->page_waitq`; it updates no statistics.
- Writeback ending with no reply: `fuse_send_writepage()` finishes the
  request at `out_free` when it lies wholly beyond the crop size or when
  queuing fails.
- Request blocked by `FUSE_NOWRITE`: it sits on `fi->queued_writes` and its
  folios stay under writeback until the release.
- Two kinds of wait: `folio_wait_writeback()` waits for one folio;
  `fuse_sync_writes()` waits for `fi->writectr`, that is for sent requests.
- `folio_wait_writeback()` under `fs/fuse/`: `fuse_page_mkwrite()`,
  `fuse_send_write_pages()` and `fuse_launder_folio()`.
- `fuse_page_mkwrite()`: waits unconditionally; it does not call
  `folio_wait_stable()`.
- `fuse_sync_writes()` callers: `fuse_fsync()`, `fuse_direct_io()` and
  `fuse_writeback_range()`.
- `fuse_flush()`: does not call `fuse_sync_writes()`; it waits through
  `write_inode_now(inode, 1)`.
- Buffered write with the writeback cache on: `folio_wait_stable()` waits
  only with `AS_STABLE_WRITES`; nothing under `fs/fuse/` sets it, but
  `setup_bdev_super()` sets `SB_I_STABLE_WRITES` for a fuseblk mount on a
  device with stable writes.

**Truncate and size changes**

- Flush before SETATTR: done only for `ATTR_MODE`, `ATTR_UID`, `ATTR_GID`,
  `ATTR_MTIME_SET` or `ATTR_TIMES_SET` on a writeback-cache regular file,
  with `write_inode_now(inode, true)` then a set/release nowrite pair; a
  plain size change flushes nothing.
- `FUSE_I_SIZE_UNSTABLE`: set with `set_bit()` outside `fi->lock`; it is one
  bit with no count, and its setters, for example `fuse_perform_write()` and
  `fuse_file_fallocate()`, hold the inode lock.
- Test of the flag: in `fuse_change_attributes_i()` in `fs/fuse/inode.c`; a
  reply that meets it is dropped whole, not only its size.
  `fuse_read_update_size()` tests it too.
- `trust_local_cmtime`: a local in `fuse_do_setattr()`, true for a
  writeback-cache regular file; it is not a field of `struct fuse_conn`.
- New size: `i_size_write()` takes `outarg.attr.size` from the reply, not
  `attr->ia_size`.
- Page cache after success: one branch, taken only when the size changed
  and the call is a truncate or the writeback cache is off; it calls
  `truncate_pagecache_range()` when the file grew, then
  `truncate_pagecache()`, then `invalidate_inode_pages2()`.
- `-EINTR` from SETATTR: `fuse_invalidate_attr()` runs before the error
  path.
- Bad reply (`fuse_invalid_attr()` or `inode_wrong_type()`):
  `fuse_make_bad()`, `-EIO`, then the same error path.

**Fsync and syncfs**

- Bucket count: taken by `fuse_writepage_add_to_bucket()`, called from
  `fuse_writepage_args_setup()`; there is no fuse_sync_bucket_get or
  fuse_sync_bucket_inc in this tree.
- Time of the count: when the request is set up, before it is queued or
  sent, so syncfs also waits for requests still on `fi->queued_writes`.
- `fc->sync_fs` clear: `fuse_writepage_add_to_bucket()` takes no count and
  `wpa->bucket` stays NULL.
- `fuse_sync_fs_writes()`: returns without swapping when the old count
  is 1; otherwise the new bucket holds one extra count until the old bucket
  drains, so a later syncfs also waits for the earlier buckets.
- Dirty folios before `fuse_sync_fs()`: `fuse_sb_defaults()` sets
  `SB_I_NO_DATA_INTEGRITY`, and with it `sync_inodes_sb()` only wakes the
  flusher and returns, so dirty data is not known to be written or waited
  for.
- Before FSYNC, after `fuse_sync_writes()`: `fuse_fsync()` calls
  `file_check_and_advance_wb_err()`, then `sync_inode_metadata(inode, 1)`;
  an error from either skips FSYNC.
- FSYNCDIR: sent by `fuse_dir_fsync()` in `fs/fuse/dir.c`, not by
  `fuse_fsync()`.
- Writeback error routes, all fed by `mapping_set_error()` in
  `fuse_writepage_end()`:

| Caller | Where the error is read |
|---|---|
| fsync | `file_check_and_advance_wb_err()` in `fuse_fsync()` |
| close | `filemap_check_errors()` in `fuse_flush()` |
| syncfs | `sb->s_wb_err`, checked in the `syncfs` syscall in `fs/sync.c` |
| munmap | none; `fuse_vma_close()` stores the `write_inode_now()` result with `mapping_set_error()` for a later caller |

**Memory mapping**

- Inode with a backing file, file not opened passthrough:
  `fuse_file_mmap()` returns `-ENODEV`.
- Shared test for `FOPEN_DIRECT_IO`: `VM_MAYSHARE`, so it also covers a
  read-only `MAP_SHARED` mapping; the test for `fuse_link_write_file()` is
  `VM_SHARED` with `VM_MAYWRITE`.
- Private mapping of a `FOPEN_DIRECT_IO` file: set up by
  `generic_file_mmap()`, so it does not get `fuse_file_vm_ops`.
- `fuse_file_cached_io_open()`: waits while the inode is in uncached mode
  with no backing file (parallel direct writes); returns `-ETXTBSY` only
  when the inode has a backing file.
- `fuse_vma_close()`: calls `write_inode_now(inode, 1)` on every close of a
  vma that has `fuse_file_vm_ops`, read-only and private cached mappings
  included; it does not call `filemap_write_and_wait()`.
- VMA tracking: there is none; a shared writable mapping adds only the
  entry on `fi->write_files`, and a shared mapping of a `FOPEN_DIRECT_IO`
  file also takes caching io mode in `fuse_file_cached_io_open()`.

**Blocking writeback**

- `FUSE_NOWRITE`: `INT_MIN`; `fuse_set_nowrite()` adds it to
  `fi->writectr` as a bias and does not overwrite the counter.
- `fi->writectr`: `fuse_send_writepage()` increments it before it decides
  to send, and decrements it again at `out_free` for a request it finishes
  unsent.
- `fuse_flush()`: does not use the pair; users are `fuse_open()`,
  `fuse_do_setattr()` and `fuse_sync_writes()`.
- `__fuse_release_nowrite()`: static in `fs/fuse/dir.c`, needs `fi->lock`
  held, and may drop and retake it through `fuse_flush_writepages()`.
- **Unsafe usage**: calling `fuse_set_nowrite()` without the inode lock.
  - Unsafe: `BUG_ON(!inode_is_locked(inode))` fires.
  - Safe: under `inode_lock()`, as `fuse_fsync()` and `fuse_open()` do.
- **Unsafe usage**: a second `fuse_set_nowrite()` before the release.
  - Unsafe: `BUG_ON(fi->writectr < 0)` fires; `inode_is_locked()` is also
    true for a shared hold, so the first check does not exclude this.
  - Safe: one pair at a time under exclusive `inode_lock()`, as
    `fuse_fsync()` does.
- **Unsafe usage**: `fuse_release_nowrite()` with no completed
  `fuse_set_nowrite()` before it.
  - Unsafe: `BUG_ON(fi->writectr != FUSE_NOWRITE)` in
    `__fuse_release_nowrite()` fires.
  - Safe: release after `fuse_set_nowrite()` returned, as
    `fuse_sync_writes()` does.
- **Unsafe usage**: returning between set and release without the release.
  - Unsafe: `fuse_flush_writepages()` sends nothing while `fi->writectr` is
    negative, so later requests stay queued and their folios stay under
    writeback.
  - Safe: release on the error path too, as the `error` label of
    `fuse_do_setattr()` does.
- **Unsafe usage**: waiting for folio writeback between set and release,
  for example with `truncate_pagecache()` or `invalidate_inode_pages2()`.
  - Unsafe: a request queued during the block is never sent, so
    `folio_wait_writeback()` in `fuse_launder_folio()` never returns.
  - Safe: release first, then truncate or invalidate, as
    `fuse_do_setattr()` and `fuse_open()` do.

**Allocation on write paths**

- `fuse_writepage_args_alloc()` and `fuse_pages_realloc()`: plain
  `GFP_NOFS`, no `__GFP_NOFAIL`; on failure
  `fuse_iomap_writeback_range()` returns `-ENOMEM` or sends what it has.
- `fuse_send_writepage()`: entered with `fi->lock` held; first try is
  `GFP_ATOMIC`; only on `-ENOMEM` it drops `fi->lock` and retries with
  `GFP_NOFS | __GFP_NOFAIL`.
- gfp argument of `fuse_simple_background()`: used only when `args->force`
  is set; otherwise `fuse_get_req()` allocates with `GFP_KERNEL` and may
  sleep on `fch->blocked_waitq`.
- `fuse_simple_request()`: `GFP_KERNEL | __GFP_NOFAIL` only for a forced
  request, in `fuse_chan_send()`; there is no preallocated
  `struct fuse_req`.
- `fuse_file_alloc()`: allocates `ff->args`, a `union fuse_file_args`, with
  `GFP_KERNEL_ACCOUNT`; it can fail, and `fuse_file_open()` then returns
  `-ENOMEM`.
- `fuse_file_open()` for a regular file: allocates `ff->args` even with
  `fc->no_open`, when no RELEASE is sent; `fuse_prepare_release()` keeps the
  inode reference there until the last `fuse_file_put()`, for example the
  one from `fuse_readpages_end()`.
- `AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`: `fuse_init_file_inode()` sets it
  only when `fc->writeback_cache`.
- **Potentially unsafe usage**: allocating with `__GFP_FS` after folio
  writeback has started and before the WRITE is queued.
  - Unsafe: outside a `memalloc_nofs_save()` scope; reclaim may reach
    `folio_wait_writeback()` in `shrink_folio_list()` for a mapping without
    `AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`, on a folio whose WRITE the
    allocating task has not yet queued.
  - Safe: `GFP_NOFS`, as `fuse_writepage_args_alloc()` and
    `fuse_pages_realloc()` use; `may_enter_fs()` in `mm/vmscan.c` is what
    keeps reclaim from waiting.
  - Safe: `GFP_KERNEL` between `memalloc_nofs_save()` and
    `memalloc_nofs_restore()`, as `virtio_fs_request_dispatch_work()` does
    around `virtio_fs_enqueue_req()`; `current_gfp_context()` clears
    `__GFP_FS` from the mask that reclaim sees.

## Direct I/O and passthrough

**Direct I/O**

- `fuse_direct_io()` before a read or a write on a `FOPEN_DIRECT_IO` file:
  calls `filemap_write_and_wait_range()` on the range and returns its error
  before any request is sent.
- `fuse_direct_io()` before a `FOPEN_DIRECT_IO` write: calls
  `invalidate_inode_pages2_range()` and returns its error.
- `fc->direct_io_allow_mmap`: tested by neither step above, nor by
  `fuse_dio_wr_exclusive_lock()`; within `fs/fuse` it is read only in
  `fuse_file_mmap()`.
- `fuse_sync_writes()`: runs for reads and writes alike, when the call is not
  `FUSE_DIO_CUSE` and `filemap_range_has_writeback()` is true.
- Invalidation after a write: done by `fuse_direct_write_iter()`, not by
  `fuse_direct_io()`; only when `res > 0 && mapping->nrpages`; the result is
  ignored.
- Async write that is not blocking, with `res > 0` and `mapping->nrpages`:
  `fuse_aio_complete()` queues `fuse_aio_invalidate_worker()` on
  `s_dio_done_wq`, which invalidates and then calls `ki_complete`.
- `cuse_write_iter()` and `fuse_dax_direct_write()` call `fuse_direct_io()`
  themselves and do no invalidation after the write.
- `fuse_dio_lock()` returns holding `inode_lock_shared()` only when all of
  these hold:
  - `ff->open_flags` has `FOPEN_PARALLEL_DIRECT_WRITES`
  - `IOCB_APPEND` is clear
  - `FUSE_I_CACHE_IO_MODE` is clear in `fi->state`
  - `fuse_io_past_eof()` is false, both before and after taking the lock
  - `fuse_inode_uncached_io_start(fi, NULL)` returns 0 under the shared lock
- `O_DIRECT` without `FOPEN_DIRECT_IO`, on a file that is neither DAX nor
  passthrough: the write goes through `fuse_cache_write_iter()` under
  `inode_lock()`, never the shared lock; `fuse_file_io_open()` clears
  `FOPEN_PARALLEL_DIRECT_WRITES` for such a file.
- Async kiocb with `fc->async_dio`, write within EOF: `fuse_direct_IO()`
  returns `-EIOCBQUEUED` and `fuse_dio_unlock()` runs without waiting for the
  replies, so the inode lock and the uncached-io count cover submission only.

**Backing files**

- `fuse_backing_open()`, `fuse_backing_close()` and `fuse_backing_lookup()`:
  in `fs/fuse/backing.c`, built with `fs/fuse/passthrough.c` only under
  `CONFIG_FUSE_PASSTHROUGH`.
- `fuse_dev_ioctl_backing_open()` in `fs/fuse/dev.c`: returns `-EOPNOTSUPP`
  without `CONFIG_FUSE_PASSTHROUGH`; `fuse_backing_open()` itself never
  returns that error.
- Checks in `fuse_backing_open()`, in order:

| Test that fails | Error |
|---|---|
| `fc->passthrough` clear, or no `capable(CAP_SYS_ADMIN)` | `-EPERM` |
| `map->flags` or `map->padding` non-zero | `-EINVAL` |
| `fget_raw(map->fd)` returns NULL | `-EBADF` |
| `d_is_reg()` false | `-EISDIR` for a directory, else `-EINVAL` |
| `s_stack_depth >= fc->max_stack_depth` | `-ELOOP` |

- `fuse_backing_open()`: does not test `->read_iter` or `->write_iter`, and
  has no test for a FUSE superblock; the depth test is the only limit on the
  backing filesystem.
- `fget_raw()`: unlike `fget()`, it does not mask `FMODE_PATH`, so an `O_PATH`
  fd is accepted.
- `fc->passthrough`: `process_init_reply()` in `fs/fuse/inode.c` sets it only
  when the reply has `FUSE_PASSTHROUGH`, `max_stack_depth` is between 1 and
  `FILESYSTEM_MAX_STACK_DEPTH`, and `FUSE_WRITEBACK_CACHE` is not set.
- `struct fuse_backing`: the refcount field is `count`; `cred` comes from
  `get_current_cred()`.
- `fuse_backing_free()`: calls `fput()` and `put_cred()` at once; only the
  `kfree_rcu()` is deferred.
- **Unsafe usage**: using `fb->file` or `fb->cred` of an entry from
  `idr_find()` on `fc->backing_files_map` under `rcu_read_lock()` alone.
  - Safe: take the reference with `fuse_backing_get()` first, as
    `fuse_backing_lookup()` does; RCU keeps only the memory of the
    `struct fuse_backing` valid.
- `struct fuse_file`: holds no `struct fuse_backing` reference.
  `ff->passthrough` is a separate `struct file` from `backing_file_open()`
  and `ff->cred` is its own cred reference; `fuse_passthrough_release()`
  drops both.
- `fi->fb`: holds one reference per inode, however many files are open.
- `fuse_inode_uncached_io_start()` on success: consumes the reference from
  `fuse_backing_lookup()`, storing it in `fi->fb` or putting it when `fi->fb`
  is already that backing file.
- `fuse_inode_uncached_io_start()` on failure: the caller keeps the
  reference; `fuse_file_passthrough_open()` puts it.
- `fi->fb` is put by `fuse_inode_uncached_io_end()` when `fi->iocachectr`
  returns to 0, and by `fuse_free_inode()` if still set.
- `fuse_backing_files_free()`, called from `fuse_conn_put()`: calls
  `fuse_backing_free()` on each IDR entry directly, without a put; it only
  warns when `count` is not 1.

**Passthrough I/O**

- `FOPEN_PASSTHROUGH` with `FOPEN_DIRECT_IO`: allowed by
  `FOPEN_PASSTHROUGH_MASK` in `fs/fuse/iomode.c`; the flag is not cleared.
- With both flags, `fuse_file_read_iter()`, `fuse_file_write_iter()`,
  `fuse_splice_read()` and `fuse_splice_write()` skip the backing file;
  `fuse_file_mmap()` tests `fuse_file_passthrough()` before
  `FOPEN_DIRECT_IO` and still maps the backing file.
- DAX inode: `fuse_file_io_open()` returns 0 before it looks at
  `FOPEN_PASSTHROUGH`, so `ff->passthrough` stays NULL and nothing is passed
  through.
- `backing_file_open()`: its first argument is the FUSE `struct file *`, not
  a path; `fuse_passthrough_open()` passes `file`.
- Credential switch: the helpers in `fs/backing-file.c` use
  `scoped_with_creds(ctx->cred)`; they contain no direct `override_creds()`
  call.
- `file_remove_privs(iocb->ki_filp)`: `backing_file_write_iter()` and
  `backing_file_splice_write()` call it on the FUSE file before the switch,
  so it runs with the credentials of the task doing the write.
- Attributes: nothing is copied from the backing inode.
- After a write, `fuse_passthrough_end_write()` calls
  `fuse_write_update_attr()`: `i_size` is raised to `iocb->ki_pos` when the
  write went past it, and `FUSE_STATX_MODSIZE` is invalidated.
- After a read, splice read or mmap, `fuse_file_accessed()` calls
  `fuse_invalidate_atime()`: it invalidates `STATX_ATIME` unless the inode is
  `IS_RDONLY()`; it does not call `touch_atime()`.
- Invalidated attributes are refetched from the server, so the FUSE inode
  shows the size and times that the server reports.
- Async write that returns `-EIOCBQUEUED`: `end_write` runs later from
  `backing_aio_complete_work()` on the `s_dio_done_wq` of the FUSE
  superblock, outside the `inode_lock()` that
  `fuse_passthrough_write_iter()` took.
- `fuse_passthrough_mmap()`: its ctx has no `end_write`, and
  `backing_file_mmap()` replaces `vma->vm_file` with the backing file, so
  stores through a shared mapping neither update nor invalidate the FUSE
  inode's cached size or times.

## virtio-fs and DAX

**virtio-fs request path**

- `virtio_fs_send_req()`: handles requests only; the queue is
  `fs->mq_map[raw_smp_processor_id()]`, which `virtio_fs_map_queues()` fills
  with indices from `VQ_REQUEST` up. Forgets come through the separate hook
  `virtio_fs_send_forget()`.
- `req->in.h.unique`: assigned in `virtio_fs_send_req()` by
  `fuse_request_assign_unique()` (`fs/fuse/dev.c`), not before the `send_req`
  op runs; `fuse_send_one()` sets only `in.h.len`.
- Scatterlist order in `virtio_fs_enqueue_req()`: `req->in.h` and the FUSE
  in-args first (device-readable); `req->out.h` and the out-args after, only
  when `FR_ISREPLY` is set.
- There is no sg_init_fuse_pages() here; `sg_init_fuse_folios()` maps
  `ap->folios` with `ap->descs`.
- Processing list: `fsvq->fud->pq.processing[]`, under `fpq->lock` nested inside
  `fsvq->lock`.
- Kick: `virtqueue_kick_prepare()` under `fsvq->lock`, `virtqueue_notify()`
  after the unlock.
- `virtio_fs_enqueue_req()` takes no reference on `req`; the `fuse_request_end()`
  in completion consumes the one from `fuse_request_alloc()`.
- `-ENOSPC` is the only error that parks a request on `fsvq->queued_reqs`.
  `-ENOMEM` and `-ENOTCONN` fail the request.
- `-ENOSPC` in `virtio_fs_send_req()`: schedules no work and arms no timer. The
  retry runs in `dispatch_work`, which `virtio_fs_requests_done_work()`
  schedules when it finds `queued_reqs` non-empty.
- `dispatch_work`: a plain `struct work_struct`, not delayed work.
- Other errors in `virtio_fs_send_req()`: the request is not ended there. It
  goes on `fsvq->end_reqs` and `virtio_fs_request_dispatch_work()` calls
  `fuse_request_end()`.
- Forget errors in `send_forget_request()`: queued only on `-ENOSPC`. On any
  other error, or on a disconnected queue, the forget is freed and silently
  dropped.
- `virtio_fs_requests_done_work()`: unlinks each request from the processing
  list itself; `virtio_fs_request_complete()` does not touch the list.
- `virtio_fs_verify_response()`: runs on every used buffer of a request queue.
  A short reply, or an `oh->len` or `oh->unique` mismatch, completes the
  request with `-EIO`.
- `req->args->may_block`: such a request completes in its own work item,
  `virtio_fs_complete_req_work()`. All others complete inline in the per-queue
  `done_work`, so a sleeping `end` callback there stalls that queue.

**virtio-fs mount and removal**

- Connection setup in `virtio_fs_get_tree()`: `fuse_chan_new()`, then
  `fuse_iqueue_init(&fch->iq, &virtio_fs_fiq_ops, fs)`, then
  `fuse_conn_init(fc, fm, fsc->user_ns, fch)`. `fuse_conn_init()` takes no ops
  or priv argument.
- The device instance is `fc->chan->iq.priv`; `struct fuse_conn` has no `iq`
  member of its own. `virtio_fs_test_super()` compares that pointer.
- `fc->release` is `fuse_free_conn`, the same as for a `/dev/fuse` mount.
- `struct virtio_fs` is a kobject, not a kref; `virtio_fs_ktype_release()` frees
  it together with `fs->vqs`.
- The connection's reference on `struct virtio_fs` is dropped by the last
  `fuse_conn_put()`, through `fuse_chan_release()` and
  `virtio_fs_fiq_release()`. `virtio_fs_put()` takes `virtio_fs_mutex`.
- **Potentially unsafe usage**: `fuse_dev_put()` or `fuse_conn_put()` with
  `virtio_fs_mutex` held.
  - Unsafe: when it can drop the last `struct fuse_conn` reference;
    `virtio_fs_put()` then locks the mutex again.
  - Safe: on a `struct fuse_dev` that was never installed, as in the error path
    of `virtio_fs_fill_super()`; `fuse_dev_put()` then skips `fuse_conn_put()`.
- `virtio_fs_fill_super()`: rechecks `list_empty(&fs->list)` under
  `virtio_fs_mutex` and fails with `-EINVAL`, because the device may have been
  removed after the lookup.
- Per-queue `struct fuse_dev`: `fuse_dev_alloc()` before
  `fuse_fill_super_common()`, `fuse_dev_install(fsvq->fud, fc->chan)` after it.
  `fuse_dev_alloc_install()` is not used.
- There is no fudptr in `fs/fuse`; `ctx->fud` stays NULL, so
  `fuse_fill_super_common()` installs nothing.
- The `kill_sb` hook is `virtio_kill_sb()`; there is no virtio_fs_kill_sb().
- `virtio_kill_sb()` order: `fuse_mount_remove()`, `virtio_fs_conn_destroy()` if
  that was the last mount, `kill_anon_super()`, `fuse_mount_destroy()`.
- `virtio_fs_conn_destroy()` steps, in order:
  - `fuse_dax_cancel_work()`;
  - `connected = false` on `VQ_HIPRIO` only, then `virtio_fs_drain_all_queues()`;
  - `fuse_conn_destroy()`: sends `FUSE_DESTROY` if `fc->conn_init` is set
    (`ctx->destroy` is forced true), then `fuse_chan_abort()` and
    `fuse_chan_wait_aborted()`;
  - `virtio_fs_stop_all_queues()`, drain again, `virtio_fs_free_devs()`.
- A `/dev/fuse` mount runs only `fuse_conn_destroy()` from `fuse_sb_destroy()`,
  and sets `ctx->destroy` only for fuseblk.
- `virtio_fs_remove()` does not end requests that are in the ring. It waits in
  `virtio_fs_drain_queue()` for the device to complete them, with
  `virtio_fs_mutex` held; a device that never answers blocks removal.
- Requests parked on `queued_reqs` at removal: failed with `-ENOTCONN` when the
  dispatch work resubmits them.
- After removal the connection is not aborted; `fs/fuse/virtio_fs.c` never calls
  `fuse_chan_abort()`. Each later request fails on its own with `-ENOTCONN`;
  forgets are freed.
- `no_control` and `no_force_umount` are forced on in
  `virtio_fs_ctx_set_defaults()`, so neither the control filesystem nor
  `umount -f` can abort the connection.
- `fsvq->vq` after removal: dangling, since `virtio_fs_cleanup_vqs()` deleted
  the virtqueues while `fs->vqs` stays allocated. `fsvq->connected`, tested
  under `fsvq->lock`, is the guard in `virtio_fs_enqueue_req()` and
  `send_forget_request()`.

**DAX mappings**

- `fuse_dax_break_layouts()`: a one-line wrapper around `dax_break_layout()`
  (`fs/dax.c`) with `fuse_wait_dax_page()` as the callback. There is no
  dax_wait_page_idle() in this tree.
- `dax_break_layout()` waits in `TASK_INTERRUPTIBLE`, so
  `fuse_dax_break_layouts()` can fail; all five callers check the result.
- `dax_break_layout()` on success also removes the DAX entries of the range from
  the page cache with `dax_delete_mapping_range()`. It does not touch
  `fi->dax->tree`.
- Truncate frees no `struct fuse_dax_mapping`. Ranges beyond the new size stay in
  the tree until reclaim or `fuse_dax_inode_cleanup()`; `fuse_fill_iomap()`
  reports a hole past `i_size`.
- Whole-file callers pass `0, -1`: `fuse_do_setattr()`, `fuse_open()` and
  `fuse_file_fallocate()`.
- `fuse_file_fallocate()`: breaks layouts for punch hole and zero range, and
  also for every call without `FALLOC_FL_KEEP_SIZE`; see `block_faults`.
- `fuse_setup_one_mapping()`: sends `inarg.fh = -1`, never a file handle.
- `fuse_setup_new_dax_mapping()`: is entered without `fi->dax->sem`. It
  allocates the range first, then takes the lock for write and rechecks the
  tree.
- With `IOMAP_FAULT`, `fuse_setup_new_dax_mapping()` never reclaims inline. It
  returns `-EAGAIN` when no range is free, and `__fuse_dax_fault()` drops the
  invalidate lock, waits on `fcd->range_waitq` and retries.
- `dmap->refcnt`: 1 when idle. Reclaim skips a range when
  `refcount_read(&dmap->refcnt) > 1`.
- `dax_iomap_rw()` is protected from reclaim by `dmap->refcnt`, raised under
  `fi->dax->sem`. No reclaim path takes the inode lock, and read/write takes
  the invalidate lock only inside `inode_inline_reclaim_one_dmap()`.
- The inode lock serialises read/write against truncate, not against reclaim.
- Reclaim functions for a live inode are `inode_inline_reclaim_one_dmap()`
  (inline) and `lookup_and_reclaim_dmap()` (worker); both end in
  `reclaim_one_dmap_locked()`. There is no
  inode_reclaim_one_dax_mapping_locked(), fuse_dax_free_one_mapping() or
  reclaim_one_dmap().
- `fuse_iomap_ops` in `fs/fuse/dax.c`: sets only `.iomap_next`.
  `fuse_iomap_begin()` and `fuse_iomap_end()` are called from
  `fuse_iomap_next()`, which `DEFINE_IOMAP_ITER_NEXT_END()` generates.

## CUSE

**Character devices in user space**

- There is no fuse_abort_conn() here; `fuse_chan_abort(fc->chan, false)` in
  `fs/fuse/dev.c` does that, in `cuse_process_init_reply()` and in
  `cuse_class_abort_store()`.
- `cuse_channel_open()`: gets the channel from `fuse_dev_chan_new()` and
  passes it as the fourth argument of `fuse_conn_init()`; `fuse_dev_fiq_ops`
  is static in `fs/fuse/dev.c`.
- `fuse_dev_alloc_install()`: takes the `struct fuse_chan *`, not the
  connection.
- `cuse_channel_open()`: stores the `struct fuse_dev` in
  `file->private_data`, and only after `cuse_send_init()` succeeded.
- `cuse_channel_open()`: sets `cc->fc.chan->initialized` with
  `smp_store_release()` before `CUSE_INIT` is sent; it does not call
  `fuse_chan_set_initialized()`.
- `fch->minor`, `fch->max_write`, `fch->max_pages`, `fch->io_uring`: 0 on a
  CUSE channel for its whole life; they are set only through
  `fuse_chan_set_initialized()` with a `struct fuse_chan_param`, which only
  `process_init_reply()` in `fs/fuse/inode.c` passes.
- `cuse_process_init_reply()`: of `struct fuse_conn` it sets only
  `fc->minor`, `fc->max_read` and `fc->max_write`; `fc->max_pages` stays
  `FUSE_DEFAULT_MAX_PAGES_PER_REQ` from `fuse_conn_init()`.
- `cuse_process_init_reply()`: reads its own flag word in
  `struct cuse_init_out`; `CUSE_UNRESTRICTED_IOCTL` is the only flag, and no
  FUSE_INIT flag is parsed.
- `cuse_process_init_reply()`: builds the device with `device_initialize()`
  and `device_add()`, not `device_create()`; the devt comes from
  `arg->dev_major` and `arg->dev_minor`, and a zero major is allocated by
  `alloc_chrdev_region()`.
- `cuse_process_init_reply()`: returns `void`; a duplicate `DEVNAME` and
  every other failure end in `fuse_chan_abort()`, no error code is reported.
- `cuse_open()`: takes `cuse_lock` with `mutex_lock()`; it does not call
  `nonseekable_open()` and does not force `FOPEN_DIRECT_IO`.
- `ff->open_flags` on a CUSE file: whatever the server replied; with
  `FOPEN_DIRECT_IO` set, `fuse_direct_io()` runs
  `filemap_write_and_wait_range()` and, for a write,
  `invalidate_inode_pages2_range()` on the chrdev inode's mapping, outside
  the `FUSE_DIO_CUSE` test.
- `fc->no_open` and `fc->no_poll`: set on a CUSE connection by an `-ENOSYS`
  reply, in `fuse_file_open()` and `fuse_file_poll()`; with `fc->no_open`
  set, `cuse_open()` succeeds without `FUSE_OPEN` and `fuse_file_put()`
  sends no `FUSE_RELEASE`.
- `cc->fm`: is on `fc->mounts` with `fm->sb == NULL`; `fuse_ilookup()` is
  the only walker of that list and skips it.
- Core functions `fs/fuse/cuse.c` calls with the chrdev file or its
  `struct fuse_file`: `fuse_do_open()`, `fuse_sync_release()`,
  `fuse_direct_io()`, `fuse_do_ioctl()`, `fuse_file_poll()`.
- `fs/fuse/cuse.c` does not call `fuse_release_common()`,
  `fuse_direct_read_iter()`, `fuse_direct_write_iter()` or
  `fuse_file_ioctl()`; those are the FUSE-only wrappers and they use the
  FUSE inode.
- `fuse_do_ioctl()`: has no CUSE flag and touches no inode; the inode checks
  are in `fuse_ioctl_common()` in `fs/fuse/ioctl.c`.
- `fuse_fill_creds()` in `fs/fuse/req.c`: runs for every CUSE request and
  treats `!fm->sb` as no idmapping.
- `cuse_class_waiting_show()`: reads `cc->fc.chan->num_waiting`; CUSE never
  calls `fuse_conn_destroy()` or `fuse_chan_wait_aborted()`.
- `cuse_channel_release()`: only unhashes and removes the device; the abort
  is in `fuse_dev_release()`, when the last `struct fuse_dev` leaves
  `fch->devices`.
- `struct cuse_conn`: freed by the last `fuse_conn_put()`, through
  `call_rcu()` and `fc->release`; an open frontend file holds a reference,
  so the last put can be in `cuse_release()`, after the channel is aborted.
- `cuse_init()`: copies `fuse_dev_operations`, replaces `.open` and
  `.release`, and sets `.unlocked_ioctl` to NULL; no command of
  `fuse_dev_ioctl()` is reachable on `/dev/cuse`, and `compat_ptr_ioctl()`
  returns `-ENOIOCTLCMD`.
- `fuse_uring_cmd()` on `/dev/cuse`: inherited under
  `CONFIG_FUSE_IO_URING`; no command is dispatched because `fch->io_uring`
  is 0, and a command with `IO_URING_F_SQE128` on a connected channel gets
  `-EOPNOTSUPP`.
- `fuse_notify()` on `/dev/cuse`: `fuse_dev_do_write()` passes every
  notification to it once `fch->initialized` is set and while
  `fch->connected`, so before the `CUSE_INIT` reply too.
- Exports: `CONFIG_CUSE` is tristate, so each core function
  `fs/fuse/cuse.c` calls needs `EXPORT_SYMBOL_GPL()`;
  `__fuse_simple_request()` and `fuse_chan_set_initialized()` are not
  exported.
- **Potentially unsafe usage**: using the file's inode as a FUSE inode in
  `fuse_do_open()`, `fuse_direct_io()`, `fuse_sync_release()`,
  `fuse_do_ioctl()`, `fuse_file_poll()` or a function they call.
  - Unsafe: on a path that runs for a CUSE file; the inode is the chrdev
    inode, `get_fuse_inode()` is a `container_of()` and returns a bad
    pointer, not NULL, and `get_fuse_conn()` reads another filesystem's
    `s_fs_info`.
  - Safe: behind `!(flags & FUSE_DIO_CUSE)`, as the `fuse_sync_writes()`
    call in `fuse_direct_io()`; the flag is defined in `fs/fuse/fuse_i.h`.
  - Safe: behind the `fi` NULL test and `sync`, as in
    `fuse_prepare_release()`; `cuse_release()` passes `fi == NULL`.
  - Safe: behind `fuse_file_passthrough(ff)`, as the
    `fuse_inode_backing(fi)` call in `fuse_prepare_release()`;
    `ff->passthrough` is set only by `fuse_passthrough_open()`, reached from
    `fuse_finish_open()`, which CUSE does not call.
  - Safe: on the `io->async` path only, as `fuse_aio_complete()`;
    `FUSE_IO_PRIV_SYNC()` sets `async` to 0 and CUSE uses nothing else.
  - Safe: in the FUSE-only wrapper, outside the shared call, as
    `fuse_ioctl_common()` and `fuse_direct_write_iter()` do.
  - Safe: taking the connection from `ff->fm`, as `fuse_file_poll()` does.
- **Potentially unsafe usage**: branching on `fch->minor`,
  `fch->max_write` or `fch->max_pages` in `fs/fuse/dev.c`.
  - Unsafe: when the branch changes what is sent for an opcode CUSE sends
    (`CUSE_INIT`, `FUSE_OPEN`, `FUSE_RELEASE`, `FUSE_READ`, `FUSE_WRITE`,
    `FUSE_IOCTL`, `FUSE_POLL`, `FUSE_INTERRUPT`); the value is 0, so the
    oldest-protocol branch is taken.
  - Safe: `fuse_adjust_compat()`, which changes only opcodes CUSE does not
    send.
  - Safe: `fuse_read_forget()`, which only picks the forget format; no
    function `fs/fuse/cuse.c` calls reaches `fuse_chan_queue_forget()`.
  - Safe: `fuse_dev_do_read()`, where `fch->max_write` only raises the
    minimum read buffer; with 0 the `nbytes < reqsize` test still ends a
    request that does not fit with `-EIO`.
  - Safe: reading `fc->minor` or `fc->max_write` instead, as
    `fuse_write_args_fill()` and `fuse_direct_io()` do;
    `cuse_process_init_reply()` sets those.
- **Unsafe usage**: a `fuse_notify()` handler that reaches a superblock or
  inode without `fuse_ilookup()`.
  - Safe: look the inode up with `fuse_ilookup()` and use the
    `struct fuse_mount` it returns, as `fuse_epoch_work()` and
    `fuse_notify_retrieve()` do; on CUSE the lookup returns NULL.
- **Potentially unsafe usage**: reading `fm->sb` without a NULL test.
  - Unsafe: when `fm` can be CUSE's `cc->fm`, as in `fs/fuse/req.c` and in
    the functions `fs/fuse/cuse.c` calls; `fm->sb` is NULL there.
  - Safe: test `!fm->sb` first, as `fuse_fill_creds()` does.
  - Safe: when `fm` is the out pointer of `fuse_ilookup()`, which skips a
    mount whose `sb` is NULL, as in `fuse_epoch_work()`.
  - Safe: when `fm` came from `get_fuse_mount()` on a FUSE inode, as in
    `fuse_access()`; `fuse_fill_super_common()` and
    `fuse_fill_super_submount()` set `fm->sb` before they create the root
    inode.

## Model gaps

### Other mistakes models make

- Models take ring commands to need a ring set up with 128-byte entries.
  `io_uring_cmd()` in `io_uring/uring_cmd.c` also sets `IO_URING_F_SQE128`
  for opcode `IORING_OP_URING_CMD128`.
- Models treat `in_args[]` as an unordered list. On the ring path
  `fuse_uring_args_to_ring()` copies `in_args[0]` to the `op_in` header and
  only the rest to the payload; a request with no per-op header calls
  `fuse_set_zero_arg0()` first, as `fuse_lookup_init()` does.
- Models take READDIR to use one page. `fuse_readdir_uncached()` sizes the
  buffer from `ctx->count`, up to `fc->max_pages` pages.
- Models take `fuse_mkdir()` to return int and pass the mode through. It
  returns `struct dentry *` and clears `S_IFDIR` before sending;
  `create_new_entry()` returns the dentry from `d_splice_alias()`.
- Models do not know `fc->no_link` and `fc->no_copy_file_range_64`. After
  `-ENOSYS` `fuse_link()` returns `-EPERM`; `__fuse_copy_file_range()` tries
  `FUSE_COPY_FILE_RANGE_64` first and falls back to `FUSE_COPY_FILE_RANGE`.
- Models take the FUSE iomap ops to supply `.iomap_begin`. `fuse_iomap_ops`
  in `fs/fuse/file.c` sets `.iomap_next`, built with
  `DEFINE_IOMAP_ITER_NEXT()`.
