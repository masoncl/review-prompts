# Bluetooth Subsystem

## Main structures

### Objects and how they relate

- Driver hooks: there is no hci_dev_driver_ops structure; `open`, `close`,
  `send`, `setup` and the rest are function-pointer members of
  `struct hci_dev` itself.
- `struct hci_drv` (`include/net/bluetooth/hci_drv.h`): optional driver
  table of handlers for `HCI_DRV_PKT`; `hci_send_frame()` hands such a
  packet to `hci_drv_process_cmd()` and never to `hdev->send`.
- `struct hci_chan`: the ACL/LE transmit queue of one `struct l2cap_conn`,
  not an AMP leftover; `hci_chan_create()` is called only from
  `l2cap_conn_add()`, and `hci_chan_sent()` schedules from it.
- SCO and ISO data: queued on `data_q` of the `struct hci_conn` itself, with
  no `struct hci_chan`; see `hci_send_sco()` and `hci_send_iso()`.
- `struct hci_request`: the only instance is a local in
  `__hci_cmd_sync_sk()` (`net/bluetooth/hci_sync.c`); there is no
  hci_request.c, and the helpers that fill a request are static in that
  file.
- `struct hci_conn` counts: `hci_conn_hold()` and `hci_conn_drop()` count
  users of the link and do not pin memory; at zero `hci_conn_drop()` queues
  `disc_work`.
- Who holds what on a `struct hci_conn`: `struct l2cap_conn` takes
  `hci_conn_get()` only; each `struct l2cap_chan` takes `hci_conn_hold()` in
  `__l2cap_chan_add()`, a fixed channel only with `FLAG_HOLD_HCI_CONN`.
- `struct sco_conn` and `struct iso_conn`: carry a keep-link-up count
  (`sco_conn_free()` and `iso_conn_free()` call `hci_conn_drop()`) and take no
  `hci_conn_get()`; each serves one socket.
- Link types: ISO is split into `CIS_LINK`, `BIS_LINK` and `PA_LINK`
  (`include/net/bluetooth/hci.h`); a `PA_LINK` conn is a periodic advertising
  sync; there is no generic ISO link type.
- `struct hci_link`: the parent is the ACL for SCO, the LE link for a CIS, and
  another BIS of the same BIG for a BIS (`hci_bind_bis()`).
- Removed channel test: check `FLAG_DEL` under the channel lock, as
  `l2cap_chan_conn()` in `net/bluetooth/l2cap_sock.c` does; `chan->conn` is
  NULL only before `__l2cap_chan_add()`.
- `chan->data` for L2CAP sockets: the `struct sock`; `l2cap_sock_put_chan()`
  sets it to NULL, and `struct l2cap_ops` callbacks in
  `net/bluetooth/l2cap_sock.c` test it, for example `l2cap_sock_recv_cb()`
  and `l2cap_sock_close_cb()`.
- `chan->data` for SMP: `struct smp_chan` on the per-connection channel
  `conn->smp`, and only while pairing runs; `struct smp_dev` on the listening
  channel in `hdev->smp_data`; NULL on `hdev->smp_bredr_data`.
- `chan->data` for 6LoWPAN: the skb being sent (`send_pkt()`); per-channel
  state is `struct lowpan_peer`, found by `__peer_lookup_chan()`.
- RFCOMM, BNEP and HIDP: hold a `struct socket` but reach through
  `l2cap_pi(sk)->chan` to the channel and its `struct l2cap_conn`.
- `struct l2cap_user`: probe and remove pair hung on a `struct l2cap_conn`;
  `l2cap_conn_del()` calls every `remove`; HIDP is the in-tree user.
- CMTP: not implemented in this tree; only `BTPROTO_CMTP` remains.
- HCI socket state: `struct hci_pinfo` in `net/bluetooth/hci_sock.c`; there is
  no hci_sock structure.
- `struct hci_uart`: defined in `drivers/bluetooth/hci_uart.h`; shared by
  `drivers/bluetooth/hci_ldisc.c` and `drivers/bluetooth/hci_serdev.c`.

## Where to look

**Core files:** Files are under `net/bluetooth/` unless a directory is given.

| Job | File | Not where expected |
|---|---|---|
| HCI device core | `hci_core.c` | Also holds `hci_conn_params_add()`, `hci_conn_params_lookup()` and `hci_conn_params_del()`. `hci_send_cmd()` here queues and returns; it does not wait. |
| Queue of synchronous command sequences | `hci_sync.c` | There is no hci_request.c or hci_request.h. `struct hci_request` and `hci_req_sync_lock()` are in `include/net/bluetooth/hci_sync.h`; `hci_req_cmd_complete()` is in `hci_core.c`. The send-and-wait is `__hci_cmd_sync_sk()`, here. |
| Event handling | `hci_event.c` | Sends commands itself: it calls `hci_send_cmd()` directly, far more often than `hci_cmd_sync_queue()`. |
| Connection objects | `hci_conn.c` | `struct hci_conn_params` is in `include/net/bluetooth/hci_core.h`, and the functions declared there for it are in `hci_core.c`. `hci_connect_le_sync()` and `hci_connect_acl_sync()` are in `hci_sync.c`. |
| HCI sockets | `hci_sock.c` | |
| Management interface | `mgmt.c` | The `mgmt_*()` notifiers the core calls, such as `mgmt_device_connected()`, are declared in `include/net/bluetooth/hci_core.h`, not `include/net/bluetooth/mgmt.h`. `struct hci_mgmt_chan` is there too. |
| Management helpers | `mgmt_util.c`, `mgmt_config.c` | `struct mgmt_pending_cmd` is in the private `mgmt_util.h`. |
| L2CAP | `l2cap_core.c` | |
| L2CAP sockets | `l2cap_sock.c` | |
| SMP | `smp.c` | Holds the SMP self tests too, under `CONFIG_BT_SELFTEST_SMP`. |
| SCO | `sco.c` | Built only with `CONFIG_BT_BREDR`; see `Makefile`. |
| ISO | `iso.c` | Built only with `CONFIG_BT_LE`. `bt_init()` in `af_bluetooth.c` does not call `iso_init()`; its only caller is `set_iso_socket_func()` in `mgmt.c`. |
| Vendor extensions | `msft.c`, `aosp.c` | Driver-specific commands have a dispatcher here, not only in `drivers/bluetooth/`: `hci_drv.c` handles `HCI_DRV_PKT` frames, which `hci_send_frame()` in `hci_core.c` hands to `hci_drv_process_cmd()` instead of `hdev->send`. |
| Self tests | `selftest.c` | Holds only the ECDH tests, under `CONFIG_BT_SELFTEST_ECDH`, and `run_selftest()`. `bt_selftest()` is real only when `CONFIG_BT` is a module; built in, `bt_selftest_init()` runs by `late_initcall()`. |
| Public headers | `include/net/bluetooth/` | Includes `hci_drv.h` and `coredump.h`. |

## The controller object

**Flag words and quirks**

- `HCI_UP`, `HCI_INIT`, `HCI_RUNNING`, `HCI_RAW` and the other bits of that
  enum: live in `hdev->flags` only, with no accessor macro that takes a bit
  number; the `dev_flags` enum starts at `HCI_SETUP`.
- Enum order in `include/net/bluetooth/hci.h`: quirks, `flags` bits, socket
  flags, `dev_flags` bits; all four are anonymous and number from 0.
- Socket flags (`HCI_SOCK_TRUSTED`, `HCI_MGMT_INDEX_EVENTS`, ...): belong to
  `hci_sock_set_flag()` and `hci_sock_test_flag()`, not to `struct hci_dev`.
- Membership check: none. The accessors in
  `include/net/bluetooth/hci_core.h` are macros that pass `nr` unchanged to
  `set_bit()`, `test_bit()` and friends; there is no `BUILD_BUG_ON()` and no
  test against `__HCI_NUM_FLAGS` or `__HCI_NUM_QUIRKS`.
- Value reported to user space: `hci_get_dev_info()` and
  `hci_get_dev_list()` clear `HCI_UP` in the copy while `HCI_AUTO_OFF` is
  set, so the reported word is not always `hdev->flags`.
- `hdev->conn_flags`: `hci_conn_flags_t` is `u8`; `enum hci_conn_flags`
  values are already `BIT()` masks, combined with `|` and `&`, never passed
  to a bitop as a bit number.
- **Unsafe usage**: passing a bit of one enum to the accessor of another
  set; it compiles and touches an unrelated bit, because the enums overlap.
  - Safe: `test_bit(HCI_INIT, &hdev->flags)` next to
    `hci_dev_test_flag(hdev, HCI_SETUP)`, as `hci_unregister_dev()` does.
  - Safe: `hci_test_quirk()` with an `HCI_QUIRK_` name, as
    `hci_register_dev()` does.

**Driver quirks**

- `struct hci_dev` has no member named quirks; the bits are in
  `quirk_flags`, a `DECLARE_BITMAP()` of `__HCI_NUM_QUIRKS` bits.
- `hci_set_quirk()`, `hci_clear_quirk()`, `hci_test_quirk()`: macros in
  `include/net/bluetooth/hci_core.h`; no driver in the tree uses a raw bitop
  on `quirk_flags`.
- `DEFINE_QUIRK_ATTRIBUTE()` in `net/bluetooth/hci_debugfs.c`: the one place
  with raw bitops on `quirk_flags`; a debugfs write flips
  `HCI_QUIRK_STRICT_DUPLICATE_FILTER` or `HCI_QUIRK_SIMULTANEOUS_DISCOVERY`,
  and returns `-EBUSY` while `HCI_UP` is set.
- `hci_clear_quirk()`: used by `drivers/bluetooth/btusb.c`, so a quirk set at
  probe can be gone after setup.
