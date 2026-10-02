# Netlink / Generic Netlink uAPI Details

## Main structures

### Objects and how they relate

- `struct genl_split_ops`: both a table form a family supplies (`split_ops`
  in `struct genl_family`) and the form every lookup yields; see
  `genl_get_cmd()` in `net/netlink/genetlink.c`.
- More than one op table in one family: for example
  `net/wireless/nl80211.c` sets both `ops` and `small_ops`; what
  `genl_validate_ops()` requires of that is under "Operation table forms".
- Op pointer seen by `pre_doit` and `post_doit`, and `genl_dumpit_info(cb)->op`:
  a per-request copy with the reject-all policy and, for `ops` and
  `small_ops` entries, the family defaults filled in, not a pointer into the
  family's table.
- Generated code: the op form varies; `net/ipv4/fou_nl.c` generates
  `struct genl_small_ops`, `net/mptcp/mptcp_pm_gen.c` generates
  `struct genl_ops`, most others `struct genl_split_ops`.
- Generated file and `struct genl_family`: some define the family too
  (`net/core/netdev-genl-gen.c`); others hold only the tables and the family
  is hand-written elsewhere (`net/ipv4/fou_core.c`).
- Fixed family ids: `GENL_ID_CTRL`, `GENL_ID_VFS_DQUOT` and `GENL_ID_PMCRAID`;
  `genl_register_family()` picks the last two by comparing the family name.
- Multicast group numbers: allocated from one global bitmap (`mc_groups`), so
  a group has the same number in every netns; only the kernel socket
  `net->genl_sock`, and so delivery, is per netns, apart from listeners that
  set `NETLINK_LISTEN_ALL_NSID`.
- `genlmsg_multicast()`: sends through the `init_net` socket only; callers
  pass the index in the family's `mcgrps`, not the global number.
- `doit(skb, info)`: `skb` is the request; `skb->sk` is the kernel socket and
  the requester's socket is `NETLINK_CB(skb).sk`.
- `dumpit(skb, cb)`: `skb` is a new reply buffer owned by the requester's
  socket; the request is `cb->skb`, so sender data is `NETLINK_CB(cb->skb)`.
- `struct netlink_callback`: embedded in the requester's
  `struct netlink_sock`, found by portid in `__netlink_dump_start()`; it has
  no policy member.
