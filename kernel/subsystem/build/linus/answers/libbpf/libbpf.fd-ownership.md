- `prog->fd`: one per `struct bpf_program`; there are no program instances in
  this tree.
- `bpf_object_unload()`: closes every `map->fd` and `prog->fd` when prepare or
  load fails, so a borrowed fd is stale before `bpf_object__close()` runs.
- `bpf_program__unload()`: exported; closes `prog->fd` and sets it to -1.
- `bpf_program__clone()`: returns an fd the caller owns and must close; it is
  not stored in `prog->fd`.
- `bpf_program__attach_perf_event_opts()`: the link takes the caller's `pfd`
  on success only; on failure `pfd` is left open for the caller.
- `link->fd` is not always owned by the link:

| Link from | `link->fd` | `link->detach` does |
|---|---|---|
| attach functions that set `bpf_link__detach_fd()`, and `bpf_link__open()` | own link fd | closes `link->fd` |
| `bpf_program__attach_perf_event_opts()` | link fd, or `pfd` itself without `FEAT_PERF_LINK` or with `force_ioctl_attach` | `PERF_EVENT_IOC_DISABLE`, closes `perf_event_fd` and `link->fd`, removes a legacy probe |
| `bpf_map__attach_struct_ops()` with `BPF_F_LINK` | own link fd | closes `link->fd` |
| `bpf_map__attach_struct_ops()` without `BPF_F_LINK` | `map->fd`, borrowed from the map | `bpf_map_delete_elem()`; closes nothing |
| `usdt_manager_attach_usdt()` | never set | destroys the child links it owns |

- `bpf_link__destroy()` after `bpf_link__disconnect()`: closes no fd; neither
  `bpf_link_perf_dealloc()` nor `bpf_link_usdt_dealloc()` closes anything.
- Disconnected perf link: `link->fd` and `perf_event_fd` stay open and a legacy
  probe is not removed.
- Disconnected USDT link: its child links are never destroyed.
- Disconnected struct_ops link without `BPF_F_LINK`: the map element is not
  deleted.
- `bpf_link__pin()` then `bpf_link__destroy()`: destroy still runs
  `link->detach`; a link using `bpf_link__detach_fd()` is left untouched apart
  from the closed fd, but `bpf_link_perf_detach()` still disables the event
  and removes a legacy probe.
- **Potentially unsafe usage**: `close(bpf_link__fd(link))` followed by
  `bpf_link__destroy()`.
  - Unsafe: when the link is not disconnected; `link->detach` closes or uses
    the same number again, or for a USDT link the closed number was never the
    link's.
  - Safe: after `bpf_link__disconnect()`, which makes `bpf_link__destroy()`
    skip `link->detach`, on a link whose `link->fd` is its own link fd, as
    `pe_subtest()` in `tools/testing/selftests/bpf/prog_tests/bpf_cookie.c`
    does.
