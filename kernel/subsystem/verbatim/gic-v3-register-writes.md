From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **The specification's negative is stronger for the Distributor than for the
    Redistributor, and a review should not over-claim.** `GICD_CTLR.RWP`'s
    description ends with an explicit exclusion clause: "Updates to other
    register fields are not tracked by this field." `GICR_CTLR.RWP`'s
    description has no equivalent sentence — it gives only the enumeration of
    what it does track. So on the redistributor side the correct argument is
    that the enumeration is exhaustive and does not include the active or
    pending registers, not that the specification states an exclusion. If a
    patch or a review comment claims a quoted exclusion clause for
    `GICR_CTLR.RWP`, it is quoting something that is not there.

*   **The Redistributor RWP list has a GICv4.1-only member.** Alongside
    `GICR_ICENABLER0`, the `GICR_CTLR` DPG fields and the `EnableLPIs` 1-to-0
    transition, it covers "In FEAT_GICv4p1, GICR_VPROPBASER, which clears Valid
    from 1 to 0". A GICv4.1 path that clears `GICR_VPROPBASER.Valid` and
    proceeds without the RWP poll is missing a completion the architecture
    provides.

*   **The software-generated interrupt ID field is four bits.** The
    architecture defines "INTID, bits [27:24] — The INTID of the SGI", and the
    driver's mask is correspondingly `0xf` shifted to bit 24. A wider mask, or a
    signed one, lets an out-of-range value through — which matters most in the
    KVM emulation of the register, where the value is guest-supplied.
