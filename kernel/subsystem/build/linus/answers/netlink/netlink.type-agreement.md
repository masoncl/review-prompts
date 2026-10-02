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
