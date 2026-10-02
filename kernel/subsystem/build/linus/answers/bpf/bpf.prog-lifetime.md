- `__bpf_prog_put()`: takes one argument and only decrements and dispatches;
  the deferral test is `in_hardirq() || irqs_disabled()`.
- Final put from softirq, or with preemption off and IRQs on:
  `bpf_prog_put_deferred()` runs in place, not on a workqueue.
- `bpf_prog_put_deferred()`: sends the perf and audit unload events and calls
  `bpf_prog_free_id()`; kallsyms removal is in `__bpf_prog_put_noref()`.
- Sleepable program: `__bpf_prog_put_noref()` calls `call_rcu_tasks_trace()`
  only, with no chained `call_rcu()`.
- `__bpf_prog_put_rcu()`: does not free used maps; it frees `func_info`, the
  uid and the security blob, then calls `bpf_prog_free()`.
- `bpf_prog_free()`: always schedules `bpf_prog_free_deferred()`; the used
  maps and the JIT images are never freed in the grace-period callback.
- `bpf_prog_free()`: puts `aux->dst_prog` before scheduling, so when reached
  from `__bpf_prog_put_rcu()` that put runs in the grace-period callback.
- `bpf_prog_free_deferred()`: drops used maps, used BTFs and
  `dst_trampoline`, and frees the JIT images.
- `aux->work`: used twice, first for `bpf_prog_put_deferred()` when deferred,
  then for `bpf_prog_free_deferred()`.
- Load failure: `bpf_prog_load()` passes `prog->aux->real_func_cnt` as
  `deferred`, so a program whose subprogs were JITed still waits a grace
  period.
- `bpf_link_free()` with `dealloc_deferred`: makes one wait before
  `bpf_link_dealloc()` puts the program; tested in this order:

| Link | Wait |
|---|---|
| `link->sleepable` or `link->prog->sleepable` | `call_rcu_tasks_trace()` |
| tracepoint link (`bpf_link_is_tracepoint()`) | `call_tracepoint_unregister_atomic()` |
| other | `call_rcu()` |

- `bpf_link_free()` with only `dealloc`: puts the program at once, with no
  wait of its own.
- Non-sleepable program behind a sleepable link (`bpf_link_init_sleepable()`):
  the link's Tasks Trace wait comes first, then, if that put is the last, the
  program's own `call_rcu()`.
