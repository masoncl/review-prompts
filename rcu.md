# RCU
- rcu_read_lock()
    - Disables preemption and migration when CONFIG_PREEMPT_RCU is off
- stands for read, copy, update
- rcu_read_lock() starts a critical section on a CPU
- rcu_read_unlock() ends a critical section on a CPU
- RCU grace periods trace when all the CPUs have left their critical sections
- Memory is never freed until after CPUs have left their critical sections

The general pattern is:

rcu_read_lock()
<access memory protected by rcu>
rcu_read_unlock()

As long as the memory protected by RCU is freed via the call_rcu callbacks,
it will never be freed while a CPU is inside the critical section.