- Timing: nothing in the code enforces the "must be set before
  hci_register_dev" comments in `include/net/bluetooth/hci.h`.
- `hci_register_dev()` reads `HCI_QUIRK_RAW_DEVICE` itself and
  `HCI_QUIRK_NO_SUSPEND_NOTIFIER` through `hci_register_suspend_notifier()`;
  setting either from the `setup` callback is too late for those tests.
- `hci_dev_setup_sync()` in `net/bluetooth/hci_sync.c`: tests quirks after
  `hdev->setup()` returns, and `hci_init_sync()` runs after that, so a quirk
  set in `setup` is seen by the init stages.
- `hci_broken_table`: logs only the quirks listed in it; for example
  `HCI_QUIRK_BROKEN_EXT_SCAN` is not listed and is never logged.

**Controller locks**

- Coredump state: there is no devcd_lock; `net/bluetooth/coredump.c` takes
  `hci_dev_lock()`, for example in `hci_devcd_timeout()` and
  `hci_devcd_shutdown()`.
- `dump.supported`: cleared under the spinlock of `dump.dump_q` in
  `hci_devcd_shutdown()`, not under `hdev->lock`.
- `hdev->req_lock`: still serialises every cmd_sync entry;
  `hci_cmd_sync_work()` holds it across `entry->func` and `entry->destroy`.
- `hdev->unregister_lock`: mutex with two users; `hci_unregister_dev()` sets
  `HCI_UNREGISTER` under it, `hci_cmd_sync_submit()` tests the flag and
  queues under it.
- `hdev->mgmt_pending_lock`: mutex for the `mgmt_pending` list; see
  `net/bluetooth/mgmt_util.c`.
- `hci_cb_list_lock`: `DEFINE_MUTEX()` in `net/bluetooth/hci_core.c`.

| Outer | Inner | Seen in |
|---|---|---|
| `req_lock` | `hdev->lock` | `hci_dev_close_sync()` |
| `req_lock` | `mgmt_pending_lock` | `set_powered_sync()` |
| `hdev->lock` | `hci_cb_list_lock` | `hci_conn_hash_flush()` → `hci_disconn_cfm()` |
| `hdev->lock` | `mgmt_pending_lock` | `set_powered()` → `mgmt_pending_add()` |
| `hdev->lock` | `unregister_lock` | `set_powered()` → `hci_cmd_sync_submit()` |
| `unregister_lock` | `cmd_sync_work_lock` | `hci_cmd_sync_submit()` |
| `hdev->lock` | `cmd_sync_work_lock` | `hci_conn_del()` → `hci_cmd_sync_dequeue()` |

**Controller registration and teardown**

- Order in `hci_unregister_dev()`:
  1. set `HCI_UNREGISTER` under `unregister_lock`
  2. `list_del()` under `write_lock(&hci_dev_list_lock)`
  3. `synchronize_srcu()`, then `cleanup_srcu_struct()`
  4. disable the work items, then `hci_devcd_shutdown()`
  5. `hci_cmd_sync_clear()`
  6. `hci_unregister_suspend_notifier()`
  7. `hci_dev_do_close()`
  8. `mgmt_index_removed()` under `hdev->lock`, then the `BUG_ON()`
  9. `hci_sock_dev_event()` with `HCI_DEV_UNREG`
  10. rfkill unregister and destroy
  11. `device_del()`, then `hci_dev_put()`
- Step 3 needs step 2: the only SRCU reader is `hci_dev_reset()`, which finds
  the device through `hci_dev_list` in `hci_dev_get_srcu()`.
- Step 5 needs step 1: `hci_cmd_sync_clear()` only cancels; the flag is what
  makes `hci_cmd_sync_submit()` return `-ENODEV`.
- Step 7 reads the flag from step 1: `hci_dev_shutdown()` skips the driver's
  `shutdown` callback, and `hci_dev_close_sync()` disables rather than
  cancels `power_off`, `ncmd_timer` and `le_scan_disable`.
- `hci_dev_close_sync()` returns before `hdev->close()` when `HCI_UP` was
  already clear, so unregistering a powered-off controller does not call
  the driver's `close`.
- Step 8 condition: `HCI_INIT`, `HCI_SETUP` and `HCI_CONFIG` all clear; user
  channel is not tested, and the `HCI_QUIRK_RAW_DEVICE` test is inside
  `mgmt_index_removed()`.
- There is no hci_del_dev_sysfs here; `hci_unregister_dev()` calls
  `device_del()` directly.
- `hci_unregister_dev()` does not remove debugfs, destroy the workqueues or
  free the index; `hci_release_dev()` does that and clears the stored lists.
- Final `hci_dev_put()`: drops the `hci_dev_hold()` taken in
  `hci_register_dev()`; the allocation reference from `device_initialize()`
  in `hci_init_sysfs()` is dropped by `hci_free_dev()`.
- `bt_host_release()` in `net/bluetooth/hci_sysfs.c`: runs on the last
  `put_device()`; with `HCI_UNREGISTER` set it calls `hci_release_dev()`,
  which ends in `kfree(hdev)`.
- `bt_host_release()` with `HCI_UNREGISTER` clear: calls
  `cleanup_srcu_struct()` and `kfree(hdev)` instead of `hci_release_dev()`;
  this is the path of a device that was never unregistered.

**Stopping controller work items**

| Where | Call | Work items | Later queue attempt |
|---|---|---|---|
| `hci_unregister_dev()` | `disable_work_sync()` | `rx_work`, `cmd_work`, `tx_work`, `power_on`, `error_reset` | refused |
| `hci_unregister_dev()` | `disable_delayed_work_sync()` | `cmd_timer`, `ncmd_timer` | refused |
| `hci_devcd_shutdown()` | `disable_work_sync()`, `disable_delayed_work_sync()` | `dump_rx`, `dump_timeout` of `struct hci_devcoredump` | refused |
| `hci_cmd_sync_clear()` | `cancel_work_sync()` | `cmd_sync_work`, `reenable_adv_work` | allowed |
| `hci_dev_close_sync()`, `HCI_UNREGISTER` set | `disable_delayed_work()` | `power_off`, `ncmd_timer`, `le_scan_disable` | refused; a running instance is not waited for |
| `mgmt_index_removed()`, `HCI_MGMT` set | `cancel_delayed_work_sync()` | `discov_off`, `service_cache`, `rpa_expired`, `mesh_send_done` | allowed |

- `hci_unregister_dev()` uses no `cancel_work_sync()` of its own; the
  cancels on this path are inside its callees, for example
  `hci_cmd_sync_clear()`, `hci_dev_close_sync()` and `mgmt_index_removed()`.
- `hci_devcd_shutdown()`: an empty stub without `CONFIG_DEV_COREDUMP`; see
  `include/net/bluetooth/coredump.h`.
- Refused means: `queue_work()`, `queue_delayed_work()` and
  `mod_delayed_work()` queue nothing; see `clear_pending_if_disabled()` in
  `kernel/workqueue.c`.
- Nothing calls `enable_work()` on a work item of `struct hci_dev`, so the
  disable lasts until the object is freed.
- `hci_recv_frame()` ignores the result of `queue_work()`: after the
  disable it still returns 0 while `HCI_UP` or `HCI_INIT` is set, and the
  skb waits on `rx_q` for the purge in `hci_dev_close_sync()`.
- `hci_cancel_cmd_sync()` in `net/bluetooth/hci_core.c` picks disable or
  cancel for `cmd_timer` and `ncmd_timer` by the same `HCI_UNREGISTER` test.

**Driver callbacks and frame ownership**

- `send` is not called in two cases, and the core frees the skb in both:
  `HCI_RUNNING` clear (returns `-EINVAL`), and packet type `HCI_DRV_PKT`,
  which goes to `hci_drv_process_cmd()`.
- `hci_recv_frame()` does not call `skb_orphan()`; it sets
  `bt_cb(skb)->incoming` and the timestamp. `skb_orphan()` is in
  `hci_send_frame()`.
- Accepted by `hci_recv_frame()`: `HCI_EVENT_PKT`, `HCI_ACLDATA_PKT`,
  `HCI_SCODATA_PKT`, `HCI_ISODATA_PKT`, `HCI_DRV_PKT`.
- The type tested is the one returned by the driver's `classify_pkt_type`
  callback, when the driver sets one; a callback that returns
  `HCI_DIAG_PKT` or `HCI_VENDOR_PKT` gets the frame freed with `-EINVAL`,
  not delivered as a diagnostic frame.
- `-ENXIO` test runs first: a frame of an unaccepted type on a controller
  that is neither `HCI_UP` nor `HCI_INIT` returns `-ENXIO`, not `-EINVAL`.
- **Potentially unsafe usage**: `kfree_skb()` after `hci_recv_frame()`
  returned an error.
  - Unsafe: on the skb that was passed in; `hci_recv_frame()` already freed
    it on both error paths.
  - Safe: on a separate clone made before the call, as
    `btmtk_usb_wmt_recv()` in `drivers/bluetooth/btmtk.c` frees
    `data->evt_skb`.

## Synchronous command queue

**Queueing interface**

| Function | Refuses when | Returns | Duplicate queued | Calls `func` directly |
|---|---|---|---|---|
| `hci_cmd_sync_submit()` | `HCI_UNREGISTER` set | `-ENODEV` | not checked | never |
| `hci_cmd_sync_queue()` | `HCI_RUNNING` clear | `-ENETDOWN` | not checked | never |
| `hci_cmd_sync_queue_once()` | `HCI_RUNNING` clear | `-ENETDOWN` | `-EEXIST` | never |
| `hci_cmd_sync_run()` | `HCI_RUNNING` clear | `-ENETDOWN` | not checked | when called on `hdev->cmd_sync_work` |
| `hci_cmd_sync_run_once()` | `HCI_RUNNING` clear | `-ENETDOWN` | `-EEXIST` | when called on `hdev->cmd_sync_work` |

