- `u64_stats_update_begin()` on 32-bit, not `CONFIG_PREEMPT_RT`: asserts
  preemption is off, once in `preempt_disable_nested()` and again in
  `__seqprop_assert()` from `write_seqcount_begin()`; it disables nothing.
- `lockdep_assert_preemption_disabled()` in `include/linux/lockdep.h`: an
  empty macro without `CONFIG_PROVE_LOCKING`; with it, warns only when
  `CONFIG_PREEMPT_COUNT` is set, `preempt_count()` is 0 and hardirqs are
  enabled.
- `u64_stats_update_begin()` on 64-bit: empty in every configuration,
  including `CONFIG_PREEMPT_RT`; it neither disables nor asserts.
- Writer exclusion: `seq` is a plain `seqcount_t` with no associated lock, so
  the write path has no `lockdep_assert_held()`; that assertion exists only in
  the `seqcount_LOCKNAME_t` variants in `include/linux/seqlock.h`.
- The per-CPU stats helpers in `include/linux/netdevice.h`, for example
  `dev_sw_netstats_rx_add()`, `dev_lstats_add()` and `dev_dstats_tx_add()`:
  `this_cpu_ptr()` plus plain `u64_stats_update_begin()`; they establish no
  context, the caller must.
- **Potentially unsafe usage**: `u64_stats_update_begin()`, directly or
  through one of the `include/linux/netdevice.h` helpers above.
  - Unsafe: when the caller is preemptible with interrupts enabled; on 32-bit
    without `CONFIG_PREEMPT_RT` a reader that preempts the section spins in
    `__read_seqcount_begin()`, and `preempt_disable_nested()` warns under
    `CONFIG_PROVE_LOCKING`.
  - Safe: per-CPU stats taken with `get_cpu_ptr()` and released with
    `put_cpu_ptr()` after the end call, as `iptunnel_xmit_stats()` in
    `include/net/ip_tunnels.h` does; `get_cpu_ptr()` calls
    `preempt_disable()`, which the assertion in `preempt_disable_nested()`
    accepts.
  - Safe: per-CPU stats inside `local_bh_disable()`, as
    `nft_counter_do_eval()` in `net/netfilter/nft_counter.c` does; without
    `CONFIG_PREEMPT_RT` this raises `preempt_count()`, which the assertion in
    `preempt_disable_nested()` accepts.
  - Safe: shared stats with `preempt_disable()` around the section and an
    outer lock for exclusion, as `mdiobus_stats_acct()` in
    `drivers/net/phy/mdio_bus.c` does; each caller asserts `bus->mdio_lock`
    with `lockdep_assert_held_once()`.
  - Safe: `u64_stats_update_begin_irqsave()`, which meets the assertion in
    `preempt_disable_nested()` by disabling interrupts.
