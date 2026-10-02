# What the bluetooth measurement found

Three models were asked the 36 questions in `bluetooth-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels up to 6.19), reader A close behind it (up to 6.17), and reader
B older (6.10 to 6.12) with whole mechanisms out of date. The hand-written
guide was never checked against current sources, so differences between it and
the built guide are expected and are noted near the end.

Readers A and C know the architecture well: the file map, the entry points,
the two ordered work queues, the table of controller locks, who frees an skb a
driver refuses, what the synchronous send functions return, and the helpers for
pending management commands. What all three get wrong is the advertising state
the hand-written guide is about, the newest locking on a connection's protocol
pointers, a helper two of them invented, and the details of teardown orders.

## What all three readers got wrong

- **`HCI_LE_ADV_0` was unknown to every reader.** Asked how to tell whether
  instance zero is enabled, reader A said only `HCI_LE_ADV` is available,
  reader C said instance zero has no state of its own and is "`HCI_LE_ADV` with
  `cur_adv_instance` 0", and reader B recommended exactly that test. The flag
  exists, `hci_cc_le_set_ext_adv_enable()` sets and clears it for handle 0x00
  when no `adv_info` matches, and `hci_disable_ext_adv_legacy_instance_sync()`
  tests it.
- **Pause and resume.** `hci_resume_advertising_sync()` re-enables instance zero
  only on an extended-advertising controller and only through
  `hci_dev_test_and_clear_flag(hdev, HCI_LE_ADV_0)`. The pause disables every
  set in one command, which clears each `adv->enabled` but leaves
  `HCI_LE_ADV_0` set, so after a pause the flag means "re-enable on resume",
  not "on in the controller". Every listed instance is re-enabled, not only
  those that were on. An instance that fails to resume is sent a remove
  command, and only `hci_cc_le_remove_adv_set()` drops its entry. The readers
  had instance zero resumed from `HCI_ADVERTISING` (A), from
  `cur_adv_instance` (C) or "if it was on" (B).
- **Instance is not handle.** `hci_add_adv_instance()` accepts a new instance
  from 1 to `le_num_of_adv_sets` + 1 while `adv_instance_cnt` is below
  `le_num_of_adv_sets`, returns `-EOVERFLOW` otherwise, and gives instance 1 on
  a one-set controller handle 0x00. Readers A and B said the handle always
  equals the instance; reader C knew `adv->handle` but said every command in
  `hci_sync.c` sends it, and several still send the instance number.
- **`conn->proto_lock`.** `l2cap_data` is annotated `__guarded_by()` with both
  `proto_lock` and `hdev->lock`, `iso_data` with `proto_lock` alone, and
  `sco_data` with nothing. All three said the device lock covers these
  pointers.
- **hci_cmd_sync_dequeue_once()** was offered by readers A and C and does not
  exist. A queued create-connection entry is cancelled by
  `hci_acl_cancel_create_conn_sync()` and `hci_le_cancel_create_conn_sync()`,
  which call `_hci_cmd_sync_cancel_entry()` under `cmd_sync_work_lock`.
- **The once variants return `-EEXIST`** when a matching entry is queued
  (readers A and B had them return 0), and a NULL argument to the lookup
  matches anything. `hci_cmd_sync_run()` on the queue's own work item calls the
  function and then destroy itself and returns 0, not the function's result;
  reader A said destroy is not called there.
- **Aborting a connection.** A create command that is still queued is only
  dequeued and `hci_abort_conn()` returns 0; BIS and PA links get no terminate
  command; after any state's command the connection is deleted if it is still
  in the hash. Each reader had a different part of this wrong.
- **Queued functions and the pending command.** Which functions copy the
  parameters under `mgmt_pending_lock` after `__mgmt_pending_listed()`, and
  that `set_le_sync()` still dereferences `cmd->sk` after unlocking. Reader B
  had the check done with `mgmt_pending_valid()` under the device lock, which
  would unlink the command.
- **SCO and ISO sockets.** `sco_chan_del()` and `iso_chan_del()` clear the
  socket's `conn` and `conn->sk`; only `iso_conn_del()` clears `conn->hcon`;
  ISO code that drops `lock_sock()` to take the device lock checks both
  pointers again afterwards. No reader had this right.
- **Teardown in `hci_unregister_dev()`** uses `disable_work_sync()` and
  `disable_delayed_work_sync()`, not the cancel forms, skips
  `mgmt_index_removed()` when `HCI_INIT` is set as well as setup and config,
  and `bt_host_release()` calls `hci_release_dev()` only when `HCI_UNREGISTER`
  is set.
- Smaller: `mgmt_untrusted_commands[]` and `mgmt_untrusted_events[]` must be
  kept in step with the trusted lists; the SMP self tests are in `smp.c`;
  `hci_sock_dev_event()` on unregister only sets `sk_err` and wakes the
  socket, the controller reference goes in release or rebind.

## What only some readers got wrong

Reader B, and nobody else:

- `hci_dev_test_flag()` and its family work on `hdev->flags`. They work on
  `hdev->dev_flags`; `hdev->flags` holds `HCI_UP`, `HCI_RUNNING` and the other
  bits user space sees and is used with plain bit operations. Testing the
  wrong word compiles.
- Quirks are `hdev->quirks` set with `set_bit()`. The bitmap is
  `hdev->quirk_flags`, reached only through `hci_set_quirk()`,
  `hci_clear_quirk()` and `hci_test_quirk()`. Reader A hedged about the old
  name and reader C still put it in backticks.
- `req_lock` is a semaphore inside `hdev->lock`, `cmd_sync_work_lock` a
  spinlock, there is no unregister lock, and `hdev->lock` covers the pending
  management commands. All four are mutexes, `req_lock` is outside
  `hdev->lock`, and the pending list has `mgmt_pending_lock`.
- The core never frees an skb the driver's `send` refuses. `hci_send_frame()`
  calls `kfree_skb()` on a negative return, so a driver that frees it too
  frees it twice. This one would change a verdict.
- A completion callback ends with `mgmt_pending_remove()`,
  `mgmt_pending_valid()` only checks, `mgmt_pending_free()` frees an skb, and
  `mgmt_pending_foreach()` takes nothing off the list. `mgmt_pending_valid()`
  unlinks, so `mgmt_pending_remove()` after it deletes the list entry twice
  and frees twice. Also a verdict changer, and the hand-written guide's main
  rule.
- `hci_cmd_sync_submit()` has no state check; destroy runs with no lock held;
  cancellation always yields `-ECANCELED`. It returns `-ENODEV` after
  `HCI_UNREGISTER`, the worker holds `req_lock`, and a cancelled wait returns
  whatever the canceller stored.
- AMP_LINK and ISO_LINK as link types, a sentinel handle value, a kref inside
  `struct hci_conn` for get and put, a plain connection list, the table names
  in `hci_event.c`, `hci_mgmt_cmd()` placed in `mgmt.c`, `conn->chan_lock` in
  L2CAP, channel timers as kernel timers, the power-on work on the wrong queue.

Readers A and B: the socket lock taken before the channel lock. The order is
`hdev->lock`, `conn->lock`, `chan->lock`, socket lock.

Reader A alone: `mgmt_pending_find()` takes no lock (it takes
`mgmt_pending_lock`); `l2cap_set_timer()` puts a reference when it cancels a
pending timer (it never puts, and holds only when nothing was pending);
`-EBADFD` from `hci_hdev_from_sock()` for an unregistering controller (that is
`-EPIPE`); `__counted_by` on the event structures' arrays.

Reader C alone: `hci_conn_hash_del()` placed inside `hci_conn_cleanup()` (it
runs straight after the delayed work is disabled, before the buffer counts are
restored); `hci_conn_drop()` as the usual release when queueing fails (callers
use `hci_conn_put()` or `kfree()`); an unexpected continuation fragment
resetting reassembly (it is only dropped).

## What the readers already knew

The file map and entry points (no reader needed more than a missing file); the
work queues and what is serialised on each, the controller locks, frame
ownership, the return values of the synchronous sends and the rule about the
device lock around them (readers A and C); the table of pending command
helpers (reader C without a correction, reader A with one); the two connection
counters (reader C); how events are dispatched and parsed (readers A and C).
These are dropped from the build set or shrunk to a pointer, except the pending
command helpers, which the usage rules rest on.

## Where the hand-written guide is stale

It is a short guide and most of it still matches the code. What does not:

- It says `HCI_LE_ADV_0` is "the only correct way to query instance 0x00's
  enabled state" and that the flag is cleared "in the corresponding disable
  path". It is cleared only when a one-set disable names handle 0x00. The
  disable of all sets that a pause sends leaves it set, and
  `hci_resume_advertising_sync()` relies on that. Only the extended
  advertising handler maintains the flag; `hci_cc_le_set_adv_enable()` never
  touches it.
- It says that on `-ECANCELED` the callback "does NOT own the memory and must
  not free it". That holds for a command that `mgmt_pending_add()` put on the
  pending list. Twenty-one call sites use `mgmt_pending_new()`, which lists
  nothing; their callbacks (`mgmt_class_complete()`,
  `add_advertising_complete()`, `disconnect_complete()`) are the only owner
  and call `mgmt_pending_free()` on every path, cancellation included. The
  rule was missing that precondition.
- It says nothing of the queued function, where the hazard is the same:
  correct ones test `__mgmt_pending_listed()` under `mgmt_pending_lock` and
  copy what they need before unlocking.
- Its list of three management structures with a flexible array reads as
  complete. `include/net/bluetooth/mgmt.h` has more than a dozen command
  structures that end in one.
- `hci_add_adv_instance()` rejects more than `instance < 1`, and an entry's
  handle can differ from its instance number.

Its description of `mgmt_pending_valid()`, `mgmt_pending_remove()` and
`DEFINE_FLEX()` with `min(__struct_size(cp), len)` is correct and is kept as
questions.

## Left out of the build set

The hand-written guide is 672 words, so the build set holds 13 of the 36
questions. Every question had at least reader B wrong, so they were chosen by
importance to someone reviewing a patch under `net/bluetooth/`, weighted
towards what the old guide was about: advertising state, pending management
commands and flexible arrays, with the command queue added because its
callbacks are where the pending commands and the connections get freed. Left
out although a reader got them wrong: the controller locks and work queues,
frame ownership and the socket channels (readers A and C have them; reader B's
double free of a refused skb is the one loss); connection reference counts,
link types and aborting a connection; `proto_lock` on the protocol pointers
(new to all three, but confined to a few functions that carry the
annotation); registration and teardown of the controller; event dispatch,
parsing and lookup; the management command table and counted arrays from user
space; all of L2CAP and the SCO and ISO sockets, which need a guide of their
own; the device lock around synchronous functions, which the header comment
states; and the documentation, tests and change checklist.

## A question changed after the first build

`bt.adv-pause-resume` first ended "what happens to an instance that fails to
resume?", and the readers were measured on that wording. One builder answered
from the body of `hci_remove_ext_adv_instance_sync()` alone and wrote that the
`struct adv_info` stays; the other followed the command to
`hci_cc_le_remove_adv_set()`, which removes the entry when the command
succeeds, and the tree agrees with it. The question now asks for the fate of
the instance in the controller and in `hdev->adv_instances`, and says to follow
a command through to the handler of its reply.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 69 corrections, 24% rewritten on average
reader B: 101 corrections, 70% rewritten on average
reader C: 70 corrections, 22% rewritten on average

question                            reader A      reader B      reader C
bt.core-files                        8% ( 2)       7% ( 2)       6% ( 3)
bt.entry-points                      4% ( 1)      15% ( 2)      34% ( 3)
bt.docs-tests                       33% ( 1)      70% ( 1)      52% ( 3)
bt.hdev-lifecycle                   17% ( 3)      79% ( 6)      32% ( 4)
bt.hdev-flag-sets                   18% ( 1)      90% ( 3)       5% ( 2)
bt.hdev-locks                        3% ( 1)      57% ( 6)       6% ( 1)
bt.workqueues                        4% ( 1)      80% ( 2)       1% ( 1)
bt.driver-frames                    15% ( 1)      76% ( 2)       8% ( 2)
bt.cmd-sync-api                      8% ( 2)      45% ( 7)      20% ( 3)
bt.cmd-sync-destroy                 12% ( 1)      89% ( 4)      20% ( 3)
bt.cmd-sync-return                   7% ( 1)      63% ( 3)       7% ( 1)
bt.cmd-sync-lock-usage              13% ( 1)      83% ( 3)       0% ( 0)
bt.cmd-sync-data-usage              16% ( 1)      78% ( 3)      34% ( 1)
bt.event-dispatch                   28% ( 1)      63% ( 3)       7% ( 1)
bt.event-parse-usage                 4% ( 1)      84% ( 1)      22% ( 1)
bt.event-conn-lookup                25% ( 1)      74% ( 2)      43% ( 1)
bt.conn-refs                        22% ( 4)      89% ( 4)      11% ( 1)
bt.conn-lifecycle                   14% ( 1)      79% ( 2)      10% ( 2)
bt.conn-types                       27% ( 1)      84% ( 1)      16% ( 1)
bt.conn-abort                       46% ( 5)      72% ( 1)      32% ( 2)
bt.conn-proto-data                  35% ( 3)      85% ( 1)      36% ( 2)
bt.adv-instances                    40% ( 3)      77% ( 3)      14% ( 1)
bt.adv-state-usage                  49% ( 3)      71% ( 2)      49% ( 3)
bt.adv-pause-resume                 68% ( 4)      82% ( 3)      55% ( 2)
bt.mgmt-handler-table               25% ( 2)      80% ( 5)      26% ( 3)
bt.mgmt-varlen-usage                26% ( 2)      64% ( 1)      22% ( 3)
bt.mgmt-pending-api                  4% ( 1)      32% ( 5)       0% ( 0)
bt.mgmt-pending-complete-usage      19% ( 1)      91% ( 1)      29% ( 2)
bt.mgmt-pending-sync-usage          46% ( 1)      85% ( 2)      46% ( 2)
bt.mgmt-flex-usage                  26% ( 1)      85% ( 2)      33% ( 1)
bt.l2cap-locks                      24% ( 3)      67% ( 4)      14% ( 4)
bt.l2cap-chan-refs                  28% ( 2)      67% ( 3)      14% ( 1)
bt.l2cap-rx-usage                   23% ( 3)      84% ( 2)       7% ( 1)
bt.sock-conn-link                   60% ( 3)      85% ( 3)      48% ( 3)
bt.hci-sock-channels                41% ( 3)      69% ( 2)      15% ( 2)
bt.change-checklist                 49% ( 3)      37% ( 4)      38% ( 4)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `bt.conn-proto-data`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `bt.hdev-lifecycle`, `bt.hdev-locks`, `bt.driver-frames`, `bt.cmd-sync-return`, `bt.cmd-sync-lock-usage`, `bt.event-dispatch`, `bt.event-parse-usage`, `bt.event-conn-lookup`, `bt.conn-refs`, `bt.conn-abort`, `bt.mgmt-handler-table`, `bt.mgmt-varlen-usage`, `bt.l2cap-locks`, `bt.l2cap-chan-refs`, `bt.l2cap-rx-usage`.

## Questions reorganised

By subject now, 31 questions as before, each a hazard, a contract or orientation. Subjects: the
controller object; the command queue; connection objects; event handling; management commands;
advertising; L2CAP. The seven questions that had no section are in the subject they belong to, and
pending management commands sit with the command table. Nothing merged or dropped: every question
had a reader badly wrong. Reworded to stop asking how a function works inside or for a list:
`bt.hdev-lifecycle`, `bt.conn-lifecycle`, `bt.conn-abort`, `bt.event-dispatch`,
`bt.mgmt-handler-table`, `bt.hdev-flag-sets`, and `bt.mgmt-flex-usage` (two structures and how to
find the rest).