- `HCI_RUNNING` is tested in `hdev->flags`, not `HCI_UP`; it is set in
  `hci_dev_open_sync()` before init, so entries are accepted during init.
- `hci_cmd_sync_submit()` makes no `HCI_RUNNING` or `HCI_UP` test and never
  calls `func`; the other four call `hci_cmd_sync_submit()` when they queue
  and can then also return `-ENODEV` or `-ENOMEM`.
- `hci_cmd_sync_run()` direct path: calls `func`, then `destroy` with the
  result of `func`, and returns 0; the caller never sees the error of `func`.
- `_once` variants: the lookup runs before the `HCI_RUNNING` test, so a
  duplicate gives `-EEXIST` even when the device is not running.
- `_once` duplicate key: `func`, `data` and `destroy` as passed; a NULL
  argument matches any value.
- `_once` variants do not see an entry that `hci_cmd_sync_work()` has already
  unlinked to run, and the lookup and the add are separate sections of
  `hdev->cmd_sync_work_lock`; a second entry can still be queued.

**Removing queued entries**

- Match key: `func`, `data` and `destroy`; each NULL argument is a wildcard;
  see `_hci_cmd_sync_lookup_entry()` in `net/bluetooth/hci_sync.c`.
- `hci_cmd_sync_lookup_entry()`: takes and drops `hdev->cmd_sync_work_lock`
  itself; in-tree callers use the result only as a boolean.
- There is no hci_cmd_sync_dequeue_once() here; code that removes one entry
  takes `hdev->cmd_sync_work_lock` and calls `_hci_cmd_sync_lookup_entry()`
  and `_hci_cmd_sync_cancel_entry()` itself.
- `_hci_cmd_sync_lookup_entry()` and `_hci_cmd_sync_cancel_entry()`: take no
  lock and assert none; the caller holds `hdev->cmd_sync_work_lock`.
- `hci_cancel_connect_sync()`: switches on `conn->type`; it does not test
  `conn->state`, and `hdev->req_status` is tested only inside
  `hci_cmd_sync_cancel()`, after the flag test.

| `conn->type` | Create in flight | Entry still queued | Neither |
|---|---|---|---|
| `ACL_LINK`, `LE_LINK` | `HCI_CONN_CREATE` set: `hci_cmd_sync_cancel()`, returns `-EBUSY` | entry cancelled with `-ECANCELED`, returns 0 | `-EBUSY` |
| `CIS_LINK` | `HCI_CONN_CREATE_CIS` set: `hci_cmd_sync_cancel()`, returns `-EBUSY` | never dequeued, `-EBUSY` | `-EBUSY` |
| other | `-ENOENT` | `-ENOENT` | `-ENOENT` |

- `HCI_CONN_CREATE`: set by `hci_acl_create_conn_sync()` and
  `hci_le_create_conn_sync()` just before the create command, cleared after
  it; the test and the cancel are under `hdev->cmd_sync_work_lock`.
- **Unsafe usage**: passing the pointer from `hci_cmd_sync_lookup_entry()` to
  `hci_cmd_sync_cancel_entry()` or dereferencing it; `hci_cmd_sync_work()` can
  unlink and `kfree()` the entry once the lock is dropped.
  - Safe: look up and cancel in one `hdev->cmd_sync_work_lock` section, as
    `hci_cmd_sync_dequeue()` does.

**Completion callback contract**

| Path that ends the entry | `err` given to `destroy` | Locks held |
|---|---|---|
| `hci_cmd_sync_work()` ran `func` | return value of `func` | `hdev->req_lock` |
| `hci_cmd_sync_run()` direct call | return value of `func` | `hdev->req_lock`, plus the caller's |
| `hci_cmd_sync_dequeue()`, `hci_cmd_sync_cancel_entry()`, `hci_cancel_connect_sync()` | `-ECANCELED` | `hdev->cmd_sync_work_lock`, plus the caller's |
| `hci_cmd_sync_clear()` | `-ECANCELED` | `hdev->cmd_sync_work_lock` |

- `hci_cmd_sync_clear()`: called only from `hci_unregister_dev()`;
  `hci_dev_close_sync()` does not call it.
- Caller's locks on the dequeue path: `hdev->lock` when `hci_conn_del()` is
  called under it, as in `hci_abort_conn_sync()`; `hdev->mgmt_pending_lock`
  when `cmd_complete_rsp()` in `net/bluetooth/mgmt.c` dequeues from inside
  `mgmt_pending_foreach()`.
- `_hci_cmd_sync_cancel_entry()`: calls `destroy` before it unlinks the entry.
- `hci_cmd_sync_run()` returning 0: `destroy` may already have run, so the
  caller no longer owns what it passed as `data`.
- No `destroy` call: when the queueing function returns `-ENODEV`, `-ENOMEM`,
  `-ENETDOWN` or `-EEXIST`; the caller frees `data` or drops its reference,
  as `hci_connect_acl_sync()` does with `hci_conn_put()`.
- **Potentially unsafe usage**: a `destroy` callback that, on `-ECANCELED`,
  takes `hci_dev_lock()` or `hdev->mgmt_pending_lock`, or calls a queueing
  function.
  - Unsafe: when `data` is a `struct hci_conn` or a listed
    `struct mgmt_pending_cmd`; `hci_conn_del()` dequeues under `hdev->lock`,
    `cmd_complete_rsp()` under `hdev->mgmt_pending_lock`, and both under
    `hdev->cmd_sync_work_lock`, which `hci_cmd_sync_submit()` and
    `hci_cmd_sync_lookup_entry()` take.
  - Safe: test `err == -ECANCELED` first and only release the data, as
    `create_le_conn_complete()` does.
  - Safe: `hci_cmd_sync_queue()` from the `destroy` of an entry whose `data`
    is NULL, as `mesh_next()` in `net/bluetooth/mgmt.c`; only
    `hci_cmd_sync_clear()` cancels such an entry, and with `HCI_UNREGISTER`
    set `hci_cmd_sync_submit()` returns before it takes
    `hdev->cmd_sync_work_lock`.

**Return values of synchronous sends**

- Controller error status: `__hci_cmd_sync_sk()` returns
  `ERR_PTR(-bt_to_errno(hdev->req_result))`; `bt_to_errno()` returns a
  positive errno.
- `__hci_cmd_sync_status()` and `hci_cmd_sync_status()` on success: return
  `skb->data[0]` unchanged, so the result can be a positive HCI status; test
  for non-zero, not for negative.
- `mgmt_status()` and `bt_status()`: accept both a negative errno and a
  positive HCI status.
- `hci_cmd_sync_cancel()`: stores `err` unchanged in `hdev->req_result`, and
  `__hci_cmd_sync_sk()` negates it; pass a positive errno, as
  `hci_cmd_sync_cancel(hdev, ECANCELED)` in `net/bluetooth/hci_sync.c`.
- `hci_cmd_sync_cancel()` with a negative errno: the waiter gets
  `ERR_PTR(-ENODATA)`, which the status variants return as 0.
- `hci_cmd_sync_cancel_sync()`: accepts either sign and stores the positive
  value.

**Device lock around synchronous functions**

- Comment in `include/net/bluetooth/hci_sync.h`: says functions with the sync
  suffix shall not be called with `hdev->lock` held; it states no exception.
- `hci_event_packet()` in `net/bluetooth/hci_event.c`: takes and drops
  `hci_dev_lock()` for every event before it dispatches, and again before it
  completes the request, so no reply is delivered while the sender holds
  `hdev->lock`, whatever the handler does.
- Callbacks that copy under `hci_dev_lock()` and unlock before sending:
  `hci_le_conn_rate_request_sync()` in `net/bluetooth/hci_sync.c`,
  `le_conn_update_sync()` in `net/bluetooth/hci_conn.c`, `conn_update_sync()`
  in `net/bluetooth/mgmt.c`.
- `le_conn_update_sync()`: retakes `hci_dev_lock()` after the command returns
  and looks the parameters up under it before it writes them.
- **Potentially unsafe usage**: calling `hci_cmd_sync_run()`,
  `hci_cmd_sync_run_once()` or `hci_abort_conn()` with `hci_dev_lock()` held.
  - Unsafe: when the caller runs on `hdev->cmd_sync_work`; `func` then runs in
    the caller and sends commands under `hdev->lock`.
  - Safe: when the caller is not on `hdev->cmd_sync_work`, so the
    `current_work()` test in `hci_cmd_sync_run()` fails and the entry is only
    queued, as `cancel_pair_device()` in `net/bluetooth/mgmt.c`.
  - Safe: on `hdev->cmd_sync_work`, take a reference under the lock and unlock
    before the call, as `disconnect_sync()` in `net/bluetooth/mgmt.c` does.

**Object pointers as callback data**

- `hci_conn_valid()`: tells whether `hci_conn_del()` has removed the
  connection from `hdev->conn_hash`; it does not keep the memory alive, the
  reference does.
- `hci_conn_del()`: calls `hci_cmd_sync_dequeue()` as its last step, after
  `hci_conn_hash_del()`, so a callback that starts later sees
  `hci_conn_valid()` fail.