- `struct genl_dumpit_info`: what `cb->data` is in a generic netlink dump;
  `genl_start()` allocates it and `genl_done()` frees it. It holds the op copy
  (with the dump's policy) and the dump's `struct genl_info`, read with
  `genl_info_dump()`. Family state goes in `cb->ctx`.
- `struct genl_info` for a do: on the stack of `genl_family_rcv_msg_doit()`;
  `attrs` is freed before that function returns, after `post_doit`.
- `attrs` entries: pointers into the request skb. For a dump
  `__netlink_dump_start()` holds a reference on that skb until the dump ends.
- `user_ptr` in `struct genl_info`: shares a union with
  `ctx[NETLINK_CTX_SIZE]`, zeroed before `pre_doit`; it is separate storage
  from `ctx` in `struct netlink_callback`.
- Notification `struct genl_info`: built by `genl_info_init_ntf()`, with
  `nlhdr` `NULL` and `genlhdr` pointing into its own `user_ptr[0]` storage,
  so `ctx` is not free for use; test with `genl_info_is_ntf()`.
- `struct netlink_ext_ack` for a request: one per message, zeroed on the stack
  of `netlink_rcv_skb()`.
- Extack TLVs reach userspace only if the requesting socket has
  `NETLINK_F_EXT_ACK` set; see `netlink_ack_tlv_len()`.

## Where to look

**Core files**

| Job | Where, and what is easy to miss |
|---|---|
| Kernel-internal Generic Netlink header | `include/net/genetlink.h`; there is no include/linux/genetlink.h in this tree |
| `struct netlink_ext_ack`, `NL_SET_ERR_MSG()` | `include/linux/netlink.h`, not `include/net/netlink.h` |
| Generated kernel code | no naming rule and not only under `net/`; search for `YNL-GEN kernel`; for example `net/core/netdev-genl-gen.c`, `net/devlink/netlink_gen.c`, `fs/nfsd/netlink.c`, `drivers/dpll/dpll_nl.c` |
| Generated uAPI headers | search for `YNL-GEN uapi header`; file name and directory need not match the family, for example `include/uapi/linux/ethtool_netlink_generated.h`, `include/uapi/drm/drm_ras.h` |
| Specs without a generated uAPI header | about half of the specs; for example `include/uapi/linux/devlink.h` is hand-written although `net/devlink/netlink_gen.c` is generated |
| Regenerating checked-in generated files | `tools/net/ynl/ynl-regen.sh` |
| Generated user-space C code | `tools/net/ynl/generated/` holds only `Makefile` and `.gitignore`; the `-user.c` and `-user.h` files are build output; `GENS_UNSUP` there leaves out conntrack and nftables |
| C sample and test programs | `tools/net/ynl/tests/`; there is no tools/net/ynl/samples/ in this tree |
| C command-line tool on top of `libynl.a` | `tools/net/ynl/ynltool/` |
| Rendered spec documentation | `Documentation/netlink/specs/index.rst`, parsed by `Documentation/sphinx/parser_yaml.py` using `tools/net/ynl/pyynl/lib/doc_generator.py`; there is no Documentation/networking/netlink_spec/ |
| Running the YNL tests | `make -C tools/net/ynl` first, then `make -C tools/net/ynl run_tests`; `run_tests` in `tools/net/ynl/tests/Makefile` has no build prerequisite |
| What `run_tests` runs | the `TEST_PROGS` scripts only; the `TEST_GEN_PROGS` binaries are built by `all` and not run by `run_tests` |
| YNL tests and kselftest | `tools/net/ynl/tests/` is not a `TARGETS` entry in `tools/testing/selftests/Makefile`; needed kernel options are in `tools/net/ynl/tests/config` |
| Spec lint and schema check | `lint` and `schema_check` targets in `tools/net/ynl/Makefile` |
| Selftest for the `nlctrl` family (family info and policy dump) | `tools/testing/selftests/net/nl_nlctrl.py` |
| YNL glue for kselftests | C: `tools/testing/selftests/net/ynl.mk` builds `libynl.a` for the families in `YNL_GENS`; Python: `tools/testing/selftests/net/lib/py/ynl.py` |

## Families and operations

**Family registration**

- Not refused: an empty family name, `maxattr` without a policy, unknown bits
  in a group's `flags`, any number of groups. There is no GENL_MAX_MCGRPS
  here.
- `genl_validate_ops()` in `net/netlink/genetlink.c`, `-EINVAL` for: a
  non-zero count with a NULL table; a `struct genl_ops` or
  `struct genl_small_ops` entry with neither `doit` nor `dumpit`; any
  `validate` flag on an op with `cmd >= resv_start_op` (every op when
  `resv_start_op` is 0); the same `cmd` twice across the three tables; the
  split-entry rules under "Operation table forms".
- Family ID range: `GENL_START_ALLOC` to `GENL_MAX_ID`, not `GENL_MIN_ID`.
- Fixed family IDs: `genl_ctrl` is matched by pointer; "pmcraid" and
  "VFS_DQUOT" are matched by `family->name`.
- Fixed group IDs, in `genl_validate_assign_mc_groups()`: four families, not
  three. The family named "NET_DM" gets group 1; `genl_ctrl`, and the
  families whose `id` is `GENL_ID_VFS_DQUOT` or `GENL_ID_PMCRAID`, get
  their family ID as group ID.
- Those four families: `BUG_ON(n_groups != 1)`, so a second group there
  crashes at registration.
- `bind` return value: `genl_bind()` discards it. `genl_bind()` returns only
  0 or the `-EPERM` from the group capability flags; a family cannot refuse
  a join.

**Multicast bind callbacks**

- Lock: `genl_bind()` and `genl_unbind()` hold `cb_lock` for read only;
  `genl_mutex` is not held.
- Capability flags: `GENL_MCAST_CAP_NET_ADMIN` and `GENL_MCAST_CAP_SYS_ADMIN`,
  tested with `ns_capable(net->user_ns, ...)` on the current task; on
  `-EPERM` `bind` is not called.
- `netnsok`: `genl_bind()` does not test it; `bind` runs for a join from any
  netns, and gets no net argument.
- Calls are not balanced. `netlink_setsockopt()` calls `bind` on every
  `NETLINK_ADD_MEMBERSHIP`, member already or not, and `unbind` on every
  `NETLINK_DROP_MEMBERSHIP`, member or not.
- `netlink_bind()`: calls `bind` for every bit set in `nl_groups`, including
  groups already joined.
- `netlink_undo_bind()`: on failure calls `unbind` for each requested
  lower-numbered group, including groups the socket had joined earlier and
  still holds.
- A later `bind(2)` with a smaller `nl_groups`: `netlink_bind()` overwrites
  the low 32 group bits; no `unbind` call for the groups dropped.
- Family unregister: `genl_unregister_mc_groups()` removes members with
  `__netlink_clear_multicast_users()`; no `unbind` call.
- In-tree user: only `thermal_genl_family` in
  `drivers/thermal/thermal_netlink.c` sets the callbacks.

**Operation table forms**

- Mixing: `genl_validate_ops()` has no test on which tables are present. Any
  combination of `ops`, `small_ops` and `split_ops` passes, provided no
  `cmd` appears in more than one.
- Lookup order in `genl_get_cmd()`: `ops`, then `small_ops`, then
  `split_ops`.
- Conversion: there is no genl_cmd_small_to_split() here.
  `genl_op_from_small()` fills a `struct genl_ops`, then
  `genl_cmd_full_to_split()` converts it.
- `pre_doit` and `post_doit`: `struct genl_split_ops` carries its own. The
  hooks in `struct genl_family` are copied in only by
  `genl_cmd_full_to_split()`, so they never run for a split entry.
- `GENL_CMD_CAP_DO` and `GENL_CMD_CAP_DUMP`: the core adds them to legacy
  ops from the handlers present; a split entry must set exactly one itself.
- Handler pointers of a split entry: not checked. An entry with
  `GENL_CMD_CAP_DO` and a NULL `doit` registers, and
  `genl_family_rcv_msg_doit()` calls `ops->doit` with no test.
- `start` or `done` without `dumpit`: no test for it.
- Order of split entries: `cmd` must not decrease from one entry to the
  next; two entries with one `cmd` must be the `GENL_CMD_CAP_DO` entry
  followed by the `GENL_CMD_CAP_DUMP` entry.
- Two split entries with one `cmd`: `internal_flags` must be equal, as well
  as `flags` outside `GENL_CMD_CAP_DO` and `GENL_CMD_CAP_DUMP`.

**Policy for a command**

- `genl_family_rcv_msg_attrs_parse()`: takes the policy and the maximum only
  from `ops->policy` and `ops->maxattr` of the resolved
  `struct genl_split_ops`. The family fallback is applied earlier, in
  `genl_op_from_full()` and `genl_op_from_small()`.
- `struct genl_ops`: `policy` and `maxattr` fall back separately. An op with
  its own `policy` and `maxattr` 0 is parsed with its policy and
  `family->maxattr`.
- Legacy op, no policy anywhere, `cmd >= resv_start_op`:
  `genl_op_fill_in_reject_policy()` installs `genl_policy_reject_all`.
  `maxattr` is not changed.
- Legacy op, no policy anywhere, `cmd < resv_start_op`: no parsing, no
  validation; `info->attrs` is NULL.
- Split entry, no policy: `genl_op_fill_in_reject_policy_split()` installs
  `genl_policy_reject_all` without testing `resv_start_op`.
- Reject-all with `maxattr` 0: strict parsing fails any attribute with
  `-EINVAL` ("Unknown attribute type"). Under `NL_VALIDATE_LIBERAL` the
  attributes are skipped instead.
- `!ops->policy` is the test for "no parsing", not `maxattr == 0`. A policy
  with `maxattr` 0 is validated and still yields a NULL `info->attrs`.
- `info->attrs` is NULL in the reject-all case with `maxattr` 0 too.
  `GENL_REQ_ATTR_CHECK()` in `include/net/genetlink.h` indexes `info->attrs`
  with no NULL test.

**Header and request flag checks**

- Gate: `genl_header_check()` acts only when
  `hdr->cmd >= family->resv_start_op`. `GENL_DONT_VALIDATE_STRICT` plays no
  part.
- Order: `genl_family_rcv_msg()` calls it before the op lookup, so an
  unknown command at or above `resv_start_op` with a bad header gets
  `-EINVAL`, not `-EOPNOTSUPP`.
- Message length: not checked here. `genl_family_rcv_msg()` tests
  `nlmsg_len` against `nlmsg_msg_size()` of
  `GENL_HDRLEN + family->hdrsize` for every command.
- `nlmsg_flags`: `NLM_F_DUMP` is masked out only when both of its bits are
  set. Any bit left outside `NLM_F_REQUEST | NLM_F_ACK | NLM_F_ECHO` gives
  `-EINVAL`.
- `genlmsghdr.version`: not checked.
- `Documentation/userspace-api/netlink/intro.rst`, "Other
  request-type-specific flags": says only that these flags are "rarely used
  (and considered deprecated for new families)".
- The document gives no advice to use commands or attributes instead, and
  does not mention `resv_start_op`.
- Its per-type remarks: `NLM_F_ROOT` and `NLM_F_MATCH` are used only
  combined as `NLM_F_DUMP`; `NLM_F_ATOMIC` is never used; `NLM_F_NONREC` is
  used only by nftables and `NLM_F_BULK` only by some FDB operations; the
  NEW flags are the most used in classic Netlink and their meaning is
  unclear.

**Permission flags**

- `GENL_ADMIN_PERM`: `netlink_capable()` always checks against
  `&init_user_ns`, whether or not the family sets `netnsok`.
- Opener check: `__netlink_ns_capable()` in `net/netlink/af_netlink.c` skips
  `file_ns_capable()` when the skb has `NETLINK_SKB_DST`.
  `netlink_sendmsg()` sets that flag whenever the sender passed a
  destination address. `ns_capable()` on the current task is always
  required.

**Locks in the core**

- Per-socket dump mutex: `nl_cb_mutex`, embedded in `struct netlink_sock`
  in `net/netlink/af_netlink.h`. There is no cb_def_mutex or dump_cb_mutex
  here, and `struct netlink_kernel_cfg` has no mutex member.
- `genl_mutex` in dumps: `genl_start()`, `genl_dumpit()` and `genl_done()`
  take it with `genl_op_lock()` around the family callback only. There is no
  genl_lock_dumpit(), genl_lock_done() or genl_parallel_done() here.
- Non-parallel family, dump callbacks other than `done` at socket close:
  `nl_cb_mutex` and `genl_mutex` are both held; neither replaces the other.
- `genl_family_rcv_msg_dumpit()`: drops `genl_mutex` around
  `__netlink_dump_start()`. The order is `nl_cb_mutex`, then `genl_mutex`.
- `genl_mutex` is released between `start` and the first round, and between
  rounds.

| Callback | `cb_lock` (read) | `nl_cb_mutex` | `genl_mutex` without `parallel_ops` |
|---|---|---|---|
| `pre_doit`, `doit`, `post_doit` | held | no | held |
| `start`, first `dumpit` round | held | held | held |
| later rounds, from `netlink_recvmsg()` | no | held | held |
| `done` at the end of a dump | as the round it ends | held | held |
| `done` at socket close | no | no | held |

- With `parallel_ops`: the `genl_mutex` column is "no" in every row.
- `done` at socket close: `netlink_release()` calls `nlk->cb.done` directly
  when `cb_running` is set. `netlink_sock_destruct()` does not call it, and
  no deferred work is involved.
- `done` at socket close for a `parallel_ops` family: runs with no core lock
  at all.

**Sending notifications**

- `info->nlhdr` may be NULL: `nlmsg_report()` in `include/net/netlink.h`
  returns 0 for NULL, and `genl_notify()` then only multicasts.
- Requester and the multicast: excluded only when echo is set. Without echo
  `nlmsg_notify()` passes 0 as the port to skip, so a requester that joined
  the group gets the multicast copy.
- Required of `info`: `genl_info_net(info)` must be a valid net;
  `genl_notify()` dereferences it for `genl_sock`.
- `genl_info_init_ntf()`: leaves the net unset. Under `CONFIG_NET_NS`
  `genl_info_net()` then returns NULL; without it `read_pnet()` returns
  `&init_net`.
- **Unsafe usage**: passing a `struct genl_info` set up by
  `genl_info_init_ntf()` to `genl_notify()` without `genl_info_net_set()`.
  - Safe: pass the `struct genl_info` the core gave the handler, as
    `ovs_notify()` in `net/openvswitch/datapath.c` does; the core sets the
    net with `genl_info_net_set()` in `genl_family_rcv_msg_doit()`.

**Multicast helpers and namespaces**

- `genlmsg_multicast_allns()`: has no test of `netnsok`.
- `genlmsg_multicast_allns()` locking: `genlmsg_mcast()` takes
  `rcu_read_lock()` itself and clones with `GFP_ATOMIC`. The kerneldoc in
  `include/net/genetlink.h` says the caller must hold RTNL or RCU;
  `genl_ctrl_event()` calls it without taking either.
- `genlmsg_multicast_allns()` return: 0 only if some netns took the message
  and none failed. An error other than `-ESRCH` from any netns is returned
  even after an earlier delivery. `-ESRCH` if nobody listened.
- `genlmsg_multicast_netns()` and `genlmsg_multicast()`: also reach a socket
  in another netns that set `NETLINK_LISTEN_ALL_NSID`, if that netns has an
  id for the sending net and the socket's opener has `CAP_NET_BROADCAST` in
  the user namespace of the sending net; see `do_one_broadcast()` in
  `net/netlink/af_netlink.c`.
- `genl_has_listeners()`: the listener bitmap is per protocol, in
  `nl_table`, not per netns. `net` only supplies the kernel socket. A
  non-zero result can come from a socket in any netns.
- `genl_has_listeners()` with `group >= n_mcgrps`: returns `-EINVAL`, which
  is non-zero, so a caller that tests the result as a boolean goes on to
  build the message.

## Policies and parsing

**Policy attribute types**

- Rows below are only the types whose checks are easy to get wrong; all are
  in `validate_nla()` in `lib/nlattr.c`.

| Type | Liberal | `NL_VALIDATE_STRICT_ATTRS` | `len` |
|---|---|---|---|
| integer types in `nla_attr_len[]` | at least `len` if non-zero, else at least the `nla_attr_minlen[]` size; a size mismatch only warns | exactly the `nla_attr_len[]` size | non-zero `len` replaces the table minimum, it is not added |
| `NLA_MSECS` | at least 8, or at least `len` if non-zero | same as liberal; never exact | as for integers |
| `NLA_STRING` | at least 1 byte; with non-zero `len`, one trailing NUL is dropped, then at most `len` | same | maximum, one trailing NUL not counted; 0 = no limit |
| `NLA_NUL_STRING` | a NUL among the first min(payload, `len` + 1) bytes, then the `NLA_STRING` checks | same | maximum without the NUL; 0 = NUL anywhere, no limit |

- `NLA_MSECS`: is in `nla_attr_minlen[]` but not in `nla_attr_len[]`, so a
  payload longer than 8 bytes passes strict validation.
- `NLA_NUL_STRING`: bytes may follow the first NUL; the payload need not end
  in NUL.
- There are no NLA_EXACT_LEN or NLA_MIN_LEN types here; exact and minimum
  lengths are `NLA_BINARY` entries with `validation_type`
  `NLA_VALIDATE_RANGE` or `NLA_VALIDATE_MIN`, built by
  `NLA_POLICY_EXACT_LEN()` and `NLA_POLICY_MIN_LEN()`.

**Policy initialiser macros**

- `NLA_POLICY_RANGE()`, `NLA_POLICY_MIN()`, `NLA_POLICY_MAX()`: also accept
  `NLA_MSECS`; see `NLA_ENSURE_INT_OR_BINARY_TYPE()`.
- `NLA_POLICY_FULL_RANGE()`: accepts `NLA_MSECS`, `NLA_UINT`, `NLA_BE16` and
  `NLA_BE32` as well as the fixed unsigned types and `NLA_BINARY`.
- `NLA_POLICY_MASK()`: accepts `NLA_BE16`, `NLA_BE32` and `NLA_UINT`; refuses
  `NLA_MSECS` and `NLA_BINARY`; see `__NLA_IS_UINT_TYPE()`.
- There is no NLA_POLICY_MAX_BE() here; big-endian attributes use the
  ordinary range and mask macros, and the value is compared after `ntohs()`
  or `ntohl()`.
- `NLA_POLICY_VALIDATE_FN()`: build error for `NLA_BITFIELD32`, `NLA_REJECT`,
  `NLA_NESTED` and `NLA_NESTED_ARRAY`; its optional third argument sets `len`.
- `NLA_POLICY_EXACT_LEN()`, `NLA_POLICY_EXACT_LEN_WARN()`,
  `NLA_POLICY_MIN_LEN()`, `NLA_POLICY_MAX_LEN()`: take no type argument and
  always produce `NLA_BINARY`.
- `NLA_POLICY_EXACT_LEN_WARN()`: a payload that is too long passes with a
  warning unless `NL_VALIDATE_STRICT_ATTRS` is set; a payload that is too
  short fails in both modes.
- `NLA_POLICY_ETH_ADDR`, `NLA_POLICY_ETH_ADDR_COMPAT`: object-like macros, no
  parentheses; they are the exact and the warn form for `ETH_ALEN`.
- The macros make no build-time check of the bounds; `__NLA_ENSURE()` tests
  the type only.
- Bound above 32767 on an unsigned type: truncated into the `s16`; if it
  lands negative, `nla_get_range_unsigned()` hits `WARN_ON_ONCE()` at run
  time, and the range it returns is wrong either way.
- `NLA_REJECT` has no initialiser macro; entries are written
  `{ .type = NLA_REJECT }`, optionally with `.reject_message`.

**String attributes**

- `NLA_NUL_STRING` with non-zero `len`: `strlen()` of `nla_data()` is at most
  `len`, so a `len` + 1 byte buffer holds it; `ethnl_parse_header_dev_get()`
  in `net/ethtool/netlink.c` reads it in place.
- `NLA_NUL_STRING` with `len` 0: the string is bounded only by `nla_len()`.
- The NUL guarantee exists only if a parse with that policy entry ran over
  the attribute; a `NULL` policy or a bare for-each walk gives none.
- `nla_strscpy()`: copies by payload length, not up to the first NUL; it
  drops one trailing NUL only, so embedded NULs are copied and counted in the
  return value.
- `nla_strscpy()` into a buffer of policy `len` + 1 bytes: cannot truncate,
  so the return value may be ignored, as `rtnl_dev_get()` in
  `net/core/rtnetlink.c` does.
- `nla_strscpy()` with policy `len` 0 or larger than the buffer minus one:
  can truncate, and then returns `-E2BIG`; the destination is still
  terminated.
- `nla_strscpy()` with `dstsize` above `U16_MAX`: `WARN_ON_ONCE()` and
  `-E2BIG`, nothing copied.
- `nla_strdup()`: allocates the payload length less one trailing NUL, plus 1;
  with no policy `len` the sender chooses the allocation size.
- `nla_strscpy()`, `nla_strdup()`, `nla_strcmp()`: dereference the attribute;
  the caller tests the `tb[]` slot for `NULL` first.

**Validation strictness**

- There is no nlmsg_validate() here; the only message-level validate helper
  is `nlmsg_validate_deprecated()`, which is liberal.
- `genlmsg_parse()` is `NL_VALIDATE_STRICT` and `genlmsg_parse_deprecated()`
  is `NL_VALIDATE_LIBERAL`; both are in `include/net/genetlink.h`.
- `nla_parse_nested()`: `NL_VALIDATE_STRICT` plus its own `NLA_F_NESTED` test
  on the container.
- `NULL` policy under a strict entry point: only the maxtype and trailing
  checks run; `__nla_validate_parse()` does not call `validate_nla()`.
- `strict_start_type`: there is no macro for it; entry 0 is written by hand,
  for example `[NDA_UNSPEC] = { .strict_start_type = NDA_NH_ID }` in
  `net/core/neighbour.c`.
- `strict_start_type` at the same level: adds the per-attribute checks only;
  trailing bytes and types above maxtype stay as the entry point chose.
- `strict_start_type` and a nested attribute at or above it that has a
  `nested_policy`: `validate_nla()` passes the upgraded flags into the nest,
  so the nest's contents get all five checks.
- Per-operation flags go in the `validate` field of the op, not in `flags`.
- `validate` flag on a command at or above `resv_start_op`:
  `genl_validate_ops()` fires `WARN_ON()` as well as returning the `-EINVAL`
  given under "Family registration".

**Dump validation flag**

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

**Unknown attributes**

- Type 0 or above maxtype under `NL_VALIDATE_MAXTYPE`: `-EINVAL` with "Unknown
  attribute type", from `__nla_validate_parse()`; "Unsupported attribute" is
  the `NLA_UNSPEC` message from `validate_nla()`.
- `strict_start_type` and a policy hole at or above it: rejected as
  `NLA_UNSPEC` even from a liberal entry point such as
  `nlmsg_parse_deprecated()`.
- Policy array size: must have at least maxtype + 1 entries; `validate_nla()`
  indexes `policy[type]` for any type up to the maxtype the caller passed.

**Nested attributes**

- Handler's `nla_parse_nested()` policy: may be `NULL` when the outer policy
  entry already validated the nest with the same maxtype, as
  `nl80211_parse_mbssid_config()` in `net/wireless/nl80211.c` does.
- Nest validation flags: the nest is validated with the flags of the outer
  parse, made strict for a type at or above `strict_start_type`, but
  `nla_parse_nested()` in the handler is always `NL_VALIDATE_STRICT`.
- Outer parse liberal, handler uses `nla_parse_nested()`: the handler can
  reject a nest the outer parse accepted, for a missing `NLA_F_NESTED`, an
  unknown type, trailing bytes or an over-long integer.
- `{ .type = NLA_NESTED }` with no `nested_policy`: nothing inside the nest
  is validated; the contents reach the handler unchecked.
- `NLA_NESTED_ARRAY`: `nla_validate_array()` skips zero-length elements and
  never tests `NLA_F_NESTED` on an element; the handler's `nla_parse_nested()`
  on each element does.

**Repeated attributes**

- `struct nla_policy` and `lib/nlattr.c` have no multi-attribute notion;
  `tb[type]` is the last instance for every policy.
- Parse with a policy: every instance passes `validate_nla()` during the
  parse, so a later walk over the same stream reads validated attributes.
- `genlmsg_data()` and `genlmsg_len()`: skip only `GENL_HDRLEN`; they are the
  right walk bounds only for a family whose `hdrsize` is 0.
- Family with a user header: walk with `nlmsg_for_each_attr()` and pass
  `GENL_HDRLEN` plus `hdrsize` as the header length.
- Top-level walk, for example: `dpll_pin_set_from_nlattr()` in
  `drivers/dpll/dpll_netlink.c`, `netdev_nl_read_rxq_bitmap()` in
  `net/core/netdev-genl.c`, `br_vlan_rtm_process()` in `net/bridge/br_vlan.c`.
- Walk inside a nest, for example: `br_afspec()` in
  `net/bridge/br_netlink.c`.
- More users: search for `nla_for_each_attr_type`,
  `nlmsg_for_each_attr_type` and `nla_for_each_nested_type`.

**Policy types and accessor helpers**

- Generated policies: files marked "YNL-GEN kernel source", for example
  `net/core/netdev-genl-gen.c` and `net/devlink/netlink_gen.c`; they hold the
  policy and the op table, the handlers' get and put calls are hand-written.
- 8-, 16- and 32-bit getters, and `nla_get_le64()`: dereference `nla_data()`
  at full width with no look at `nla_len()`.
- `nla_get_u64()`, `nla_get_s64()`, `nla_get_be64()`, `nla_get_msecs()`,
  `nla_get_in6_addr()`, `nla_get_bitfield32()`: copy with `nla_memcpy()`, so a
  short payload is zero-filled, not over-read; the value is silently wrong.
- `nla_get_uint()`, `nla_get_sint()`: pick the 32-bit getter when `nla_len()`
  is 4, else the 64-bit one.
- Range and mask checks use the byte order of the policy type: an `NLA_U16`
  entry is compared in host order, an `NLA_BE16` entry after `ntohs()`.
- Policy `NLA_U16` or `NLA_U32` with a range or mask, read with
  `nla_get_be16()` or `nla_get_be32()`: the bound was tested on the
  host-order value, which is byte-swapped on a little-endian machine.
- **Potentially unsafe usage**: a dereferencing getter wider than the length
  the policy guarantees.
  - Unsafe: when nothing before the call bounds `nla_len()` from below: a
    narrower integer type, `NLA_BINARY` or `NLA_UNSPEC` with no minimum, a
    `NULL` policy, or a for-each walk with no parse; the read runs past the
    payload.
  - Safe: a parse ran with a policy entry whose type is an integer at least
    as wide as the getter and whose `len` is 0 or at least that width;
    `nla_attr_minlen[]` in `lib/nlattr.c` defines the minimum, as
    `netdev_nl_dev_get_doit()` in `net/core/netdev-genl.c` relies on for
    `NETDEV_A_DEV_IFINDEX`.
  - Safe: the code tests `nla_len()` itself before the get, as
    `ip_metrics_convert()` in `net/ipv4/metrics.c` does.

## Dumps

**Dump lifecycle**

- Negative dumpit return: ends the dump and becomes the `int` payload of
  `NLMSG_DONE`; `sk->sk_err` is not touched and no `NLMSG_ERROR` is sent.
- `-EMSGSIZE` with `skb->len != 0`: rewritten to `skb->len`, so it means
  "more to come"; it ends the dump only when returned with an empty skb.
- `NLMSG_DONE` that does not fit: the skb goes out without it, and the next
  round writes only `NLMSG_DONE`; `cb->dump` is not called again, because it
  is called only while `nlk->dump_done_errno > 0`.
- `netlink_dump()` failing by itself in a round run from `netlink_recvmsg()`
  (`-ENOBUFS` on allocation failure or a full receive buffer):
  `netlink_recvmsg()` puts that in `sk->sk_err`; the dump stays running,
  `done` is not called, and a later read that dequeues a message can retry.
- Extack TLVs on `NLMSG_DONE`: gated by `NETLINK_F_EXT_ACK` on the socket in
  `netlink_ack_tlv_len()`; `NLM_F_ACK_TLVS` is the flag set on the result.
- `cb->extack` in `start`: `control->extack`, NULL when the caller of
  `netlink_dump_start()` set none; in `done`: NULL.
- `struct netlink_callback`: embedded in `struct netlink_sock` as `cb` and
  cleared with `memset()`, not allocated; it has no `start` member, only
  `struct netlink_dump_control` does.
- rtnetlink: `rtnl_dumpit()` in `net/core/rtnetlink.c` wraps the handler and
  takes `rtnl_lock()` unless `RTNL_FLAG_DUMP_UNLOCKED`.
- `RTNL_FLAG_DUMP_SPLIT_NLM_DONE`: `rtnl_dumpit()` turns a 0 return with data
  in the skb into `skb->len` and returns 0 on the next call without calling
  the handler, so `NLMSG_DONE` arrives in its own message.

**Buffer size for a round**

- `NLMSG_GOODSIZE`: `SKB_WITH_OVERHEAD(PAGE_SIZE)` only when `PAGE_SIZE` is
  below 8192, otherwise `SKB_WITH_OVERHEAD(8192UL)`; see
  `include/linux/netlink.h`.
- 32 KiB cap: applies only to `nlk->max_recvmsg_len`, in
  `netlink_recvmsg()`; `cb->min_dump_alloc` is not capped by
  `netlink_dump()`, for example `crypto/crypto_user.c` passes up to 65535.
- Tailroom the dumpit sees: exactly the size chosen, because `skb_reserve()`
  in `netlink_dump()` hides what the allocator rounded up.
- Receive buffer test: the skb is charged to `sk->sk_rmem_alloc` first; the
  round fails with `-ENOBUFS` only if something else was already charged and
  the total reaches `sk->sk_rcvbuf`, so one skb larger than `sk_rcvbuf`
  passes on an empty queue.
- Raising `cb->min_dump_alloc` during the dump: honoured, `netlink_dump()`
  reads it every round.
- Pattern for an object found too large: raise `cb->min_dump_alloc`, leave
  the skb empty, return a positive value; the next round retries with the
  larger skb, as `nl80211_dump_wiphy()` and `nl802154_dump_wpan_phy()` do.
- That retry round: user space reads a zero-length datagram, since
  `__netlink_sendskb()` queues the empty skb.
- Growing in the same round: `__inet_diag_dump()` in `net/ipv4/inet_diag.c`
  calls `pskb_expand_head()` on the empty skb and runs the handler again.
- rtnetlink: there is no calcit op in this tree; `rtnetlink_rcv_msg()` calls
  `rtnl_calcit()` directly and only for `RTM_GETLINK`, other rtnetlink dumps
  start with `min_dump_alloc` 0.

**Dump state between rounds**

- `cb->ctx`: `u8 ctx[NETLINK_CTX_SIZE]` (48) in an anonymous union with
  `long args[6]`; it has no alignment attribute of its own.
- `ctx` is the last member of `struct netlink_callback`, so an overrun lands
  in what follows `cb` in `struct netlink_sock`.
- Size check: `NL_ASSERT_CTX_FITS()` in `include/linux/netlink.h`; there is
  no NL_ASSERT_DUMP_CTX_FITS.
- The check is opt-in: nothing fails if a dumper casts `cb->ctx` without it;
  an open-coded `BUILD_BUG_ON(sizeof(*ctx) > sizeof(cb->ctx))` is the same
  check, for example in `net/ipv4/nexthop.c`.
- `struct genl_dumpit_info`: two members, `op` and an embedded
  `struct genl_info info`; the family is `info.family`.
- `genl_dumpit_info()` and `genl_info_dump()` return `const` pointers.
- `struct genl_info` of a dump: `genl_start()` sets every member; its own
  `ctx` / `user_ptr` union is zeroed and is not the dump position.
- `genl_info_dump(cb)->extack`: copied from `cb->extack` by `genl_start()`,
  by `genl_dumpit()` before each round and by `genl_done()`, so it has the
  values given under "Dump lifecycle", NULL in the family's `done`.
- Attribute release: `genl_done()` frees `attrs` and the
  `struct genl_dumpit_info`; there is no genl_parallel_done() here.
- `cb->data` under rtnetlink: holds the real handler whenever
  `rtnetlink_dump_start()` installs `rtnl_dumpit()`;
  `rtnetlink_dump_start()` warns if `control->data` was already set.

**Dump consistency**

- `NLM_F_DUMP_INTR` is not sticky: `nl_dump_check_consistent()` overwrites
  `cb->prev_seq` on every call, so only the first message checked after the
  counter changed carries the flag; user space has to test every message.
- `NLMSG_DONE` is checked too: `netlink_dump_done()` calls
  `nl_dump_check_consistent()` on it, so the flag can appear on a message the
  dumper never built.
- Counter names: there is no genl_ctrl_seq here; `fib_seq` is the FIB
  notifier's counter (for example `net/ipv4/fib_notifier.c`) and is never
  assigned to `cb->seq`. Search for assignments to `cb->seq` to find the
  dump counters.
- A value built from several counters can be 0 even if none of them is:
  `inet_base_seq()` in `net/ipv4/devinet.c` adds two and substitutes
  `0x80000000` for a 0 sum.
- Other ways in-tree code keeps the value non-zero, for example:
  `dev_base_seq_inc()` in `net/core/dev.c` replaces a wrapped 0 with 1;
  `net/batman-adv/` stores `generation << 1 | 1`.
- Writing 0 to both `cb->seq` and `cb->prev_seq` is the reset used when one
  dump moves on to an independent set, as `rtnl_dump_all()` and
  `rtnl_mdb_dump()` do; it is not a counter value.

## Extended ACK

**Extended ACK helpers**

- `NL_SET_ERR_MSG()` argument: must be a string literal, or a macro that
  expands to one; it initialises `static const char __msg[]`, so a
  `const char *` variable does not compile. There is no __NL_SET_ERR_MSG()
  in this tree.
- `NL_SET_ERR_MSG_FMT()` `fmt` argument: must also be a string literal, since
  it is pasted between `"%s"` literals.
- `NL_SET_ERR_MSG_FMT()` truncation: logged with `net_warn_ratelimited()`,
  with the untruncated text; it is not a `WARN_ON()`.
- `NL_SET_ERR_MSG_FMT_MOD()`: the `KBUILD_MODNAME ": "` prefix counts against
  the `NETLINK_MAX_FMTMSG_LEN` bytes.
- NULL extack, `NL_SET_ERR_MSG()` and `NL_SET_ERR_MSG_ATTR_POL()`:
  `do_trace_netlink_extack()` still runs; only the stores are skipped.
- NULL extack, `NL_SET_ERR_MSG_FMT()` and `NL_SET_ERR_MSG_ATTR_POL_FMT()`:
  nothing runs, not even the tracepoint.
- `NL_SET_BAD_ATTR()`: writes `bad_attr` and also `policy = NULL`, so it
  clears a policy recorded earlier; `NL_SET_ERR_MSG_ATTR()` does the same.

**Delivery to user space**

- `NLM_F_CAPPED` and TLVs: independent; `netlink_ack()` appends the TLVs
  after the echoed payload when there is one, after the request header when
  capped.
- `NLMSGERR_ATTR_POLICY`: not emitted for a policy type that
  `__netlink_policy_dump_write_attr()` in `net/netlink/policy.c` skips, for
  example `NLA_REJECT` and `NLA_UNSPEC`.
- `NLMSG_DONE` TLVs: `netlink_dump_done()` uses `netlink_ack_tlv_len()` and
  `netlink_ack_tlv_fill()` with `nlk->dump_done_errno`, so a failed dump
  carries the offset, policy and missing-attribute TLVs too, and a
  successful one only message and cookie.
- Condition for `NLMSG_DONE` to carry anything: the extack is a zeroed local
  of `netlink_dump()`, so only what the `->dump()` call of the same
  `netlink_dump()` invocation set is sent.
- Extack set by a `->dump()` call that returns a positive value, or
  `-EMSGSIZE` with data in the skb: discarded.
- No tailroom for `NLMSG_DONE` (header plus errno) in that skb: `NLMSG_DONE`
  is built by the next `netlink_dump()` call, which does not call `->dump()`
  again, so the errno arrives without TLVs.
- `RTNL_FLAG_DUMP_SPLIT_NLM_DONE`: `rtnl_dumpit()` in `net/core/rtnetlink.c`
  returns `skb->len` for a final 0, so an extack set by a handler that
  returned 0 after writing data is not delivered.
- TLVs larger than the remaining `skb_tailroom()`: `netlink_dump_done()` sets
  `NLM_F_ACK_TLVS` and writes no TLVs.
- `->start()`: `cb->extack` is the `extack` member of
  `struct netlink_dump_control`, which `genl_family_rcv_msg_dumpit()` fills
  and `rtnetlink_rcv_msg()` leaves NULL.
- `->start()` that returns 0: its extack is dropped when the first
  `netlink_dump()` call returns 0, because `__netlink_dump_start()` then
  returns `-EINTR` and `netlink_rcv_skb()` sends no ACK.

**Attribute pointer and message text**

- Range check for `bad_attr` and `miss_nest`: `nlmsg_check_in_payload()` in
  `net/netlink/af_netlink.c` bounds the pointer by the one request message,
  from `nlmsg_data(nlh)` up to but excluding `nlh` plus `nlh->nlmsg_len`; it
  does not use the skb bounds.
- Pointer into another message of the same skb: fails the check.
- Failed check: `WARN_ON()` fires and only that offset TLV is skipped;
  message, `NLMSGERR_ATTR_POLICY` and `NLMSGERR_ATTR_MISS_TYPE` are still
  sent.
- **Unsafe usage**: `bad_attr` or `miss_nest` pointing at a
  `struct nlattr` outside the request message that is being acked.
  - Safe: a pointer from the attribute table parsed from the request `nlh`,
    as `genl_family_rcv_msg_attrs_parse()` produces; `nlmsg_check_in_payload()`
    defines the range.
- Message lifetime with the macros: not a concern; the literal forms store a
  `static` array and the `_FMT` forms store `_msg_buf`.
- Direct store to `_msg`: the string must live until `netlink_ack()` or
  `netlink_dump_done()` reads it with `strlen()`; `validate_nla()` in
  `lib/nlattr.c` stores `reject_message` of the policy entry for
  `NLA_REJECT`.
- **Unsafe usage**: copying a `struct netlink_ext_ack` by value after an
  `_FMT` macro set the message, then using the copy once the original is
  reused or gone; `_msg` of the copy points at `_msg_buf` of the original.
  - Safe: pass the same struct by pointer until the ACK is built, as
    `netlink_rcv_skb()` does with its local extack and `netlink_ack()`.
- Trailing newline in the message: flagged by
  `scripts/coccinelle/misc/newline_in_nl_msg.cocci`.
- `Documentation/userspace-api/netlink/intro.rst`, Extended ACK section: is
  addressed to user space and states no requirement on a family.
- What it tells user space: `NLMSGERR_ATTR_MSG` is a message in English
  describing the problem; `NLMSGERR_ATTR_OFFS` points to the attribute that
  caused the problem; an extended ACK on success is to be treated as a
  warning.
- Not in `intro.rst`: any rule about parsing the text, punctuation, or
  restating the errno.

## uAPI design rules

**Frozen properties**

- `Documentation/userspace-api/netlink/intro.rst`: contains no list of frozen
  properties and no list of permitted changes.
- Explicit freeze statements in the documents: "Answer requests" in
  `Documentation/core-api/netlink.rst` (reply versus ACK is uAPI), and
  `version` in `Documentation/userspace-api/netlink/genetlink-legacy.rst`
  ("compatibility breaking changes are generally not allowed").
- Family ID and multicast group ID: not fixed, except for the few families
  that `genl_register_family()` and `genl_validate_assign_mc_groups()` in
  `net/netlink/genetlink.c` special-case; otherwise the ID is allocated at
  registration, and user space resolves both by name through
  `CTRL_CMD_GETFAMILY`.
- `CTRL_ATTR_MAXATTR` in the `CTRL_CMD_GETFAMILY` reply: `ctrl_fill_info()`
  writes `family->maxattr`; a family that sets policy only per operation, for
  example the generated `netdev_nl_family` in `net/core/netdev-genl-gen.c`,
  reports 0.
- Per-operation attribute support: available only from `CTRL_CMD_GETPOLICY`
  for such a family.
- Probing by sending an attribute and reading the error: works only where the
  core validates strictly; `genl_family_rcv_msg_attrs_parse()` uses
  `NL_VALIDATE_LIBERAL` when the op sets `GENL_DONT_VALIDATE_STRICT`
  (`GENL_DONT_VALIDATE_DUMP_STRICT` for a dump), and parses nothing when the
  op has no policy.
- `version`: not a discovery mechanism;
  `Documentation/userspace-api/netlink/intro.rst` calls the header field
  irrelevant, and of the four schema files only
  `Documentation/netlink/genetlink-legacy.yaml` has a `version` property, so a
  `genetlink` spec always renders 1.

**Reply versus ACK**

- What to return: "information identifying the created object such as the
  allocated object's ID".
- Strength of the guidance: "Try to find useful data to return" and "better
  to err on the side of replying"; an ACK-only command is not forbidden.
- `Documentation/userspace-api/netlink/specs.rst`: lets a SET `do` omit the
  reply section when the kernel answers with the error code alone.
- Scope of the specific rule: NEW and ADD commands; a command that changes an
  object is covered only by the general sentence.
- Echo in "Answer requests": the only text is the parenthesis "(without
  having to resort to using `NLM_F_ECHO`)"; the document gives no reason.
