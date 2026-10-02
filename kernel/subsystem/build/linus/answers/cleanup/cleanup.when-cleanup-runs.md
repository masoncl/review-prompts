- `goto` forward past the declaration to a label inside the variable's scope:
  where the compiler accepts the jump, the cleanup function still runs at
  scope exit, on a variable that was never initialised; Clang rejects the jump
  (see "Goto and cleanup in one function").
