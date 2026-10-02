- Zone management ops: `REQ_OP_ZONE_OPEN` is 11, `REQ_OP_ZONE_CLOSE` 13,
  `REQ_OP_ZONE_FINISH` 15, `REQ_OP_ZONE_RESET` 17, `REQ_OP_ZONE_RESET_ALL` 19.
- All five zone management ops are odd, so `op_is_write()` is true and
  `bio_data_dir()` is `WRITE` for each, although none carries data.
- `REQ_OP_ZONE_APPEND`: value 7.
- `op_is_write()` is false only for `REQ_OP_READ`, `REQ_OP_FLUSH` and
  `REQ_OP_DRV_IN`.
- `REQ_OP_FLUSH` in a bio: `submit_bio_noacct()` in `block/blk-core.c` ends
  the bio with `BLK_STS_NOTSUPP`.
- `REQ_OP_DRV_IN` and `REQ_OP_DRV_OUT` in a bio: `submit_bio_noacct()` ends
  the bio with `BLK_STS_NOTSUPP` too.
- `REQ_PREFLUSH` or `REQ_FUA` on a bio: `submit_bio_noacct()` accepts them
  only with `REQ_OP_WRITE` or `REQ_OP_ZONE_APPEND`; with any other op it warns
  once and fails the bio.
