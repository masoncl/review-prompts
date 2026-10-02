From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **The LPI Pending table is not shared.** The specification says of it:
    "This table is specific to a particular Redistributor." Extending a sharing
    argument from the configuration table to the pending table is a category
    error, and a patch that pins or shares the pending table across a group is
    doing something the architecture does not ask for.

*   **Divergent `GICR_PROPBASER` values within a group are UNPREDICTABLE.**
    "Setting different values in different copies of GICR_PROPBASER on
    Redistributors that are required to use a common LPI Configuration table
    when GICR_CTLR.EnableLPIs == 1 leads to UNPREDICTABLE behavior." A
    secondary sentence constrains it only partially: "If GICR_PROPBASER is
    programmed to different values on different Redistributors, it is
    IMPLEMENTATION DEFINED which copy or copies of GICR_PROPBASER are used when
    the GIC reads the LPI Configuration tables. However, the copy or copies
    that are used will correspond to a Redistributor on which
    GICR_CTLR.EnableLPIs == 1." Read that as a floor on how bad it can get, not
    as a licence: the only guarantee is that the chosen copy belongs to an
    enabled redistributor.

*   **There is no "it will be noticed eventually".** The specification states
    both that "A cached LPI Configuration table entry is not guaranteed to
    remain in the cache" and that "A cached LPI Configuration table entry is not
    guaranteed to remain incoherent with memory". Neither direction can be
    relied on, which is exactly why the explicit invalidation is the only way to
    publish a change.
