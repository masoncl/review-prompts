- Protocol code: `fs/smb/smbdirect/`, not under `fs/smb/common/`; there is no
  fs/smb/common/smbdirect/ directory in this tree.
- File names carry no prefix, for example `accept.c` and `connection.c`.
- Headers: wire formats in `fs/smb/smbdirect/pdu.h`; `struct smbdirect_socket`
  in `fs/smb/smbdirect/socket.h`; internal prototypes in
  `fs/smb/smbdirect/internal.h`; there is no smbdirect_pdu.h or
  smbdirect_socket.h.
- Public API: `include/linux/smbdirect.h`; it defines
  `struct smbdirect_socket_parameters` and only forward-declares
  `struct smbdirect_socket`, so ksmbd and cifs hold a pointer and cannot reach
  its fields.
- `CONFIG_SMBDIRECT` in `fs/smb/smbdirect/Kconfig`: promptless tristate,
  selected by `CONFIG_SMB_SERVER_SMBDIRECT` and `CONFIG_CIFS_SMB_DIRECT`;
  builds the separate module `smbdirect.o`.
- Exports: all in namespace "SMBDIRECT" (`DEFAULT_SYMBOL_NAMESPACE` in
  `fs/smb/smbdirect/internal.h`); each user needs `MODULE_IMPORT_NS()`.
- Other user: `fs/smb/client/smbdirect.c`; the move is complete on both sides,
  neither `fs/smb/server/` nor `fs/smb/client/` calls an RDMA core function
  directly.
- `fs/smb/server/transport_rdma.c`: glue only; it has no RDMA CM handler, no
  completion handler, no credit or negotiate code and no work item.
- Listener in `transport_rdma.c`: a `struct smbdirect_socket` made by
  `smbdirect_socket_create_kern()`, then `smbdirect_socket_bind()` and
  `smbdirect_socket_listen()`; see `smb_direct_listen()`.
- Two listeners, `smb_direct_ib_listener` (port 445) and
  `smb_direct_iw_listener` (port 5445); each has a kthread,
  `smb_direct_listener_kthread_fn()`, that loops on `smbdirect_socket_accept()`.
- `struct smb_direct_transport`: holds a pointer `socket`, not an embedded
  socket.
- There is no ksmbd_rdma_destroy() here; `ksmbd_rdma_stop_listening()` tears
  both listeners down.
