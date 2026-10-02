| Hook | Called from | Return value | Sleepable program | Per device |
|---|---|---|---|---|
| `hid_device_event` | `dispatch_hid_bpf_device_event()`, from `__hid_input_report()` | `<0`: walk stops, event dropped, error returned; `0`: size kept; `>0`: new `ctx.size`, seen by the next program | refused by `hid_bpf_ops_check_member()` | up to the ops limit |
| `hid_rdesc_fixup` | `call_hid_bpf_rdesc_fixup()`, from `__hid_device_probe()` | `<0` or above `HID_MAX_DESCRIPTOR_SIZE`: original descriptor kept; `0`: program's buffer used at the old size; `>0`: buffer used at that size | allowed | one |
| `hid_hw_request` | `dispatch_hid_bpf_raw_requests()`, from `__hid_hw_raw_request()` | `0`: next program, then `ll_driver->raw_request()`; nonzero: walk stops, value returned, transport not called | allowed | up to the ops limit |
| `hid_hw_output_report` | `dispatch_hid_bpf_output_report()`, from `__hid_hw_output_report()` | `0`: next program, then `ll_driver->output_report()`; nonzero: walk stops, value returned, transport not called | allowed | up to the ops limit |

- Ops limit: `HID_BPF_MAX_PROGS_PER_DEV` (64) counts `struct hid_bpf_ops` on
  `hdev->bpf.prog_list`, whatever hooks each one fills; there is no per-hook
  count.
- `hid_open_report()`: does not call `hid_rdesc_fixup`; it starts from
  `hdev->bpf_rdesc`, which `__hid_device_probe()` filled before the driver's
  `probe`.
- `hid_hw_request()` in `drivers/hid/hid-core.c`: runs the `hid_hw_request`
  hook only through `__hid_request()`; when the transport has
  `ll_driver->request`, the hook is not run.
- `hid_device_event` size check: made once after the walk; a final `ctx.size`
  above `allocated_size` gives `-EINVAL`.
- `from_bpf` in `struct hid_bpf_ctx_kern`: true in a hook run that a HID-BPF
  kfunc started, whichever hook it is.
- With `from_bpf` true, `hid_bpf_hw_request()`,
  `hid_bpf_hw_output_report()`, `hid_bpf_input_report()` and
  `hid_bpf_try_input_report()` return `-EDEADLOCK` on that context.
- `KF_SLEEPABLE` kfuncs (see `hid_bpf_kfunc_ids` in
  `drivers/hid/bpf/hid_bpf_dispatch.c`): the verifier refuses them in a
  `hid_device_event` program, since that program cannot be sleepable.
- `hid_bpf_try_input_report()`: the only injecting kfunc without
  `KF_SLEEPABLE`, so the one a `hid_device_event` program can call directly.
- `hid_bpf_input_report()` from `hid_device_event`: reached through a
  `bpf_wq` callback with its own `hid_bpf_allocate_context()`; see
  `tools/testing/selftests/hid/progs/hid.c`.
- `hid_bpf_try_input_report()` inside `hid_device_event`: the nested dispatch
  zeroes and refills `hdev->bpf.device_data`, the buffer the program got
  from `hid_bpf_get_data()`, so the program must pass a copy and must not
  rely on the old contents afterwards.
