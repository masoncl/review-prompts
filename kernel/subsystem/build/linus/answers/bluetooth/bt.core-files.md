Files are under `net/bluetooth/` unless a directory is given.

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
