From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **Wait for `GICR_VPENDBASER.Dirty` to clear before descheduling.** The
    redistributor sets Dirty while it is parsing the virtual pending table
    after a schedule, and the code path between making a vPE resident and
    entering the guest is preemptible, so a deschedule can arrive mid-scan. On
    GICv4.1 the architecture is explicit in both directions: with `Valid == 0`,
    "Writing 1 to GICR_VPENDBASER.Valid is UNPREDICTABLE while
    GICR_VPENDBASER.Dirty == 1"; with `Valid == 1`, "Writing 0 to
    GICR_VPENDBASER.Valid is UNPREDICTABLE while GICR_VPENDBASER.Dirty == 1".
    Do not quote that pairing at a GICv4.0 implementation: `GICR_VPENDBASER`
    has two full field-description variants, and in the GICv4.0 one the
    `Valid == 1` sub-case reads "Writing **1**", additionally gated on
    `GICR_TYPER.Dirty == 1`. The rule in the next bullet is the
    variant-independent one and is the safer thing to cite.
    `its_clear_vpend_valid()` opens by
    waiting for Dirty to clear, under the comment "Make sure we wait until the
    RD is done with the initial scan", which makes it a full residency barrier
    rather than just a Valid-clearing helper.

*   **The whole-register rule is stricter than the Dirty rule alone.** "Writing
    a new value to any bit of GICR_VPENDBASER, other than
    GICR_VPENDBASER.Valid, when GICR_VPENDBASER.Valid==1 is UNPREDICTABLE." A
    patch that adjusts any other field of a live `GICR_VPENDBASER` — even one
    that looks advisory — is outside the architecture.