- **Potentially unsafe usage**: dereferencing `conn` in a queued callback after
  `hci_conn_valid()` returned true.
  - Unsafe: when the entry holds no reference; `hci_conn_valid()` compares
    addresses only and `bt_link_release()` in `net/bluetooth/hci_sysfs.c`
    frees the object on the last `put_device()`.
  - Safe: when the entry took `hci_conn_get()` and `destroy` drops it, as
    `hci_connect_acl_sync()` with `hci_acl_create_conn_sync_complete()`.
  - Safe: for fields that `hdev->lock` protects, check and copy under
    `hci_dev_lock()`, as `hci_le_conn_rate_request_sync()` does.
- `mgmt_pending_remove()` and `mgmt_pending_free()`: do not dequeue.
- `cmd_complete_rsp()` in `net/bluetooth/mgmt.c`: calls
  `hci_cmd_sync_dequeue(match->hdev, NULL, cmd, NULL)`; it runs from
  `mgmt_index_removed()` and `__mgmt_power_off()` through
  `mgmt_pending_foreach()`.
- Other `mgmt_pending_foreach()` callbacks that remove, for example
  `settings_rsp()`: do not dequeue, so the queued callback must still
  validate.
- Validity helpers in `net/bluetooth/mgmt_util.c`:

| Helper | Lock | Effect |
|---|---|---|
| `mgmt_pending_valid()` | takes `hdev->mgmt_pending_lock` | unlinks if listed; caller then frees with `mgmt_pending_free()` |
| `mgmt_pending_listed()` | takes `hdev->mgmt_pending_lock` | tests only; stale once it returns |
| `__mgmt_pending_listed()` | asserts `hdev->mgmt_pending_lock` | tests only |

- Command from `mgmt_pending_new()`: never listed, so `mgmt_pending_valid()`
  returns false for it; `destroy` frees it for every `err`, as
  `disconnect_complete()` does.

## Connection objects

**Connection creation and deletion**

- `HCI_CONN_HANDLE_UNSET()`: a predicate (`handle > HCI_CONN_HANDLE_MAX`), not
  a value; each conn from `hci_conn_add_unset()` has its own placeholder from
  `hdev->unset_handle_ida`.
- `hci_conn_hash_lookup_handle()`: also finds a conn by its placeholder;
  `hci_abort_conn_sync()` depends on that.
- `hci_conn_del()` sleeps (`disable_delayed_work_sync()`,
  `synchronize_rcu()`); it cannot run inside `rcu_read_lock()` or under a
  spinlock.
- `le_conn_timeout`: only `cancel_delayed_work()`, only for `LE_LINK`; a
  running `le_conn_timeout()` is not waited for, and for `HCI_ROLE_SLAVE` it
  takes `hci_dev_lock()`.
- `hci_conn_unlink()` is the first step of `hci_conn_del()`; on a parent it
  unlinks every child, and with `HCI_UP` set it can delete children too,
  through `hci_conn_cleanup_child()` -> `hci_conn_failed()`, for example a SCO
  child whose handle is still unset.
- **Potentially unsafe usage**: calling `hci_conn_del()` while iterating
  `hdev->conn_hash.list`.
  - Unsafe: when a deleted entry can be a parent in `hci_conn_link()`; the
    child it deletes may be the saved next entry.
  - Safe: re-read the first entry each round, as `hci_conn_hash_flush()` does.
  - Safe: delete only `CIS_LINK` entries, as `hci_unbound_cis_failed()` does;
    no `hci_conn_link()` caller passes a CIS as parent.
- Initial reference: dropped in `hci_conn_del_sysfs()` (`put_device()` or
  `device_unregister()`), not by `hci_conn_put()`; without another
  `hci_conn_get()` reference `bt_link_release()` frees the conn before
  `hci_conn_del()` returns.
- RCU: `hci_conn_hash_del()` runs `synchronize_rcu()` before that reference is
  dropped, so `hci_conn_get()` on an entry found inside `rcu_read_lock()` is
  safe, as in `hci_disconnect_all_sync()`.
- Lookup helpers return the pointer after `rcu_read_unlock()` with no
  reference; it stays valid only while the caller holds `hdev->lock`.
- `hci_cmd_sync_dequeue(hdev, NULL, conn, NULL)`: removes only queued entries
  whose `data` is the conn itself, calling their destroy with `-ECANCELED`.
- Entries that wrap the conn stay queued, for example
  `struct le_conn_update_data`; that entry holds `hci_conn_get()`, and
  `le_conn_update_sync()` tests `hci_conn_valid()` under `hdev->lock`.
- `hci_conn_del()` calls neither `hci_disconn_cfm()` nor `hci_connect_cfm()`
  for the conn it deletes; a caller whose conn the upper layers may know does
  so first, as `hci_conn_hash_flush()` and `hci_conn_failed()` do.

**Handle assignment**

- Return type is `u8`, an HCI status; no negative errno.
- Checks, in order:

| Check | Return |
|---|---|
| `conn->handle == handle` | 0, before any other test |
| `handle > HCI_CONN_HANDLE_MAX` | `HCI_ERROR_INVALID_PARAMETERS` |
| `conn->abort_reason` non-zero | `conn->abort_reason` |

- No "handle already set" test and no link-type test in
  `hci_conn_set_handle()`; `hci_conn_complete_evt()`,
  `hci_sync_conn_complete_evt()` and `le_conn_complete_evt()` do
  `!HCI_CONN_HANDLE_UNSET(conn->handle)` themselves before calling it.
- No debugfs or sysfs work inside; the caller runs
  `hci_debugfs_create_conn()` and `hci_conn_add_sysfs()` itself after a 0
  return, for example `hci_conn_complete_evt()`;
  `hci_cc_le_set_cig_params()` runs neither.
- Non-zero return is not always used as the event status:
  `hci_cc_le_set_cig_params()` skips that conn;
  `hci_le_create_big_complete_evt()` forces `HCI_ERROR_UNSPECIFIED` and
  deletes it.

**Connection reference counts**

- Last `hci_conn_drop()` delay: `conn->disc_timeout` only for `ACL_LINK` or
  `LE_LINK` in `BT_CONNECTED`, doubled when `!conn->out`; 0 in every other
  state, `BT_CONNECT` included.
- `hci_conn_hold()`: cancels `disc_work` with `cancel_delayed_work()`; a
  `hci_conn_timeout()` already running is not stopped, and it reads `refcnt`
  once at entry.
- Last `hci_conn_drop()` after `hci_conn_del()`: queues nothing, since
  `disc_work` was disabled; it still dereferences the conn, so the caller
  needs a `hci_conn_get()` reference.
- Failed queueing: release with `hci_conn_put()`; see `hci_abort_conn()`,
  `hci_connect_le_sync()`, `hci_le_conn_update()`.
- `-EEXIST` from `hci_cmd_sync_queue_once()` or `hci_cmd_sync_run_once()`:
  also needs the `hci_conn_put()`, though the caller then returns 0.
- Successful queueing: the destroy callback owns the `hci_conn_put()`; it also
  runs with `-ECANCELED` when the entry is dequeued.

**Aborting a connection**

- Second abort: `conn->abort_reason` non-zero -> return 0, nothing done; there
  is no HCI_CONN_ABORT_REQ flag. `-EEXIST` from `hci_cmd_sync_run_once()` is
  also turned into 0.
- `hci_abort_conn()` tests neither `conn->state` nor the sent command;
  `hci_cancel_connect_sync()` in `net/bluetooth/hci_sync.c` decides by link
  type, under `hdev->cmd_sync_work_lock`:

| Case | Action | Result |
|---|---|---|
| ACL/LE, `HCI_CONN_CREATE` set | `hci_cmd_sync_cancel()` | abort queued |
| ACL/LE, create entry still queued | entry cancelled | return 0 |
| CIS, `HCI_CONN_CREATE_CIS` set | `hci_cmd_sync_cancel()` | abort queued, or run inline on `cmd_sync_work` |
| anything else | none | abort queued, or run inline on `cmd_sync_work` |

- Still-queued case: `hci_abort_conn()` returns 0 without queueing
  `abort_conn_sync()` and without deleting the conn; the destroy callbacks
  only `hci_conn_put()` on `-ECANCELED`.
- Return of `hci_abort_conn()`: 0, or the queueing error (`-ENETDOWN`,
  `-ENODEV`, `-ENOMEM`); never the result of the HCI command.
- `hci_abort_conn_sync()` by `conn->state`:

| State | Command | If conn still in hash afterwards |
|---|---|---|
| `BT_CONNECTED`, `BT_CONFIG` | `hci_disconnect_sync()` | `hci_conn_failed()` |
| `BT_CONNECT` | `hci_connect_cancel_sync()` | `hci_conn_failed()` |
| `BT_CONNECT2` | `hci_reject_conn_sync()` | `hci_conn_failed()` |
| `BT_OPEN`, `BT_BOUND` | none | `hci_conn_failed()` |
| other | none | `BT_CLOSED`, `hci_disconn_cfm()`, `hci_conn_del()` |

- Own deletion does not depend on the command result: after the command it
  takes `hdev->lock` and deletes whenever
  `hci_conn_hash_lookup_handle()` on the handle saved at entry still returns
  this conn; otherwise it returns 0.
- `hci_conn_failed()` on that path notifies with `hci_connect_cfm()`, not
  `hci_disconn_cfm()`, even for `BT_CONNECTED`.
- `BIS_LINK` and `PA_LINK` in `hci_disconnect_sync()`: no command; it calls
  `hci_conn_failed()` under `hdev->lock` and returns 0.
- `hci_abort_conn_sync()` return: can be a positive HCI status (`reason` while
  `HCI_CONN_SCANNING`, `HCI_ERROR_LOCAL_HOST_TERM` for a CIS with no Create
  CIS sent).

**Protocol data and callbacks**

- Pointer lock: the spinlock `proto_lock` in `struct hci_conn`, not
  `hdev->lock` alone.

