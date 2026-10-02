- Kinds created without a sysfs PMU directory:

| Kind | Created by | File | `type` |
|---|---|---|---|
| tool | `tool_pmu__new()` | `tools/perf/util/tool_pmu.c` | `PERF_PMU_TYPE_TOOL` |
| hwmon | `perf_pmus__read_hwmon_pmus()` | `tools/perf/util/hwmon_pmu.c` | `PERF_PMU_TYPE_HWMON_START` + N |
| DRM | `perf_pmus__read_drm_pmus()` | `tools/perf/util/drm_pmu.c` | from `PERF_PMU_TYPE_DRM_START` |
| fake | `perf_pmus__fake_pmu()` | `tools/perf/util/pmus.c` | `PERF_PMU_TYPE_FAKE` |
| placeholder core | `perf_pmu__create_placeholder_core_pmu()` | `tools/perf/util/pmu.c` | `PERF_TYPE_RAW` |

- There is no perf_pmus__tool_pmu() and no perf_pmu__fake symbol here.
- `perf_pmus__fake_pmu()`: returns a function-static struct and does not add it
  to `core_pmus` or `other_pmus`.
- Placeholder core PMU: made by `pmu_read_sysfs()` when `core_pmus` is empty
  after the sysfs read; it has `is_core` set and counts as
  `PERF_PMU_KIND_PE`, so no kind test separates it from a sysfs core PMU.
- `perf_pmu__kind()` in `tools/perf/util/pmu.h`: maps `pmu->type` to
  `enum pmu_kind`; compare with `PERF_PMU_KIND_PE` to cover DRM, hwmon, tool
  and fake in one test, as `store_evsel_ids()` does.
- `evsel__is_non_perf_event_open_pmu()` in `tools/perf/util/evsel.c`: the
  evsel form, `evsel->pmu->type > PERF_PMU_TYPE_PE_END`.
- NULL PMU: `perf_pmu__kind()` returns `PERF_PMU_KIND_PE`;
  `perf_pmu__is_tool()`, `perf_pmu__is_hwmon()` and `perf_pmu__is_drm()` return
  false; `perf_pmu__is_fake()` and `perf_pmu__is_tracepoint()` dereference it.
- `attr.type`: `parse_events_add_pmu()` stores `pmu->type` there for every
  kind, so a tool, hwmon or DRM evsel carries the synthetic type in its attr;
  what must be guarded is the syscall, not the assignment.
- Walkers: tool, hwmon and DRM PMUs are put on `other_pmus`, so
  `perf_pmus__scan()` returns them; `perf_pmus__scan_core()` walks `core_pmus`
  only.
- Event lookup in `tools/perf/util/pmu.c`: `perf_pmu__have_event()` and
  `perf_pmu__num_events()` hand off for tracepoint, hwmon and DRM only.
- Tool PMU events: ordinary aliases from the json table named "common" (set
  in `tool_pmu__new()`), filtered by `tool_pmu__skip_event()`.
- Tracepoint PMU: kind `PERF_PMU_KIND_PE`, yet its events come from
  `tools/perf/util/tp_pmu.c`, not from aliases.
