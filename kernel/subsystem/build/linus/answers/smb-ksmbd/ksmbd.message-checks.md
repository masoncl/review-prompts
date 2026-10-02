- `ProtocolId`: tested by `ksmbd_verify_smb_message()` in
  `fs/smb/server/smb_common.c`, on the current command's header;
  `check_smb2_hdr()` only rejects `SMB2_FLAGS_SERVER_TO_REDIR`.
- `len` below `__SMB2_HEADER_STRUCTURE_SIZE + sizeof(__le16)`: rejected before
  `StructureSize2` is read; this matters for a small `NextCommand`.
- Accepted when `clc_len != len`, exactly these four:
  - `clc_len == len + 1`;
  - `ALIGN(clc_len, 8) == len`;
  - the command is `SMB2_NEGOTIATE_HE`, any mismatch;
  - `clc_len < len` and `len - clc_len <= 8`.
- No other command tolerates a calculated length above `len + 1`.
- NEGOTIATE: `smb2_get_data_area_len()` has no case for it, so only the fixed
  part is checked; `smb2_handle_negotiate()` bounds the dialects and contexts.
- Offsets clamped up to `offsetof(..., Buffer)` in `smb2_get_data_area_len()`:
  for example `BufferOffset`, `DataOffset`, `InputOffset`. The clamp is local;
  the field in the request is unchanged.
- A handler that adds the raw field to `req` reads a different place than the
  one checked when the field is below `Buffer`; `smb2_write()` rejects such a
  `DataOffset` itself.
- Not clamped: `SecurityBufferOffset`, `ReadChannelInfoOffset`,
  `WriteChannelInfoOffset`, `CreateContextsOffset`.
- Data length 0: `smb2_calc_size()` skips the overlap test and the offset takes
  no part in `clc_len`; the offset is only known to be <= 4096.
- `clc_len == len + 1`: the last byte of the calculated length is past what
  was received. The buffer has one spare byte (`pdu_size + 4 + 1` from
  `kvmalloc()`) that the read does not fill; in a non-final compound command
  that byte is the next header's first byte.
