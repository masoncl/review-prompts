- `setup_ns()` in `tools/testing/selftests/net/lib.sh`: writes
  `net.ipv4.conf.all.rp_filter=0` and `net.ipv4.conf.default.rp_filter=0`, and
  pins nothing else; `forwarding`, `accept_local` and every IPv6 value stay as
  they were when the namespace was created.
- `lo` after `setup_ns()`: keeps the `rp_filter` it copied when the namespace
  was created; `setup_ns()` sets `lo` up first, `inetdev_event()` then calls
  `ipv4_devconf_setall()`, and `devinet_copy_dflt_conf()` skips it.
- `test_global_init()` in
  `tools/testing/selftests/bpf/prog_tests/flow_dissector_classification.c`:
  writes `default`, `all` and `lo` `rp_filter`; that pins `rp_filter` for `lo`
  and for devices created afterwards.
- IPv4 `conf/default/X` write: reaches an existing device only while that
  device's bit for X in `state` is clear (`devinet_copy_dflt_conf()`).
- IPv4 `conf/default/forwarding` write: reaches no existing device;
  `devinet_sysctl_forward()` does not call `devinet_copy_dflt_conf()`.
- `state` bit for X on a new device: copied from `conf/default` by
  `inetdev_init()`; it is already set if `devinet_conf_proc()` set it on a
  `conf/default/X` write in this namespace or in the namespace the values
  were inherited from. A `forwarding` write sets no bit in `conf/default`.
- IPv4 `conf/default` write: a test can rely on it only for devices created
  or moved in afterwards.
- Device moved into the namespace: `__dev_change_net_namespace()` in
  `net/core/dev.c` sends `NETDEV_UNREGISTER` then `NETDEV_REGISTER`;
  `inetdev_event()` destroys the `struct in_device` and builds a new one from
  the destination's `conf/default`, so IPv4 per-device values written before
  the move are lost.
- IPv4 `conf/all/forwarding` or `ip_forward` written with the value it already
  has: `devinet_sysctl_forward()` skips `inet_forward_change()`, so no device
  is rewritten.
- `forwarding_enable()` in `tools/testing/selftests/net/forwarding/lib.sh`:
  not a namespace example; that library creates no namespace, the helper
  writes the namespace the script runs in and relies on
  `forwarding_restore()` to put the saved value back.
- No selftest under `tools/` reads or sets `devconf_inherit_init_net`.
- **Potentially unsafe usage**: in a new namespace, writing only
  `conf/<dev>/rp_filter=0` or `conf/<dev>/accept_local=0` to get 0 in effect
  on that device.
  - Unsafe: when nothing has written `conf/all` for that setting in the
    namespace; `IN_DEV_RPFILTER()` and `IN_DEV_ACCEPT_LOCAL()` in
    `include/linux/inetdevice.h` still see the inherited `conf/all` value.
  - Safe: for `rp_filter`, in a namespace made by `setup_ns()`, which already
    wrote `conf/all/rp_filter=0`; `test_tun()` in
    `tools/testing/selftests/net/netfilter/ipvs.sh` writes only
    `conf.tunl0.rp_filter=0` after `setup_ns`.
  - Safe: the test writes `conf/all` for the setting itself, as
    `test_global_init()` does.