| Pointer | Annotation | Write | Read |
|---|---|---|---|
| `l2cap_data` | `__guarded_by(&proto_lock, &hdev->lock)` | both locks | either |
| `iso_data` | `__guarded_by(&proto_lock)` | `proto_lock` | `proto_lock` |
| `sco_data` | none | no `proto_lock` use | under `hdev->lock` |

- `__guarded_by()` is compiler-checked only with
  `CONFIG_WARN_CONTEXT_ANALYSIS`; `net/bluetooth/Makefile` sets
  `CONTEXT_ANALYSIS := y`.
- `l2cap_disconn_ind()`: reads `l2cap_data` under `proto_lock` only; it runs
  from `hci_conn_timeout()` without `hdev->lock`.
- `smp_conn_security()`: reads `l2cap_data` through `context_unsafe()`; its
  caller must exclude `l2cap_conn_del()`.
- `iso_data`: cleared by `iso_conn_del()` under `hdev->lock`, and by
  `iso_conn_free()` on the last `iso_conn_put()`, with or without
  `hdev->lock`; `iso_conn_free()` clears it only if it still points at that
  `struct iso_conn`.
- `sco_data`: cleared by `sco_conn_free()`, not by `sco_conn_del()`.
- `struct hci_cb`: five callbacks only (`connect_cfm`, `disconn_cfm`,
  `security_cfm`, `key_change_cfm`, `role_switch_cfm`); no filter member; the
  `connect_cfm` and `disconn_cfm` implementations test `hcon->type`
  themselves, `l2cap_security_cfm()` and `rfcomm_security_cfm()` do not.
- `hci_cb_list`: walked under the mutex `hci_cb_list_lock`, not RCU.
- `hci_auth_cfm()`: calls nothing while `HCI_CONN_ENCRYPT_PEND` is set.
- `hci_encrypt_cfm()` in `BT_CONFIG`: calls `hci_connect_cfm()` and
  `hci_conn_drop()` instead of `security_cfm`.
- **Unsafe usage**: after `release_sock()`, `hci_dev_lock()`, `lock_sock()`,
  acting on socket state or a conn pointer read before the release.
  - Safe: recheck `sk->sk_state` is still `BT_OPEN` or `BT_BOUND`, as
    `sco_connect()` does (`-EBADFD`); `sco_chan_add()` then rejects a socket
    or conn already attached (`-EBUSY`).
  - Safe: recheck `iso_pi(sk)->conn` and its `hcon` (`-ENOTCONN`):
    `iso_sock_rebind_bc()` tests that `hcon` is unchanged,
    `iso_conn_big_sync()` that it is non-NULL; `iso_conn_del()` clears both.
  - Safe: recheck `sk->sk_state` before restoring a state set earlier, as
    `iso_sock_recvmsg()` does around `iso_conn_big_sync()`.

## Event handling

**Event dispatch tables**

- `hci_event_packet()`: before it calls `hci_event_func()` it checks only
  that `skb->len` is at least `sizeof(struct hci_event_hdr)` and that
  `hdr->evt` is not 0; it does not read `hdr->plen`.
- `skb->len > max_len`: `hci_event_func()` only warns and still calls the
  handler; `hci_le_meta_evt()` and `hci_cc_func()` do the same.
- Pull before the handler runs: exactly `min_len` bytes; the handler gets
  both `data` (the fixed part) and `skb`, which now starts at the first byte
  after `min_len`.
- `max_len` of variable-length entries: an argument of the macro, not fixed
  by it; `hci_ev_table[]` entries pass `HCI_MAX_EVENT_PLEN` (255),
  `hci_le_ev_table[]` and `hci_cc_table[]` entries pass
  `HCI_MAX_EVENT_SIZE` (260).
- Entries with `req` set: three, not two; `hci_le_meta_evt()` is registered
  with `HCI_EV_REQ_VL()` alongside `hci_cmd_complete_evt()` and
  `hci_cmd_status_evt()`.
- Handler signatures differ by table:

| Table | Handler takes | Returns |
|---|---|---|
| `hci_ev_table[]`, `req` clear | `(hdev, data, skb)` | nothing |
| `hci_ev_table[]`, `req` set | the same plus `opcode`, `status`, `req_complete`, `req_complete_skb` | nothing |
| `hci_le_ev_table[]` | `(hdev, data, skb)` | nothing |
| `hci_cc_table[]` | `(hdev, data, skb)` | `u8` status |
| `hci_cs_table[]` | `(hdev, status)` | nothing |

- `hci_cc_table[]` handler return value: `hci_cmd_complete_evt()` stores it
  in `*status`, so it is the status the pending request completes with, not
  only a log value.
- `HCI_EV_VENDOR`: registered with `min_len` 0, so `hci_vendor_evt()` runs
  with nothing validated or pulled.

**Connection lookup in handlers**

- There is no hci_conn_hash_lookup_state() here; the helpers in
  `include/net/bluetooth/hci_core.h` that take a state argument are
  `hci_conn_hash_lookup_big_state()` (`BIS_LINK` only) and
  `hci_conn_hash_list_state()`, which calls a callback for each match;
  `hci_lookup_le_connect()` has `BT_CONNECT` built in.
- `hci_event_func()`: calls the handler without `hdev->lock`;
  `hci_event_packet()` takes it only around the `hdev->recv_event` clone and
  around `hci_store_wake_reason()`, so a new handler must take
  `hci_dev_lock()` itself before a lookup.
- Helpers that look up without locking, for example `cs_le_create_conn()`:
  rely on the caller's `hci_dev_lock()`.
- `hci_conn_hold()`: increments `conn->refcnt` and cancels `disc_work`;
  `hci_conn_del()` deletes whatever `conn->refcnt` is, so a hold does not
  keep the pointer usable after `hci_dev_unlock()`.
- `hci_conn_get()`: pins the memory only; code that runs later checks
  `hci_conn_valid()` before it acts on the connection, as
  `create_big_complete()` in `net/bluetooth/hci_conn.c` does under
  `hdev->lock`; a callback that only calls `hci_conn_drop()` and
  `hci_conn_put()` makes no check, as `le_read_features_complete()` in
  `net/bluetooth/hci_sync.c`.
- Cmd_sync entry that carries the conn, queued from a handler: the queue
  site takes `hci_conn_get()`, for example `hci_le_conn_rate_request()`;
  `hci_le_read_remote_features()` in `net/bluetooth/hci_sync.c` also takes
  `hci_conn_hold()`, with `hci_conn_hold(hci_conn_get(conn))`.
- `hci_conn_failed()`: ends in `hci_conn_del()`; after either call the
  pointer is dead even though the handler still holds `hdev->lock`.
- `hci_conn_hash_lookup_handle()`: compares the full 16-bit value with no
  range check; a connection from `hci_conn_add_unset()` carries a placeholder
  above `HCI_CONN_HANDLE_MAX` until `hci_conn_set_handle()` replaces it.
- Connection-complete handlers (`hci_conn_complete_evt()`,
  `hci_sync_conn_complete_evt()`, `le_conn_complete_evt()`): look up by
  address (`hci_conn_hash_lookup_ba()`, `hci_conn_hash_lookup_role()`), not by
  the handle in the event.
- Lookup helpers return the first match only; a
  `while ((conn = lookup(...)))` loop ends only if each pass deletes the
  match or changes the field matched, as `hci_le_big_sync_lost_evt()` does
  with `hci_conn_del()`.

**Parsing variable-length events**

- **Potentially unsafe usage**: indexing a counted array, or reading a
  trailing block, that lies beyond the `min_len` the dispatcher pulled.
  - Unsafe: when nothing has compared the count times the element size, or
    the block length, with `skb->len`; the read runs past the end of the skb.
  - Safe: after pulling the whole array, as `hci_num_comp_pkts_evt()` does
    with `hci_ev_skb_pull()` and
    `flex_array_size(ev, handles, ev->num)`; indexing `ev->handles[i]` is
    then correct. `skb_pull_data()` returns NULL when `skb->len` is short.
  - Safe: after comparing `skb->len` with the array size without a pull, as
    `hci_cc_le_read_conn_interval()` does with `flex_array_size()` and
    `hci_cc_le_set_cig_params()` does with `array_size()`.
- **Potentially unsafe usage**: calling `hci_proto_connect_ind()` for an
  event whose trailing data `iso_connect_ind()` reads.
  - Unsafe: when the handler has not checked the trailing length against the
    skb first; `hci_recv_event_data()` returns a pointer into
    `hdev->recv_event` with no length check, and `iso_connect_ind()` in
    `net/bluetooth/iso.c` copies `ev3->length` bytes from it.
  - Safe: after pulling `ev->length`, as `hci_le_per_adv_report_evt()` does
    before the call.
- Count field of `struct hci_ev_num_comp_pkts` and
  `struct hci_ev_le_ext_adv_report`: `num`; `hci_le_adv_report_evt()` and
  `hci_le_ext_adv_report_evt()` loop with `while (ev->num--)`.
- `hci_le_ext_adv_report_evt()`: has no length-limit check of its own;
  `process_adv_report()` drops a report with `len > max_adv_len(hdev)`.
- There is no hci_le_past_report_evt() here; `hci_le_past_received_evt()` is
  a fixed-length entry, and `hci_le_per_adv_report_evt()` is a handler with
  a trailing data block.
- `__counted_by()` in `include/net/bluetooth/hci.h`: only on command
  structs, for example `struct hci_cp_le_set_cig_params`; the event structs'
  flexible arrays are not annotated, so no compiler bound backs the
  handler's own check.
