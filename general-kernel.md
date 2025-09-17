- preemption in the kernel means having the CPU taken away, potentally allowing
other tasks to run on the current CPU.
- disabling preemption means you will continue to run on the current CPU, but
may be interrupted by irqs.  per-cpu variable usage while preemption is disabled
can assume the CPU number has not changed
- migration means to be moved to a different CPU
- disabling migration means you will stay on the current CPU, but you may still
be preempted by other tasks.  You'll return to the current CPU when scheduled again.
per-cpu variable usage while migration is disabled can assume the CPU number has
not changed.
- typeof() can be used in access struct field offsets before a variable
is fully initialized.  It can be combined with container_of() or offset_of() without creating circular
references.  struct foo *ptr = contaoner_of(x, typeof(*ptr), y)) is safe.
- kernel self tests using pthreads are not kernel code. They are applciations,
and memory allocated inside a pthread is private to that pthread.
- kernel self tests may leak memory or file descriptors.  It's not a regression
unless it unintentionally crashes the system