- Separate "NLM_F_ECHO" section: pass the request info to `genl_notify()` so
  the flag takes effect; described as useful for precise feedback, for
  example logging.
- `genl_notify()` in `net/netlink/genetlink.c`: the helper that honours
  `NLM_F_ECHO`, through `nlmsg_report()` on `info->nlhdr`.
- `genlmsg_multicast()` in `include/net/genetlink.h`: takes no
  `struct genl_info`, so a notification sent with it is never echoed.
- `Documentation/userspace-api/netlink/intro.rst`, "Notification echo":
  states the feature "is not universally implemented".

**Command and attribute numbering**

- Notifications: get command IDs separate from requests and replies; only the
  request and its reply share an ID.
- Reason given for the shared ID: easier to match request and reply, and
  "we have plenty of ID space".
- Reason given for separate notification IDs: easier to sort notifications
  from replies and present them through a different API.
- Model names: `unified` and `directional`; there is no "classic" model.
- New family: `unified`; `Documentation/netlink/genetlink.yaml` and
  `Documentation/netlink/genetlink-c.yaml` accept no other `enum-model`.
- `unified`: one enumeration for all messages; notification IDs come from the
  same space as request IDs.
- Value 0 in a new family: no `unspec` entry is defined at all; the first
  attribute and the first command are 1, as in `include/uapi/linux/netdev.h`.
