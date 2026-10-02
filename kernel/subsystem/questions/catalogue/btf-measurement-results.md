# What the btf measurement found

Two models were asked the questions in `btf-measurement.md` with no sources, and a checker
that had the sources then corrected each answer against a mainline tree (kernel
7.3.0-rc4). The readers are labelled A (the more current) and B (a few releases
older); which models they were does not matter here. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted at the end.

## The central fact both readers got wrong

Updating or deleting a map element does **not** free its special fields. The
array and hash update and delete paths call `bpf_obj_cancel_fields()` or
`check_and_cancel_fields()`, which only cancel timers, work items and task
work. Kernel pointers and list or tree heads stay in the element, which may be
recycled at once, until the allocator's destructor (`htab_mem_dtor()`) or the
map's own free runs `bpf_obj_free_fields()`. Both readers described an eager
free through a check_and_free_fields() that is not in the tree, and reader A
said it did not know `bpf_obj_cancel_fields()` at all.

## Other things both got wrong

- `check_and_init_map_value()` is for buffers being handed out or swapped in,
  not for recycled elements: the hash and array update paths never call it.
  The cgroup storage update does, on the new buffer it installs.
- `copy_map_value_long()` copies in long-sized chunks only when the map has no
  record.
- Timer and work teardown uses `hrtimer_try_to_cancel()` and `cancel_work()`,
  deferred through irq_work when called in hard interrupt context or with
  interrupts off. Neither waits, and there is no bpf_timer_delete_work().
- The newer kinds: `BPF_TASK_WORK`, `BPF_RES_SPIN_LOCK`, `BPF_UPTR`, and the
  `BPF_MAP_TYPE_RHASH` map type in the allowlist. `BPF_GRAPH_ROOT`,
  `BPF_GRAPH_NODE` and `BPF_KPTR` are masks, not kinds.
- An armed timer holds a reference on the program, not on the map.

## What reader B got wrong as well

No locking update flag, no locked copy and no resilient lock (all three exist);
every direct access to a special field is rejected (an aligned 8-byte load of a
kernel pointer or user pointer field is allowed); per-CPU kernel pointer
fields have one slot per CPU (it is one pointer to a per-CPU object); the
destructor runs when a kernel pointer is exchanged (the exchange just returns
the old pointer).

## Where the hand-written guide is stale

`btf.md` is mostly a checklist of what to trace, and its allowlist table is
close to the code. Its "Update" section tells the reviewer to trace ownership
without saying what the code does, which is the fact above. It was never
onboarded to the drift checker.

## What was left out of the build set, and why

Ten of the nineteen questions were kept, with the same text as in the
measurement set, and their budgets add up to 515 words. The guide is sized to
600 words, the floor for a built guide whose hand-written original is shorter,
and no question is given fewer than 40: a first build of nine questions and 305
words, with 25 to 45 words a question, came out as fragments that meant nothing
without the question beside them. Those nine are the kinds and the map type
allowlist, which both readers had out of date, and the copy, initialise, free,
cancel, update, delete and copy-out questions that between them carry the
central fact above. With the room the larger size gave, `btf.timer-lifecycle`
came back: both readers had an armed timer holding the map and a teardown that
waits, and it drew seven corrections for reader A, more than any question but
`btf.new-field-kind`. Six questions had a clause reworded in both files after
the measurement. `btf.field-types` and `btf.map-type-support` ask for constant
names in full, and the first no longer presupposes that every kind holds a
resource; `btf.check-and-init` no longer presupposes that an update path must
call the function, and asks on what memory calling it is unsafe;
`btf.free-fields` says that the contexts it asks about include NMI and
interrupts off, after a build answered without either; `btf.cancel-fields` says
what to do on a tree without the function; and `btf.timer-lifecycle` asks
whether cancelling waits for a running callback, which is what both readers had
wrong. Otherwise they ask what they asked.

- `btf.nmi-context`. Both readers were wrong here too, but three answers that
  were kept carry its facts: which actions are safe in NMI, and that the timer
  and work item teardown is deferred through irq_work, is in `btf.free-fields`;
  that a delete from a program frees nothing is in `btf.delete-and-reuse`; and
  that the teardown does not wait is in `btf.timer-lifecycle`. It is the next
  to come back if the guide is allowed more words.
- `btf.new-field-kind`. The most corrections of any question for both readers,
  and the only one about changing the implementation, but its answer is a list
  of places that needs 80 words, and a patch that adds a kind is rarer than one
  that touches a map's update or free path.
- `btf.kptr-semantics`, `btf.spin-lock-field`, `btf.verifier-access`,
  `btf.graph-ownership`, `btf.uptr`. What reader B had wrong here is listed
  above; reader A had between 5% and 54% rewritten and at most two corrections
  on each. They are about what a program may do with one kind of field, which
  the verifier enforces, where the guide is about what map code must do with
  all of them; what freeing does for each kind is in `btf.free-fields`.
- `btf.record`, `btf.core-files`. Reader A had 2% and 25% rewritten, and each
  answer that was kept names the function and the file to read.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 46 corrections, 41% rewritten on average
reader B: 45 corrections, 79% rewritten on average

question              reader A        reader B
btf.field-types         6% ( 2)        36% ( 3)
btf.record              2% ( 1)        77% ( 3)
btf.map-type-support   31% ( 3)        86% ( 1)
btf.verifier-access    54% ( 1)        90% ( 1)
btf.core-files         25% ( 3)        62% ( 1)
btf.copy-helpers       62% ( 4)        71% ( 2)
btf.check-and-init     67% ( 1)        89% ( 1)
btf.free-fields        35% ( 1)        87% ( 2)
btf.cancel-fields      85% ( 2)        90% ( 2)
btf.lookup-usage        0% ( 2)        76% ( 3)
btf.update-ownership   70% ( 3)        77% ( 2)
btf.delete-and-reuse   82% ( 2)        77% ( 2)
btf.nmi-context        87% ( 1)        80% ( 2)
btf.timer-lifecycle    63% ( 7)        86% ( 3)
btf.kptr-semantics     39% ( 2)        90% ( 3)
btf.graph-ownership     5% ( 1)        84% ( 1)
btf.spin-lock-field    18% ( 1)        89% ( 1)
btf.uptr                9% ( 0)        88% ( 2)
btf.new-field-kind     53% ( 9)        79% (10)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `btf.nmi-context`, `btf.kptr-semantics`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `btf.record`.

## Questions reorganised

Three subjects: field kinds and the record (kinds, the record, the map type allowlist, kernel
pointers); copying and initialising values; freeing and cancelling fields, which now holds the
central fact above in one builder call. 15 questions became 13. Merged: `btf.free-fields` and
`btf.nmi-context` into `btf.free-contexts`; `btf.update-ownership` and `btf.delete-and-reuse` into
`btf.update-delete-ownership`. Nothing was dropped. `btf.map-type-support` no longer asks for the
allowlist as a table, which opening `map_check_btf()` shows, but for what an unlisted kind or map
type gets and what a map type must already do before it is added to the list.
