- Bound for a field the message check did not cover: the current command's
  length from `smb2_current_req_len()`, compared as `off > len ||
  cnt > len - off`; see the channel info test in `smb2_read()`.
- `smb2_find_context_vals()` guarantees that name and data lie inside the
  context, not that the data is large enough for the caller's struct; callers
  compare `DataOffset + DataLength` with the struct size, as
  `smb2_create_sd_buffer()` does.
- `smb2_set_ea()` entry size: `sizeof(struct smb2_ea_info) + EaNameLength + 1
  + EaValueLength`; the 1 is the name terminator.
- `LockCount`: bounded against the request by `ksmbd_smb2_check_message()`,
  for which `smb2_get_data_area_len()` makes the lock array the data area, not
  by `smb2_lock()`, which only rejects 0 and values above 64.
- `parse_sec_desc()` returning 0 does not mean the offsets were checked: it
  returns 0 before validating them when `DACL_PRESENT` is clear in `type`.
- **Unsafe usage**: calling `smb2_set_ea()` with a `buf_len` that was not
  compared with `sizeof(struct smb2_ea_info)`; it reads `EaNameLength` of the
  first entry before any size test.
  - Safe: check first, as `smb2_set_info_file()` and the `ea_buf` path of
    `smb2_open()` do.
- **Unsafe usage**: testing the result of `smb2_find_context_vals()` for NULL
  only; a malformed list returns `ERR_PTR(-EINVAL)`.
  - Safe: test both `IS_ERR()` and NULL, in either order, as
    `parse_lease_state()` and `smb2_create_sd_buffer()` do.
- **Potentially unsafe usage**: reading a field of the request body in code
  that runs before `ksmbd_verify_smb_message()`, such as
  `check_user_session` or `allocate_rsp_buf`.
  - Unsafe: when nothing has compared the field's position with the received
    length; no size or layout check has run yet, and `NextCommand` of the
    current command is not yet validated either.
  - Safe: compare the field's position with `get_rfc1002_len()` of the
    request first, as `smb2_allocate_rsp_buf()` does before it reads
    `InfoType`.