- Reason given for dropping `unspec`: the values "are not used in practice"
  (`Documentation/core-api/netlink.rst`);
  `Documentation/userspace-api/netlink/specs.rst` adds that entry 0 "is
  almost always reserved as undefined".
- Sending 0 by mistake: not a reason either document gives.

**Numbering in existing families**

- Neither document states a rule for adding to an existing family; the
  `unspec` advice in `Documentation/core-api/netlink.rst` is addressed to new
  families.
- Nearest statement: the `unspec` value 0 of older families "is supported
  (`type: unused`) but should be avoided in new families".
- `value-start`: a property of `definitions` entries (`enum`, `flags`) only;
  attributes and operations are numbered with per-entry `value`.
- `value` omitted: the entry takes the previous value plus one, so an entry
  appended to the list continues the existing numbering.
- `enum-model`: one property of `operations` for the whole family; a spec
  cannot give one operation a different model.
- `directional` family, `value` omitted: `_dictify_ops_directional()` in
  `tools/net/ynl/pyynl/lib/nlspec.py` continues the request and the
  from-kernel counters separately; explicit values are not required.

**Attribute design preferences**

| Topic | Preference | Reason the documents state |
|---|---|---|
| Array | `multi-attr`: the attribute itself repeats, no wrapper nest | "(no extra nesting)"; the `indexed-array` wrapper limits the array to 64kB |
| C structure | one attribute per member | `Documentation/userspace-api/netlink/intro.rst`: structures "caused problems with validation and extensibility" |
| Integer width | `sint` / `uint` over fixed-width types "in majority of cases" | none stated |
| Narrower than 32 bits | avoid | no memory saved in the message, due to alignment |

