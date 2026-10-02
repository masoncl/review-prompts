- Source of `conf/all` and `conf/default` in a namespace other than `init_net`:

| `devconf_inherit_init_net` | IPv4, `devinet_init_net()` | IPv6, `addrconf_init_net()` |
|---|---|---|
| 0 (default) | copy of `init_net`'s current values | compiled `ipv6_devconf`, `ipv6_devconf_dflt` |
| 1 | copy of `init_net`'s current values | copy of `init_net`'s current values |
| 2 | compiled `ipv4_devconf`, `ipv4_devconf_dflt` | compiled `ipv6_devconf`, `ipv6_devconf_dflt` |
| 3 | copy of `current->nsproxy->net_ns` | copy of `current->nsproxy->net_ns` |

- Value 0 is not "compiled defaults" for IPv4: `case 0` and `case 1` share one
  branch in `devinet_init_net()`, so host IPv4 tuning reaches every new
  namespace by default.
- Value 3 is valid: the entry in `net_core_table` in
  `net/core/sysctl_net_core.c` has `.extra2 = SYSCTL_THREE`.
- `sysctl_devconf_inherit_init_net`: one global int, not per namespace.
- `net_core_table` is registered for `init_net` only, in `sysctl_core_init()`;
  a test inside its own namespace cannot read or write the file.
- IPv6 `conf/default` `autoconf` and `disable_ipv6`: set from `ipv6_defaults`
  (module parameters in `net/ipv6/af_inet6.c`) after the switch, for every
  value of the sysctl; they are never inherited.
- IPv6 `stable_secret.initialized`: cleared in both copies after the switch,
  for every value.
- IPv4 copy: a `memcpy()` of the whole `struct ipv4_devconf`, so the `state`
  bitmap of the source is inherited along with `data`; see "Pinning per-device
  sysctls" for what that changes.
