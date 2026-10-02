- There is no vpe_to_cpuid_nolock() here; the lock-taking helpers are
  `vpe_to_cpuid_lock()` and `irq_to_cpuid_lock()`, with their unlock twins.
- Writers: `its_vpe_set_affinity()` under `vpe_lock`, and
  `its_vpe_irq_domain_activate()` without `vpe_lock`, before its own
  `its_send_vmapp()` calls.
- `irq_to_cpuid_lock()`: takes `vpe_lock` only for `its_vpe_irq_chip` and for
  an LPI with a vLPI map; any other `struct irq_data` is read as a physical
  LPI of a `struct its_device`.
- vLPI commands sent through the ITS (`its_send_vmovi()`, `its_send_vinv()`,
  `its_send_vint()`, `its_send_vclear()`, `its_send_vmapti()`): take no
  `vpe_lock`.
- **Unsafe usage**: passing the `struct irq_data` of a GICv4.1 doorbell
  (`its_vpe_4_1_irq_chip`) or of a vSGI (`its_sgi_irq_chip`) to
  `irq_to_cpuid_lock()`; its chip data is a `struct its_vpe`, which the
  function would use as a `struct its_device`.
  - Safe: `vpe_to_cpuid_lock()` on the `struct its_vpe`, as
    `its_vpe_4_1_invall()` and `its_sgi_get_irqchip_state()` do.
- **Potentially unsafe usage**: reading `vpe->col_idx` without `vpe_lock`.
  - Unsafe: on a vLPI or vSGI path that uses the value to pick `rd_base` or a
    collection for a command; that path holds another irq's `irq_desc` lock,
    and `its_vpe_set_affinity()` can change `col_idx` before the access.
  - Safe: in a callback of the doorbell irq, which runs under the same
    `irq_desc` lock as `its_vpe_set_affinity()`, as
    `its_vpe_set_irqchip_state()` does.
  - Safe: in `valid_vpe()`, which the command builders call; the value only
    selects the collection that `valid_col()` sanity-checks and is not
    encoded in the command.
  - Safe: in `its_vpe_irq_domain_activate()` for the doorbell, which
    `__setup_irq()` reaches through `irq_activate()` with the doorbell's
    `irq_desc` lock held, the lock `its_vpe_set_affinity()` runs under.