- `hci_le_big_sync_established_evt()`: uses `ev->num_bis` to size its pull,
  to match `conn->num_bis` in `hci_conn_hash_lookup_big_sync_pend()` and to
  bound its loops over `ev->bis[]`; the `ISO_MAX_NUM_BIS` bound is checked in
  `hci_conn_big_create_sync()`, on the command side.

## Management commands

**Command table and length checks**

- Header tests in `hci_mgmt_cmd()` (`net/bluetooth/hci_sock.c`): a short
  header, or `hdr->len` not equal to the payload length, returns `-EINVAL`
  to `sendmsg()` and sends no status event.
- `HCI_MGMT` is not tested by `hci_mgmt_cmd()`; the device-state tests are
  `HCI_SETUP`, `HCI_CONFIG`, `HCI_USER_CHANNEL` and `HCI_UNCONFIGURED` only.
- `HCI_MGMT_HDEV_OPTIONAL`: skips only the test that the presence of `hdev`
  matches `HCI_MGMT_NO_HDEV`.
- With `HCI_MGMT_HDEV_OPTIONAL` and an index other than `MGMT_INDEX_NONE`:
  the lookup and the device-state tests still run, so a bad index still
  gets `MGMT_STATUS_INVALID_INDEX`.
- Handler of an `HCI_MGMT_HDEV_OPTIONAL` entry: must accept `hdev == NULL`.
- `mgmt_event()` and `mgmt_event_skb()` in `net/bluetooth/mgmt.c`: take no
  flag and always send with `HCI_SOCK_TRUSTED`.
- `mgmt_limited_event()` and `mgmt_index_event()`: take the socket flag as
  an argument; these are the ones that can reach a socket that is not
  trusted.
- Delivery of a limited event: `__hci_send_to_channel()` skips every socket
  that lacks the flag, so a new flag reaches no socket until code sets it.
- Flags set at bind: `hci_sock_bind()` sets six event flags, for example
  `HCI_MGMT_INDEX_EVENTS` and `HCI_MGMT_SETTING_EVENTS`, on every
  `HCI_CHANNEL_CONTROL` socket, trusted or not.
- Other event flags: set on the calling socket by a command handler or its
  completion callback, for example `read_ext_controller_info()` sets
  `HCI_MGMT_EXT_INFO_EVENTS` and clears two of the bind-time flags.
- `mgmt_commands[]`, `mgmt_events[]`, `mgmt_untrusted_commands[]` and
  `mgmt_untrusted_events[]`: maintained by hand; `read_commands()` copies
  them verbatim and nothing checks them against `mgmt_handlers`.
- `MGMT_OP_READ_VERSION` and `MGMT_OP_READ_COMMANDS`: have
  `HCI_MGMT_UNTRUSTED` in `mgmt_handlers` and are in neither command array.

**Pending command helpers**

- Lock: the mutex `hdev->mgmt_pending_lock`; `hci_dev_lock()` does not
  cover the list.

| Function | Lock | List and free |
|---|---|---|
| `mgmt_pending_add()` | takes the mutex | adds at tail |
| `mgmt_pending_remove()` | takes the mutex | `list_del()`, then frees |
| `mgmt_pending_find()` | takes it for the walk | none |
| `mgmt_pending_foreach()` | holds it across every callback | see below |
| `mgmt_pending_listed()` | takes the mutex | none |
| `__mgmt_pending_listed()` | `lockdep_assert_held()` | none |

- `mgmt_pending_remove()`: `list_del()` is unconditional; there is no test
  that the command is on the list.
- `mgmt_pending_foreach()` with `remove` true: unlinks before the callback
  and calls `mgmt_pending_free()` after it.
- `mgmt_pending_foreach()` callback: must not free the command, and must not
  call a helper that takes the mutex.
- `mgmt_pending_foreach()` with opcode 0: matches every command.
- `mgmt_pending_listed()` under the mutex: deadlocks; use
  `__mgmt_pending_listed()` there.
- `mgmt_pending_find()` result: not pinned once the helper returns.
- `hci_dev_lock()` does not pin a found command: completion callbacks call
  `mgmt_pending_valid()` without it, for example
  `mgmt_set_powered_complete()`.

**Counted arrays from user space**

- Count bound: needed although `struct_size()` saturates, because
  `expected_len` is a `u16` and would truncate; see `load_link_keys()` in
  `net/bluetooth/mgmt.c`.
- `u8` counts: `add_adv_patterns_monitor()` has no count bound, computes
  the size in a `size_t`, and requires `len > sizeof(*cp)`, so a count of
  zero is rejected.
- Per-element validation is not all-or-nothing in most handlers.
  - `load_irks()`: checks every element first and rejects the whole command.
  - `load_link_keys()` and `load_long_term_keys()`: clear the old keys, then
    skip a bad element with `continue`, and still reply success.
  - `load_conn_param()` and `load_conn_subrate()`: skip a bad element with
    `continue`, and still reply success.
- `load_conn_subrate()`: one more handler with the bound and the exact
  `struct_size()` comparison.

**Variable-length parameters on the stack**

- Stack copy of a command structure that ends in a flexible array: there is
  one in `net/bluetooth/mgmt.c`, `set_mesh_sync()`, declared with
  `DEFINE_FLEX()` for `struct mgmt_cp_set_mesh` and sized by
  `sizeof(hdev->mesh_ad_types)`.
- `DEFINE_FLEX()` count: must be a compile-time constant; `__DEFINE_FLEX()`
  in `include/linux/overflow.h` asserts it.
- Fill in `set_mesh_sync()`: `memcpy()` of
  `min(__struct_size(cp), cmd->param_len)`, under `hdev->mgmt_pending_lock`.
- `num_ad_types` after the copy: holds the value from user space, which
  `set_mesh()` does not validate; no statement names it, and it is the
  `__counted_by()` counter of `ad_types`.
- Tail length in `set_mesh_sync()`: taken from `cmd->param_len` minus
  `sizeof(struct mgmt_cp_set_mesh)`.
- Oversized tail: truncated by the copy, and then not used at all, because
  the tail is copied on only if its length fits `hdev->mesh_ad_types`.
- `char buf[512]` cast to a structure: used for reply and event structures
  that the kernel fills, as in `read_ext_controller_info()` and
  `ext_info_changed()`, not for a copy of command parameters.
- `mesh_send()`: no stack copy; `mgmt_mesh_add()` copies into the fixed
  `param` array of `struct mgmt_mesh_tx`.
- `mesh_send()` bound for that array: rejects `adv_data_len` of 0 or above
  31, then requires `struct_size()` to equal `len`.
- Counted-by annotations in `include/net/bluetooth/mgmt.h`: only
  `struct mgmt_cp_set_mesh` and `struct mgmt_cp_load_conn_subrate` have
  one; the other flexible arrays have none.

**Ownership in completion callbacks**

- Names: there is no set_powered_complete() or set_discoverable_complete()
  here; the callbacks are `mgmt_set_powered_complete()`,
  `mgmt_set_discoverable_complete()` and `mgmt_set_connectable_complete()`.
- Callbacks whose command comes from `mgmt_pending_new()` and is never
  listed, for example: `get_conn_info_complete()`,
  `get_clock_info_complete()`, `mgmt_class_complete()`.
- Socket close: removes no pending command; `mgmt_cleanup()` handles only
  `struct mgmt_mesh_tx`.
- What unlinks a listed command: `mgmt_pending_foreach()` with `remove`,
  `mgmt_pending_remove()`, `mgmt_pending_valid()`, `remove_pairing()` and
  `remove_pairing_by_addr()`.
- `err == -ECANCELED` must be tested before `mgmt_pending_valid()`:
  `cmd_complete_rsp()` runs the callback through `hci_cmd_sync_dequeue()`
  while `mgmt_pending_foreach()` holds `hdev->mgmt_pending_lock`.
- Listed command and `-ECANCELED`: the callback returns without freeing;
  in the `cmd_complete_rsp()` case `mgmt_pending_foreach()` frees it.
- **Unsafe usage**: `mgmt_pending_remove()` after `mgmt_pending_valid()`
  returned true; the entry is already unlinked.
  - Safe: `mgmt_pending_free()`, as in `set_name_complete()`.
- **Unsafe usage**: `mgmt_pending_remove()` on a command from
  `mgmt_pending_new()`; `cmd->list` is zeroed and `list_del()` is
  unconditional.
  - Safe: `mgmt_pending_free()`, as `disconnect()` does when
    `hci_cmd_sync_queue()` fails.
  - Safe: `mgmt_pending_remove()` on a command from `mgmt_pending_add()`
    that nothing has unlinked, as `set_powered()` does under
    `hci_dev_lock()` when queueing fails.
- **Unsafe usage**: a callback for a command from `mgmt_pending_new()` that
  returns without `mgmt_pending_free()`, for any `err` including
  `-ECANCELED`; nothing else frees the command.
  - Safe: free on every path, as `disconnect_complete()` and
    `mgmt_class_complete()` do.

**Pending commands in queued functions**

- Lock: `hdev->mgmt_pending_lock`, not `hci_dev_lock()`.
- `set_powered_sync()`: tests with `__mgmt_pending_listed()` under the
  mutex; it does not call `mgmt_pending_valid()` or `mgmt_pending_listed()`.
- `mgmt_pending_valid()` in a queued function: unlinks the command, so the
  completion callback's own `mgmt_pending_valid()` then fails and nothing
  replies or frees.
- Same pattern as `set_powered_sync()`: search `__mgmt_pending_listed` in
  `net/bluetooth/mgmt.c`; for example `set_ssp_sync()`, `set_name_sync()`
  and `set_mesh_sync()`; `mgmt_add_adv_patterns_monitor_sync()` reads
  `cmd->user_data` that way.
- `set_default_phy_sync()`: not this pattern; its command comes from
  `mgmt_pending_new()`.
