- Models have this right; see "Notes for driver authors" in
  `Documentation/networking/statistics.rst`.
- The document names no mechanism for the periodic refresh, only that the
  ethtool interrupt coalescing interface can set its frequency; it says
  nothing about how the cached copy is protected or about ethtool statistics
  reads being allowed to sleep.