- Per-element extension and "the index carries no meaning": not reasons the
  documents give for `multi-attr`.
- C layout or padding: not a reason the documents give against structures.
- `sint` / `uint` and alignment:
  `Documentation/userspace-api/netlink/specs.rst` warns that the full 64 bit
  value may be unaligned; avoiding alignment problems is not a stated benefit.
- `nla_put_uint()` and `nla_put_sint()` in `include/net/netlink.h`: emit the
  8-byte form with `nla_put()`, not `nla_put_64bit()`, so no pad attribute is
  added.
- `type-value` nesting:
  `Documentation/userspace-api/netlink/genetlink-legacy.rst` says modern
  families should use a flat structure, "the nesting serves no good purpose".

## Specs and generated code

**Schema levels**

- `protocol` (top-level property, default `genetlink`) selects the level;
  `SpecFamily.__init__()` in `tools/net/ynl/pyynl/lib/nlspec.py` loads
  `<protocol>.yaml` from the parent of the spec's directory.
- Specs carry no `$schema` line; under `Documentation/netlink/` `$schema`
  appears only inside the four schema files.
- The schema files are not strict supersets: `genetlink-c.yaml` and
  `netlink-raw.yaml` accept only `admin-perm` under `flags`;
  `genetlink.yaml` and `genetlink-legacy.yaml` also accept
  `uns-admin-perm`.