- `cmd->sk`: a field of the command, so the same rule covers reading it.
- Socket reference: `mgmt_pending_new()` takes one and `mgmt_pending_free()`
  drops it; no queued function in `net/bluetooth/mgmt.c` takes its own.
- **Potentially unsafe usage**: dereferencing the command in a queued
  function outside `hdev->mgmt_pending_lock`.
  - Unsafe: for a command from `mgmt_pending_add()`, before the lock is
    taken or after it is dropped; `mgmt_pending_foreach()` with `remove`
    can free it at any time.
  - Safe: under the mutex after `__mgmt_pending_listed()` returned true,
    copying into locals, as `set_powered_sync()` does.
  - Safe: `mgmt_pending_listed()` as a go or no-go test with no later
    dereference, as `set_discoverable_sync()`, `set_connectable_sync()`,
    `start_discovery_sync()` and `stop_discovery_sync()` do.
  - Safe: for a command from `mgmt_pending_new()`; only its completion
    callback frees it, and `hci_cmd_sync_work()` runs that after the queued
    function returns, as with `get_conn_info_sync()`.

## Advertising

**Advertising instance tracking**

- `hci_add_adv_instance()` in `net/bluetooth/hci_core.c`, new entry: needs
  `1 <= instance <= hdev->le_num_of_adv_sets + 1` and
  `hdev->adv_instance_cnt < hdev->le_num_of_adv_sets`.
- Refusal on range or count: `ERR_PTR(-EOVERFLOW)`; allocation failure:
  `ERR_PTR(-ENOMEM)`. It does not return NULL, `-EINVAL` or `-EBUSY`.
- Instance `le_num_of_adv_sets + 1`: used by `mesh_send_sync()` in
  `net/bluetooth/mgmt.c`; the MGMT add handlers reject
  `cp->instance > hdev->le_num_of_adv_sets` before they call.
- `adv->handle` is a separate member of `struct adv_info`: 0x00 when
  `le_num_of_adv_sets == 1 && instance == 1`, otherwise equal to
  `adv->instance`.
- Commands that send `adv ? adv->handle : instance`: search `adv->handle` in
  `net/bluetooth/hci_sync.c`; for example `hci_enable_ext_advertising_sync()`
  and `hci_set_ext_adv_data_sync()`.
- Commands that send the instance number unchanged: for example
  `hci_remove_ext_adv_instance_sync()`, `hci_set_adv_set_random_addr_sync()`,
  `hci_set_per_adv_params_sync()`, `hci_enable_per_advertising_sync()`.
- Handle back to entry: reply and event handlers in
  `net/bluetooth/hci_event.c` pass the handle to `hci_find_adv_instance()`,
  which compares `adv->instance`; an entry whose `adv->handle` is 0x00 is not
  found by its handle.
- `instance` argument 0x00 to `hci_disable_ext_adv_instance_sync()`: disables
  every set (`num_of_sets` 0), not handle 0x00 alone.
- `hci_disable_ext_adv_legacy_instance_sync()`: disables handle 0x00 alone,
  and sends nothing when `HCI_LE_ADV_0` is clear.
- `hci_remove_ext_adv_instance_sync()` with instance 0: disables every set,
  then removes only handle 0x00.

**Testing whether advertising is on**

- `HCI_LE_ADV_0` in `include/net/bluetooth/hci.h`: tracks the enable and
  disable commands that name handle 0x00 on a controller with extended
  advertising.
- `HCI_LE_ADV_0` writers: `hci_cc_le_set_ext_adv_enable()` sets or clears it
  when a command with `num_of_sets` non-zero names handle 0x00 and the lookup
  finds no entry; `hci_resume_advertising_sync()` clears it.
- `HCI_LE_ADV_0` after a disable with `num_of_sets == 0`: still set; that
  reply clears every `adv->enabled` and `HCI_LE_ADV` only.
- `HCI_LE_ADV`: set by every successful enable reply, for any handle; it is
  not specific to instance zero.
- `HCI_LE_ADV` clear while an `adv->enabled` is true: `le_conn_complete_evt()`
  clears `HCI_LE_ADV` on success status and writes no `adv->enabled`.
- `adv->enabled`: set by `hci_cc_le_set_ext_adv_enable()` for any entry found,
  periodic or not; `periodic_enabled` is separate, kept by
  `hci_cc_le_set_per_adv_enable()`.
- `adv->enabled`: written only by `hci_cc_le_set_ext_adv_enable()` and
  `hci_le_ext_adv_term_evt()`; `hci_cc_le_set_adv_enable()` maintains
  `HCI_LE_ADV` only.
- Entry with `adv->handle` 0x00 (`le_num_of_adv_sets == 1`, instance 1): its
  enable and disable replies change `HCI_LE_ADV_0`, not `adv->enabled`.
- **Unsafe usage**: testing `HCI_LE_ADV` to decide that handle 0x00 is enabled
  on a controller with extended advertising; an enable of any set sets
  `HCI_LE_ADV`.
  - Safe: test `HCI_LE_ADV_0`, which `hci_cc_le_set_ext_adv_enable()` writes
    only for handle 0x00, as `hci_disable_ext_adv_legacy_instance_sync()`
    does; the flag can be set while handle 0x00 is off, and that function then
    sends a disable for handle 0x00.
- **Unsafe usage**: reading a `struct adv_info` outside `hci_dev_lock()` while
  a reply or event handler can run; `hci_remove_adv_instance()` frees the
  entry, for example from `hci_le_ext_adv_term_evt()`.
  - Safe: look up and read under `hci_dev_lock()`, and unlock before sending
    the command, as `hci_set_ext_adv_data_sync()` does.
- Set Ext Adv Params reply: there is no hci_cc_set_ext_adv_param() here;
  `hci_set_ext_adv_params_sync()` in `net/bluetooth/hci_sync.c` parses the
  reply and stores `hdev->adv_tx_power` for instance 0.
- `hci_cc_le_set_adv_set_random_addr()`: returns without storing anything
  when the handle is 0.
- `hdev->random_addr` for instance zero: stored by
  `hci_cc_le_set_random_addr()`; `hci_set_adv_set_random_addr_sync()` calls
  `hci_set_random_addr_sync()` first when the instance is 0, which sends
  `HCI_OP_LE_SET_RANDOM_ADDR` unless it defers the update.

**Pausing and resuming advertising**

- Pause state: `hdev->advertising_paused` and `hdev->advertising_old_state`;
  neither holds `hdev->cur_adv_instance` or `HCI_LE_ADV`.
- `hdev->advertising_old_state`: holds the `HCI_ADVERTISING` bit; pause does
  not clear `HCI_ADVERTISING`, and resume only sets the flag again, so it
  selects no command.
- Extended resume, listed instances: `hci_enable_ext_advertising_sync()` for
  every entry in `hdev->adv_instances`, not
  `hci_schedule_adv_instance_sync()`.
- Extended resume, instance zero: re-enabled with
  `hci_enable_ext_advertising_sync(hdev, 0x00)` if
  `hci_dev_test_and_clear_flag(hdev, HCI_LE_ADV_0)` is true;
  `hdev->cur_adv_instance` is not read.
- `HCI_LE_ADV_0` between pause and resume: does not mean "enabled in the
  controller"; the pause's disable has `num_of_sets` 0 and its reply leaves
  the flag set.
- `HCI_LE_ADV_0` after resume: set again by the enable reply on success; if
  the enable fails it stays clear.
- Legacy resume: `hci_schedule_adv_instance_sync(hdev,
  hdev->cur_adv_instance, true)` returns `-EPERM` when `HCI_ADVERTISING` is
  set and `-ENOENT` when the instance has no entry, before any command; so
  `hci_resume_advertising_sync()` itself sends nothing for instance zero.
- Failed resume, controller: `hci_remove_ext_adv_instance_sync()` sends
  `HCI_OP_LE_REMOVE_ADV_SET` with the instance number, not `adv->handle`.
- Failed resume, list: the sync function frees nothing;
  `hci_cc_le_remove_adv_set()` calls `hci_remove_adv_instance()` and
  `mgmt_advertising_removed()` on success status only.
- Remove command fails: the entry stays in `hdev->adv_instances` with
  `enabled` false; the resume loop ignores the return value.

## L2CAP

**L2CAP connection and channel locks**

- `struct l2cap_conn`: one mutex, `conn->lock`; there is no chan_lock or
  ident_lock field.
- `conn->lock` covers `conn->chan_l`, `conn->rx_skb`, `conn->rx_len` and
  `conn->users`.
- `conn->hchan`: cleared under `conn->lock` in `l2cap_conn_del()` and tested
  under it in `l2cap_register_user()`.
- Signalling idents: allocated from the IDA `conn->tx_ida` in
  `l2cap_get_ident()`, with no mutex of their own.
- `l2cap_recv_acldata()`: calls `hci_dev_unlock()` before it takes
  `conn->lock`; the reference from `l2cap_conn_hold_unless_zero()`, taken
  under the device lock, keeps the conn alive across the gap.
- Device lock outside `conn->lock`: see `l2cap_chan_connect()`, and
  `l2cap_conn_del()` and `l2cap_security_cfm()`, both marked
  `__must_hold(&hcon->hdev->lock)`.
- `l2cap_chan_add()`: takes `conn->lock`. `__l2cap_chan_add()` and
  `l2cap_chan_del()` link and unlink `conn->chan_l` and do not take
  `conn->lock`.
- `l2cap_chan_timeout()` and `l2cap_sock_shutdown()`: take `conn->lock`, then
  the channel lock, before `l2cap_chan_close()`; `l2cap_sock_shutdown()`
  skips `conn->lock` when `l2cap_conn_hold_unless_zero()` returned NULL.
