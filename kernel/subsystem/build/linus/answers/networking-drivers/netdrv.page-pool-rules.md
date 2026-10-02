- `allow_direct == false` does not mean "ring only":
  `page_pool_put_unrefed_netmem()` in `net/core/page_pool.c` recycles into
  the lockless cache anyway when `page_pool_napi_local()` is true.
- That upgrade applies to every return path, for example
  `napi_pp_put_page()` (which itself passes `false`), `xdp_return_frame()`
  and a driver's `page_pool_put_full_page(pool, page, false)`;
  `page_pool_put_netmem_bulk()` makes the same test.
- `page_pool_napi_local()`: true only when not `CONFIG_PREEMPT_RT`,
  `in_softirq()`, and this CPU equals the pool's `cpuid` or
  `napi->list_owner`. It has no busy-poll test.
- `cpuid` of `struct page_pool`: -1 from `page_pool_create()`; a real CPU
  only from `page_pool_create_percpu()`.
- `list_owner`: `____napi_schedule()` writes the CPU only when it queues the
  NAPI on the per-CPU poll list; the threaded wake-up path returns before
  that. `napi_complete_done()` resets it to -1.
- Hardirq or IRQs disabled: no page may be returned at all, by either path;
  `__page_pool_put_page()` has `lockdep_assert_no_hardirq()`.
- Ring path from process context: the caller need not disable BH;
  `page_pool_producer_lock()` takes the `_bh` lock itself outside softirq.
- `xdp_return_buff()`, `xdp_return_frag()` and `xdp_return_frame_rx_napi()`
  in `net/core/xdp.c` pass direct = true, so they carry the same context
  rule as `page_pool_recycle_direct()`; `__xdp_return()` drops the direct
  flag only when `xdp_return_frame_no_direct()` is true.
- `page_pool_destroy()` is refcounted by `user_cnt`: only the call that
  drops it to zero tears the pool down; earlier calls just return.
- XDP registration holds one `user_cnt` reference
  (`page_pool_use_xdp_mem()`), and `xdp_unreg_mem_model()` drops it by
  calling `page_pool_destroy()`.
- A pool registered with `xdp_rxq_info_reg_mem_model()` therefore needs both
  `xdp_rxq_info_unreg()` and the driver's own `page_pool_destroy()`, in
  either order.
- The "Driver unload" example in `Documentation/networking/page_pool.rst`
  shows `xdp_rxq_info_unreg()` and no `page_pool_destroy()`; on its own that
  leaves `user_cnt` at 1 and the pool is never torn down.
- `p.napi` is read by `page_pool_napi_local()` on page returns until
  `page_pool_disable_direct_recycling()` clears it; in the core only the
  last `page_pool_destroy()` calls that.
- A driver that frees the `struct napi_struct` before the last
  `page_pool_destroy()` must first call
  `page_pool_disable_direct_recycling()`, after `napi_disable()`;
  `enet_rx_stop()` in `drivers/net/ethernet/alibaba/eea/eea_rx.c` calls it
  between `napi_disable()` and `netif_napi_del()`.
- `page_pool_disable_direct_recycling()` with `p.napi` set: runs
  `napi_assert_will_not_race()` in `net/core/dev.h`, which WARNs unless
  `NAPI_STATE_SCHED` is set and `list_owner` is -1, or the NAPI was never
  added.
- DMA at destroy: the first release pass in `page_pool_scrub()` clears
  `dma_sync` and unmaps every page still recorded in `dma_mapped`,
  in-flight pages included, when `PP_DMA_INDEX_BITS` is non-zero.
- The device must have stopped DMA into pool pages before the last
  `page_pool_destroy()`; a page returned afterwards is only freed.
- `PP_DMA_INDEX_BITS` zero: pages are not tracked; an in-flight page keeps
  its mapping until it comes back to the pool.
- "stalled pool shutdown" warning: `page_pool_release_retry()` prints it
  only when `slow.netdev` is NULL or `NET_PTR_POISON`. A pool created with
  `netdev` set stalls silently; `page_pool_unreg_netdev()` re-points it at
  the loopback device when its netdev unregisters.
