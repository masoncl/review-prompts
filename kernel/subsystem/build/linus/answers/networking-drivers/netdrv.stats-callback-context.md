- Models have this right; see `dev_get_stats()` in `net/core/dev.c`, which
  takes no lock and makes no test of `netif_running()`.
