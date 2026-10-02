From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **Two list registers must not hold the same virtual INTID unless both are
    Invalid.** The architecture states that "Behavior is UNPREDICTABLE if two or
    more List Registers specify the same vINTID when: • ICH_LR<n>_EL2.State ==
    0b01. • ICH_LR<n>_EL2.State == 0b10. • ICH_LR<n>_EL2.State == 0b11." Only
    the Invalid state is exempt. This is what makes multi-source software
    interrupts awkward: distinct sources are architecturally distinct interrupt
    events but must not occupy several list registers at once, so the emulation
    injects one per entry and arranges a maintenance interrupt to deliver the
    rest.

*   **The physical INTID rule is a different rule.** In the separate list of
    programming errors that result in UNPREDICTABLE behaviour, the architecture
    names "Having two or more interrupts with the same pINTID in the List
    registers for a single virtual CPU interface." Two list registers may carry
    the same *physical* INTID in some other arrangement no more than they may
    carry the same virtual one, but the two statements are in different
    sections, constrain different fields, and cannot be cited for each other.
    If a patch or review comment cites one section for the other's claim, the
    citation is wrong even if the conclusion happens to hold.

*   **Special INTIDs and the LPI range have their own constraints.** A virtual
    INTID in 1020-1023 in a list register whose state is not Inactive is
    UNPREDICTABLE, and specifying a virtual INTID in the LPI range while
    `ICC_SRE_EL1.SRE == 0` is UNPREDICTABLE.
