- `nfsd_nl_family`: the family struct in `fs/nfsd/netlink.c`; there is no
  nfsd_genl_family in this tree.
- `Documentation/netlink/specs/nfsd.yaml`: declares `protocol: genetlink`.
- Commands beyond threads, version, listener, pool-mode and rpc-status: cache
  requests, cache-flush, unlock-ip, unlock-filesystem, unlock-export and
  server-stats-get; see `nfsd_nl_ops[]` in `fs/nfsd/netlink.c`.
- Dumps: no entry of `nfsd_nl_ops[]` sets `.start` or `.done`; there is no
  nfsd_nl_rpc_status_get_start(). Each `dumpit` call resumes from `cb->args[]`.
- `NFSD_CMD_CACHE_NOTIFY`: an event, so it has no entry in `nfsd_nl_ops[]` and
  no generated prototype; `nfsd_cache_notify()` in `fs/nfsd/nfsctl.c` sends it
  to group `NFSD_NLGRP_EXPORTD`, reached through the `cache_notify` member of
  `struct cache_detail`.
- Pool-mode commands: `sunrpc_set_pool_mode()` only checks the name against a
  list and stores nothing; `sunrpc_get_pool_mode()` always prints "pernode"
  (`net/sunrpc/svc.c`).
- Neighbouring families, generated the same way: `lockd_nl_family` from
  `Documentation/netlink/specs/lockd.yaml`, handlers in `fs/lockd/svc.c`;
  `sunrpc_nl_family` from `Documentation/netlink/specs/sunrpc_cache.yaml`,
  handlers in `net/sunrpc/svcauth_unix.c`.
- Values are positional: the generator numbers commands, attributes and flag
  bits in spec order, so a new entry goes last in its list.
- **Unsafe usage**: a doit handler reading `info->attrs[X]` where `X` is not
  listed under that operation's `request: attributes:` in the spec.
  - Unsafe: `.maxattr` and the top-level policy are sized by the highest
    listed attribute, not by the attribute set, and
    `genl_family_rcv_msg_attrs_parse()` in `net/netlink/genetlink.c` allocates
    `maxattr + 1` slots; an op with no `.policy` gets `info->attrs == NULL`,
    which `GENL_REQ_ATTR_CHECK()` dereferences.
  - Safe: read only listed attributes, as `nfsd_nl_threads_set_doit()` does;
    adding one to the handler means adding it to the op's request list and
    regenerating.
- Nested attribute sets: handlers parse them again with `nla_parse_nested()`
  into a local `tb[]` whose bound is written by hand. `fs/nfsd/export.c` uses
  the last attribute's name (`NFSD_A_SVC_EXPORT_FSID`, `NFSD_A_EXPKEY_PATH`,
  `NFSD_A_AUTH_FLAVOR_FLAGS`, `NFSD_A_FSLOCATION_PATH`), so appending an
  attribute to one of those sets needs the bound changed too, or the new type
  is rejected with `-EINVAL`.
- `export-flags` and `xprtsec-mode` in the spec: must match, in order and
  count, the export flag bits `NFSEXP_READONLY` through `NFSEXP_PNFS` and the
  bits `NFSEXP_XPRTSEC_NONE`, `NFSEXP_XPRTSEC_TLS` and `NFSEXP_XPRTSEC_MTLS`
  in `include/uapi/linux/nfsd/export.h`.
  `nfsd_nl_parse_one_export()` stores `NFSD_A_SVC_EXPORT_FLAGS` straight into
  `ex_flags`, and the generated `NLA_POLICY_MASK()` value (equal to
  `NFSEXP_ALLFLAGS`) comes from the number of spec entries.