- Per-connection lookups that return a referenced, locked channel:
  `l2cap_get_chan_by_scid()` and `l2cap_get_chan_by_dcid()`. Neither takes
  `conn->lock`; the caller holds it.
- There is no l2cap_get_chan_by_ident() here. Callers of
  `__l2cap_get_chan_by_ident()`, for example `l2cap_connect_create_rsp()`, call
  `l2cap_chan_hold_unless_zero()` and `l2cap_chan_lock()` themselves.
- `chan_list_lock`: rwlock for the global `chan_list`.
  `l2cap_global_chan_by_psm()` and `l2cap_global_fixed_chan()` return a
  referenced channel that is not locked.
- `l2cap_chan_lock()`: `mutex_lock_nested()` with subclass `chan->nesting`, an
  `atomic_t` that `l2cap_chan_create()` sets to `L2CAP_NESTING_NORMAL`.
- Listening channel: set to `L2CAP_NESTING_PARENT`, as `l2cap_sock_listen()`
  does. `smp_new_conn_cb()` sets `L2CAP_NESTING_SMP`.
- `l2cap_chan_ops` callbacks: `l2cap_sock_teardown_cb()` takes the socket with
  `lock_sock_nested()` at `chan->nesting`; the others that lock the socket,
  for example `l2cap_sock_state_change_cb()`, use `lock_sock()`.
- `l2cap_sock_getsockopt()` and `l2cap_sock_setsockopt()`: take the channel
  lock first, then `lock_sock()`.
- **Unsafe usage**: taking `conn->lock` while holding a socket lock or a
  channel lock.
  - Safe: release both first, as `l2cap_sock_shutdown()` does: it pins the
    conn with `l2cap_conn_hold_unless_zero()` under the channel lock, drops
    that lock, then takes `conn->lock` and the channel lock.
    `l2cap_chan_timeout()` defines the order: `conn->lock`, channel lock, then
    `chan->ops->close()`, which takes the socket lock.
  - Safe: defer the close, as `l2cap_sock_cleanup_listen()` does under the
    parent socket lock: it arms `__set_chan_timer()` with timeout 0, and
    `l2cap_chan_timeout()` closes the channel under `conn->lock`.

**Channel references and timers**

- Socket reference: it is the creator's reference from `l2cap_chan_create()`;
  `l2cap_sock_alloc()` takes no extra one.
- `l2cap_sock_put_chan()`: drops the socket's reference once and clears
  `chan->data` and `l2cap_pi(sk)->chan`; called from `l2cap_sock_kill()` under
  `lock_sock()` and from `l2cap_sock_destruct()`.
- `chan->conn`: set in `__l2cap_chan_add()` with `l2cap_conn_get()` and not
  cleared afterwards; `l2cap_chan_destroy()` drops that conn reference.
- Deleted channel: marked by `FLAG_DEL`, set in `l2cap_chan_del()`. All four
  timer handlers test `FLAG_DEL`, not `chan->conn`.
- `l2cap_chan_timeout()`: tests `FLAG_DEL` before taking any lock and puts;
  it tests again under `conn->lock` and the channel lock.
- Timer handlers: take no reference; each consumes the one that
  `l2cap_set_timer()` took.
- `l2cap_set_timer()`: calls `l2cap_chan_hold()` when `cancel_delayed_work()`
  returned false, then `schedule_delayed_work()`, whose result it ignores.
- `__set_retrans_timer()`: a static function in
  `net/bluetooth/l2cap_core.c`; arms nothing while `monitor_timer` is pending
  or `chan->retrans_timeout` is 0.
- `__set_monitor_timer()`: clears the retransmission timer first; arms
  nothing if `chan->monitor_timeout` is 0.
- `__set_ack_timer(c)`: the macro body names `chan->ack_timer`, so it holds
  `c` and arms the timer of the variable `chan` in scope.
- `l2cap_chan_hold_unless_zero()`: dereferences its argument;
  `l2cap_conn_hold_unless_zero()` returns NULL for NULL.
- **Potentially unsafe usage**: plain `l2cap_chan_hold()` on a channel reached
  through a list or a back pointer.
  - Unsafe: on a channel found by walking `chan_list`; `l2cap_chan_destroy()`
    unlinks it only after the count has reached zero.
  - Safe: on an entry of `conn->chan_l` under `conn->lock`, as
    `l2cap_conn_del()` does; `l2cap_chan_del()` drops the list's reference
    only after `list_del()`.
  - Safe: on a non-NULL `l2cap_pi(sk)->chan` under the socket lock, as
    `l2cap_sock_cleanup_listen()` does; `l2cap_sock_kill()` clears that
    pointer and drops the reference under `lock_sock()`.

**Parsing received L2CAP frames**

- `l2cap_sig_channel()`, packet over `L2CAP_SIG_MTU` (48): sends one
  `L2CAP_REJ_MTU_EXCEEDED` reject and drops the whole packet;
  `l2cap_le_sig_channel()` has no such test.
- `l2cap_sig_channel()`, command with `len > skb->len` or zero ident: sends a
  reject, pulls the smaller of `len` and `skb->len`, and continues the loop.
- `l2cap_sig_channel()`, bytes left over that are fewer than
  `L2CAP_CMD_HDR_SIZE`: sends a reject with ident 0.
- `l2cap_bredr_sig_cmd()`: discards the return value of the response
  handlers, for example `l2cap_config_rsp()`, so a short response gets no
  command reject. `l2cap_le_sig_cmd()` does the same for
  `l2cap_le_connect_rsp()`.
- `l2cap_get_conf_opt()`: takes an `end` pointer and returns `-EINVAL` when
  the option header or value does not fit; callers stop on a negative return.
- `l2cap_get_conf_opt()` with `olen` other than 1, 2 or 4: `*val` is a pointer
  into the buffer; the caller compares `olen` with the destination size
  before `memcpy()`, as `l2cap_parse_conf_req()` does.
- `net/bluetooth/l2cap_core.c` does not call `skb_pull_data()`; the tests are
  explicit compares of `skb->len` and `cmd_len`, plus `pskb_may_pull()` for
  the SDU length.
- `l2cap_recv_acldata()`: takes `struct hci_dev *hdev` and a `u16 handle`,
  finds the hcon under `hci_dev_lock()`, and returns `-ENOENT` after freeing
  the skb if there is none.
- Start fragment longer than the declared frame: `skb->len` is cut to the
  declared length plus `L2CAP_HDR_SIZE`, the frame goes to
  `l2cap_recv_frame()`, and then `l2cap_conn_unreliable()` is called; the
  frame is not dropped.
- Start fragment and MTU: `l2cap_recv_acldata()` does not compare the declared
  length with `conn->mtu`.
- Start fragment shorter than `L2CAP_LEN_SIZE`: buffered in a `conn->rx_skb`
  sized from `conn->mtu`; `l2cap_recv_len()` finishes the length from the next
  fragment.
- `l2cap_recv_frame()` with `hcon->state` not `BT_CONNECTED`: queues the skb
  on `conn->pending_rx` before any length test; `process_pending_rx()` runs
  the tests later.
- `l2cap_ecred_data_rcv()`: returns a negative value only while the caller
  still owns the skb (no credits, over `chan->imtu`, over `chan->mps`, or
  `l2cap_ecred_recv()` failing on an SDU that fits one PDU); on its other
  error paths it frees the skb itself and returns 0, because
  `l2cap_data_channel()` frees the skb on a negative return.
- **Unsafe usage**: passing `l2cap_recv_frame()` an skb shorter than
  `L2CAP_HDR_SIZE`; it reads the header with no length test and ignores the
  result of `skb_pull()`.
  - Safe: `l2cap_recv_acldata()` passes a frame only when the declared length
    plus `L2CAP_HDR_SIZE` equals or was cut to `skb->len`, or when
    `conn->rx_len` has reached 0.
  - Safe: `process_pending_rx()` passes only skbs that `l2cap_recv_frame()`
    itself queued on `conn->pending_rx`.

## Model gaps

### Other mistakes models make

- Models take `hci_cmd_sync_cancel()` to wake the waiter itself. It queues
  `cmd_sync_cancel_work`, which wakes the waiter;
  `hci_cmd_sync_cancel_sync()` wakes the waiter directly.
- Models do not know the flag `HCI_LE_PER_ADV`.
  `hci_cc_le_set_per_adv_enable()` sets and clears it.
- Models take a handler in `net/bluetooth/hci_event.c` to store
  `adv->tx_power` from the Set Extended Advertising Parameters reply.
  `hci_set_ext_adv_params_sync()` in `net/bluetooth/hci_sync.c` stores it, for
  a non-zero instance that has an entry.
- Models take lock requirements here to be stated only by comments and
  lockdep. `net/bluetooth/Makefile` sets `CONTEXT_ANALYSIS := y`, so with
  `CONFIG_WARN_CONTEXT_ANALYSIS` the compiler checks `__must_hold()`; a
  function that locks conditionally is opted out with `__context_unsafe()`,
  for example `hci_set_ext_adv_data_sync()`.
- Models take a `struct hci_dev` that was never registered to hold nothing but
  its memory. `struct hci_dev` has `srcu`, set up in `hci_alloc_dev_priv()`.
- Models take signalling ident allocation never to fail. `l2cap_get_ident()`
  returns 0 when no ident is free in `conn->tx_ida`.
- Models write allocations here as `kzalloc()` or `kmalloc()` of a `sizeof`.
  This tree uses `kzalloc_obj()`, `kmalloc_obj()` and `kzalloc_flex()` from
  `include/linux/slab.h`, as in `mgmt_pending_new()` and
  `hci_cmd_sync_submit()`.
