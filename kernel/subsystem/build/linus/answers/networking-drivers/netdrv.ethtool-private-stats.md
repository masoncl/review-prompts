- Barred by `Documentation/networking/statistics.rst`: only statistics with a
  matching member in `struct rtnl_link_stats64`; they go "exclusively" through
  `ndo_get_stats64`, and reporting them through ethtool or debugfs "will not
  be accepted".
- Queue statistics, the standard ethtool groups and page pool statistics: the
  notes for driver authors do not bar them from `get_ethtool_stats`.
- Counters reported before a standard interface existed: the document has no
  rule to keep, duplicate or remove them; it only remarks that the ioctl was
  historically used for per-queue and standards-based statistics.
- Number of statistics: drivers "are advised" to keep it constant; this is
  advice, not a requirement.
- Reason given: retrieval takes several system calls, so a changing count
  races with user space. No other reason is given.
- Count mismatch in the kernel: `ethtool_get_stats()` in
  `net/ethtool/ioctl.c` calls `get_sset_count` itself; if user space passed a
  different non-zero `n_stats`, it returns `n_stats` 0 and no values.
- `get_ethtool_stats` kerneldoc in `include/linux/ethtool.h`: "only useful if
  the device maintains statistics not included in" `struct
  rtnl_link_stats64`.