- `netlink-raw.yaml`: accepts only `netlink-raw` as `protocol`.
- `genetlink.yaml` already accepts `name-prefix` and `enum-name` on
  attribute sets and on `operations`; `genetlink-c.yaml` adds the remaining
  C naming properties, marked by "Start genetlink-c" comments.
- No spec under `Documentation/netlink/specs/` declares `genetlink-c`.
- `make -C tools/net/ynl schema_check`: runs
  `./pyynl/cli.py --spec <spec> --validate` on each `*.yaml` in
  `Documentation/netlink/specs/` and prints `ok` or `not ok` per spec.
- `schema_check` exit status: 0 even when a spec fails, because the recipe
  is one shell loop that ends with the counter increment; read the output.
- `make -C tools/net/ynl lint`: runs only `yamllint` on
  `Documentation/netlink/specs/`; it lints neither the schema files nor the
  Python tools.
- yamllint configuration: none for the specs; the only `.yamllint` in the
  tree is `Documentation/devicetree/bindings/.yamllint`.

**Generated kernel code**

- Marker match: `ynl-regen.sh` uses `git grep`, so it finds only files
  tracked by git; a new generated file needs the two marker lines and a
  `git add` first (see `Documentation/userspace-api/netlink/intro-specs.rst`).
- Marker layout: `/* YNL-GEN <mode> <type> */` must start a line, and the
  spec path must be the comment on the line directly before it.
