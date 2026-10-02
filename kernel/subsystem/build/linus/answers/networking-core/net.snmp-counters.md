- `__SNMP_INC_STATS64()` on a 32-bit build: defined as
  `SNMP_ADD_STATS64(mib, field, 1)`, so it disables BH itself; it is identical
  to `SNMP_INC_STATS64()`.
- `__IP_INC_STATS()` and `__IP6_INC_STATS()`: self-protecting on 32-bit only;
  on 64-bit they are `__this_cpu_inc()`, so callers still need BH off.
- `__SNMP_ADD_STATS64()` and `__SNMP_UPD_PO_STATS64()` on 32-bit: the only
  64-bit forms that do the bare `syncp` write; reached through
  `__IP_ADD_STATS()` and `__IP_UPD_PO_STATS()`.
- `SNMP_ADD_STATS64()` and `SNMP_UPD_PO_STATS64()` on 32-bit: wrap the `__`
  form in `local_bh_disable()` / `local_bh_enable()`.
- Plain 64-bit forms on 32-bit: not usable in hard-irq context or with IRQs
  off; `__local_bh_enable_ip()` in `kernel/softirq.c` has
  `WARN_ON_ONCE(in_hardirq())` and `lockdep_assert_irqs_enabled()`.
- 32-bit `__SNMP_ADD_STATS64()`: uses `raw_cpu_ptr()`, so
  `CONFIG_DEBUG_PREEMPT` does not check it.
- `u64_stats_update_begin()` on 32-bit: calls `preempt_disable_nested()`, which
  disables preemption itself on `CONFIG_PREEMPT_RT` and otherwise only asserts
  it via `lockdep_assert_preemption_disabled()` (`CONFIG_PROVE_LOCKING`).
- `__this_cpu_preempt_check()`: does not test softirq state; see
  `check_preemption_disabled()` in `lib/smp_processor_id.c`. It passes, for
  example, on nonzero `preempt_count()`, IRQs off, or
  `current->migration_disabled`, so a clean debug run does not show the BH
  requirement is met.
- Users of the 64-bit forms: the `IP_` wrappers in `include/net/ip.h` and
  `_DEVINC()` in `include/net/ipv6.h`.
- `SNMP_DEC_STATS()`: has no double-underscore form; `SNMP_DEC_STATS64()` is
  defined only when `BITS_PER_LONG` is not 32.
- **Potentially unsafe usage**: a double-underscore MIB macro in code that can
  run in process context.
  - Unsafe: when BH is enabled at the call; `raw_cpu_generic_to_op()` in
    `include/asm-generic/percpu.h` is an unprotected read-modify-write, and a
    softirq update of the same counter in between is lost.
  - Unsafe: in a receive handler that is also the socket backlog handler;
    `__release_sock()` in `net/core/sock.c` calls `sk_backlog_rcv()` after
    `spin_unlock_bh()`, in process context with BH enabled.
  - Safe: the plain macro in such a handler, as `tcp_v4_do_rcv()` does with
    `TCP_INC_STATS()`; it is `this_cpu_inc()`, whose generic form
    `this_cpu_generic_to_op()` disables IRQs around the update.
  - Safe: inside the caller's own `local_bh_disable()` section, as
    `tcp_v4_send_reset()` and `__napi_busy_loop()` do.
