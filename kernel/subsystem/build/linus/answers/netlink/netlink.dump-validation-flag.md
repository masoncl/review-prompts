| Op type | With `GENL_DONT_VALIDATE_DUMP` |
|---|---|
| `struct genl_ops`, `struct genl_small_ops` | `genl_cmd_full_to_split()` clears `policy` and `maxattr` of the dump half; no parse runs, `info.attrs` is `NULL`, attributes are neither checked nor rejected |
| `struct genl_split_ops` | `policy` and `maxattr` stay as written; `genl_start()` still parses the request against them |

- Split dump op with the flag and a policy: still parsed, strictly unless
  `GENL_DONT_VALIDATE_DUMP_STRICT` is also set; for example the
  `CTRL_CMD_GETFAMILY` dump in `genl_ctrl_ops` is parsed strictly.
- Header length: `genl_family_rcv_msg()` rejects a message shorter than
  `GENL_HDRLEN` plus `hdrsize` before `genl_start()` runs, so the test the
  flag skips in `genl_start()` is a repeat.
- Legacy dump handler that needs attributes: parses `cb->nlh` itself, as
  `ovs_flow_cmd_dump()` in `net/openvswitch/datapath.c` does with
  `genlmsg_parse_deprecated()`.
- Policy dump: `ctrl_dumppolicy_start()` adds, and `ctrl_dumppolicy_put_op()`
  reports, no dump policy for a legacy op with the flag, because the dump
  half has `policy` `NULL`.