- Modes: `kernel`, `uapi` and `user`; uAPI headers under `include/uapi/`
  carry `/* YNL-GEN uapi header */` and are regenerated the same way.
- `/* YNL-ARG ... */`: a separate line that holds `--user-header`,
  `--exclude-op` and `--function-prefix`; `ynl-regen.sh` passes it on
  verbatim, for example in `drivers/net/wireguard/generated/netlink.c`.
- `/* To regenerate run: tools/net/ynl/ynl-regen.sh */`: written by `main()`
  in `tools/net/ynl/pyynl/ynl_gen_c.py` into every generated file.
- Skip test: compares the file's mtime with the spec's only; a change to
  `ynl_gen_c.py` regenerates nothing without `-f`.
- Family struct gate: `kernel_can_gen_family_struct()`, true only for
  `protocol` `genetlink`; the op table and policies have no such gate.

| Level | Op policies | Op table | `struct genl_family` |
|---|---|---|---|
| `genetlink` | static | static, `[]` | emitted |
| `genetlink-c` | static | exported, sized | not emitted |
| `genetlink-legacy` | static if `split`, else exported | exported, sized | not emitted |
| `netlink-raw` | no kernel file in tree | no kernel file in tree | not emitted |

- Exported op table: `const`, with an explicit element count, declared
  `extern` in the generated header; the hand-written family points at it,
  as `net/mptcp/pm_netlink.c` does with `mptcp_pm_nl_ops`.
