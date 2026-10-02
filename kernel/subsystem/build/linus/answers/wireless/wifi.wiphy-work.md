- `struct wiphy_hrtimer_work`: same five operations as
  `struct wiphy_delayed_work`, named `wiphy_hrtimer_work_init()`,
  `wiphy_hrtimer_work_queue()`, `wiphy_hrtimer_work_cancel()`,
  `wiphy_hrtimer_work_flush()`, `wiphy_hrtimer_work_pending()`;
  `CLOCK_BOOTTIME`, relative `ktime_t` delay, 1 ms slack.
- Worker: `cfg80211_wiphy_work()` runs on `system_dfl_wq`.
- While `rdev->suspended` is set the worker returns without running
  anything; items stay queued until `wiphy_resume()` in
  `net/wireless/sysfs.c` queues the worker again.
- `wiphy_delayed_work_queue()` on an armed item: `mod_timer()` moves the
  deadline to the new value, so repeated queueing postpones the handler.
- Flush never drops the wiphy mutex; `cfg80211_process_wiphy_works()` calls
  the handlers inline in the caller.
- `wiphy_delayed_work_flush()` and `wiphy_hrtimer_work_flush()`: delete the
  timer first, then run the handler only if the item is already on the work
  list; with the timer still armed the handler does not run and the item is
  left idle.
- Flush from inside a handler does not deadlock: the running item is taken
  off the list before `func` is called, so flushing itself does nothing.
- `cfg80211_process_wiphy_works()`: after 100 handlers in one call without
  reaching the target it WARNs and empties the list, dropping what is still
  queued.
- Mutex assertion: `wiphy_work_cancel()`, `wiphy_delayed_work_cancel()`,
  `wiphy_hrtimer_work_cancel()`, `wiphy_delayed_work_flush()` and
  `wiphy_hrtimer_work_flush()` assert it on entry; `wiphy_work_flush()`
  asserts it only through `cfg80211_process_wiphy_works()`, reached when
  `work` is NULL or the item is on the list.
- **Unsafe usage**: calling a wiphy work cancel or flush function without
  the wiphy mutex.
  - Safe: under the mutex, as `_cfg80211_unregister_wdev()` does before
    `wiphy_work_cancel()`; the cancel functions assert it.
  - Safe: from inside a wiphy work handler, which `cfg80211_wiphy_work()`
    calls with the mutex held.
- **Unsafe usage**: freeing an object that embeds a wiphy work item while
  the item is queued or its timer is armed.
  - Safe: cancel under the wiphy mutex before the free, as
    `ieee80211_link_stop()` does for `csa.finalize_work` before
    `ieee80211_free_links()` frees the link; `cfg80211_wiphy_work()` calls
    `wk->func` and the timer callbacks read `dwork->wiphy`, and
    `cfg80211_dev_free()` WARNs if the list is not empty.
