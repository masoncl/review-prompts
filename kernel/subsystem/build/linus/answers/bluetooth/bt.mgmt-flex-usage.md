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