- Policies of nested attribute sets used in a request: exported and
  declared in the header at every level, including `genetlink`.
- `netlink-raw`: the kernel-mode path of `main()` has no test that refuses
  it; no committed kernel file is generated from a netlink-raw spec.

**The kernel-policy property**

- Values: `split`, `per-op`, `global`; there is no other value.

| Value | Policies | Op table |
|---|---|---|
| `global` | one, over the request attributes of all ops | `struct genl_small_ops` |
| `per-op` | one per op and mode that has a request, as under `split` | `struct genl_ops` |
| `split` | one per op and mode that has a request | `struct genl_split_ops` |

- `global`: `_load_global_policy()` raises unless every op that has an
  `attribute-set` uses the same one.
- `global`: op table entries carry no policy; the hand-written
  `struct genl_family` must set `.policy` and `.maxattr`, as
  `net/ipv4/fou_core.c` does with `fou_nl_policy`.
- `per-op`: `print_kernel_op_table()` builds each entry's `.policy` and
  `.maxattr` from the `do` request attributes only.
- `pre` and `post`: put into the op table only under `split`; under `global`
  and `per-op` the generator only declares the hook prototypes in the
  header.

| Source | Default |
|---|---|
| `Documentation/core-api/netlink.rst` | `per-op` |
| `Family.resolve()` in `tools/net/ynl/pyynl/ynl_gen_c.py` | `split` |
| schema description of `kernel-policy` | `split` |

- Accepted by `Documentation/netlink/genetlink-legacy.yaml` and
  `Documentation/netlink/netlink-raw.yaml` only.
- `genetlink.yaml` and `genetlink-c.yaml`: set `additionalProperties: False`
  at the top level, so a spec with `kernel-policy` fails validation and
  those levels always get `split`.

**Attribute checks in a spec**

- Spec-level `checks` properties: `flags-mask`, `min`, `max`, `min-len`,
  `max-len`, `exact-len`, `unterminated-ok`; `range`, `full-range` and
  `sparse` are keys that `_init_checks()` adds and the schema rejects in a
  spec.
- `unterminated-ok`: switches `NLA_NUL_STRING` to `NLA_STRING`;
  `Documentation/netlink/genetlink.yaml` does not accept it, the other three
  schemas do.
- Big-endian `u16`/`u32`: `Type.attr_policy()` changes the type to
  `NLA_BE16`/`NLA_BE32` and uses the same macros; there is no
  NLA_POLICY_MAX_BE in this tree.
- Precedence in `TypeScalar._attr_policy()`: `flags-mask`, a flags enum or
  `enum-as-flags` first, then full range, range, `min`, `max`, sparse enum;
  with a mask, `min` and `max` are dropped silently.
- Limit outside -32768..32767: `NLA_POLICY_FULL_RANGE()` for every scalar
  type; the generator does not emit `NLA_POLICY_FULL_RANGE_SIGNED()`.
- **Unsafe usage**: a signed attribute type with `min` or `max` outside
  -32768..32767, on a request attribute of a spec that kernel code is
  generated from.
  - Unsafe: the generator pairs `NLA_POLICY_FULL_RANGE()` with a
    `struct netlink_range_validation_signed`;
    `NLA_ENSURE_UINT_OR_BINARY_TYPE()` in `include/net/netlink.h` rejects
    the signed type at build time.
  - Safe: an unsigned type, as `NETDEV_A_PAGE_POOL_IFINDEX` (`NLA_U32`) in
    `net/core/netdev-genl-gen.c`; `NLA_ENSURE_UINT_OR_BINARY_TYPE()`
    accepts unsigned types.

| Type | Check | Initialiser |
|---|---|---|
| string | `max-len` | `{ .type = NLA_NUL_STRING, .len = N, }` |
| string | `exact-len` | `NLA_POLICY_EXACT_LEN(N)` |
| string | `min-len` | ignored by `TypeString._attr_policy()` |
| binary | `max-len` | `NLA_POLICY_MAX_LEN(N)` |

- String with `exact-len`: `NLA_POLICY_EXACT_LEN()` has type `NLA_BINARY`,
  so `max-len` and `unterminated-ok` on the same attribute have no effect.
- `Documentation/core-api/netlink.rst` forms for `max-len`: a literal
  integer, the name of a defined constant, and `CONST - 1` for strings.
- `len-or-define` in the schemas: accepts the `CONST - 1` form.
- `get_limit_str()`: handles the integer and the name; it has no handling
  for ` - 1`, and `c_upper()` turns that `-` into `_`.
- No spec under `Documentation/netlink/specs/` uses the `CONST - 1` form.
- `get_limit_str()` on a constant from `definitions`: prints the bare
  upper-case name when the definition has `header`, otherwise the name
  prefixed with the family name.

## Model gaps

### Other mistakes models make

- Models take `nla_nest_end()` to be the only way to close a nest and to be
  unable to fail. It stores the length in the 16-bit `nla_len` and checks
  overflow only with `DEBUG_NET_WARN_ON_ONCE()`; `nla_nest_end_safe()` in
  `include/net/netlink.h` returns `-EMSGSIZE` past `U16_MAX`.
- Models do not know when per-socket private data dies. `netlink_release()`
  calls `genl_release()`, which runs `sock_priv_destroy`, before the `unbind`
  calls and before the `done` of an unfinished dump;
  `genl_unregister_family()` waits for `genl_sk_destructing_cnt` to reach 0.
- Models take a family to set `min_dump_alloc` in
  `struct netlink_dump_control`. `genl_family_rcv_msg_dumpit()` builds that
  struct itself and leaves the field 0; a Generic Netlink dumper can only
  raise `cb->min_dump_alloc`.
- Models expect `kmalloc_array()` and an explicit gfp argument in the core.
  `net/netlink/genetlink.c` uses `kmalloc_objs()`, `kmalloc_obj()` and
  `kzalloc_obj()` from `include/linux/slab.h`; `default_gfp()` supplies
  `GFP_KERNEL` when the argument is left out.
- Models do not know `nlmsg_payload()` in `include/net/netlink.h`: it returns
  the fixed header only if `nlmsg_len` covers the given size, else NULL.
- Models expect the classic socket-op signatures in
  `net/netlink/af_netlink.c`. `netlink_bind()` and `netlink_connect()` take
  `struct sockaddr_unsized *`, and `netlink_getsockopt()` takes `sockopt_t *`.
