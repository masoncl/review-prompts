# What is in here

Working material for converting hand-written subsystem guides into built ones.
Nothing in this directory is built into a guide. The procedure is "Converting a
guide" in `kernel/docs/subsystem-questions.md`.

- `<guide>-measurement.md`: a wide set of questions about the subject, used to
  find out what a model already knows before deciding what the guide should
  spend its words on. Run with `build-guides.py --no-sources --check-memory
  --questions <this directory> --guide <guide>-measurement`.
  `mm-vma-measurement-116.md` is the one `mm-vma` was cut from.
- `<guide>-measurement-results.md`: what the measurement found, written down
  because the runs themselves are not kept. It is the reason the build set
  holds the questions it does.
- `mm-vma.md`: a catalogue of what the hand-written `mm-vma.md` was trying to
  teach, lesson by lesson, with what was wrong or missing in it.
- `mm-vma-previous-questions.md`: an earlier question set that tried to
  recreate the hand-written guide item by item. Kept for the hazards it lists.
