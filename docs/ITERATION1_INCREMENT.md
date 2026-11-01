# Iteration 1 comparison results increment

## My goal

I wanted a clear way to inspect the difference between expected rules, baseline output, and local-model output instead of reading raw JSON files. This is a distinct interface improvement beyond the Assignment 2 R&D checkpoint.

## Before and after

At R&D code checkpoint `75fa9d8`, the app provided document review, approval, calendar, records, and export. Research comparisons existed only in saved evaluator files and written notes.

The app now has a fourth tab, Research comparison. I can open an evaluator's `results.json` and inspect the fixture/case, method, field, answer-key value, recorded output, match status, error, and elapsed time. The view supports both formal-document and dataset result formats.

## How the feature handles evidence

- Opening results does not run inference or alter the currently reviewed schedule.
- Historical evidence is clearly labeled. A previous success is not presented as a fresh extraction.
- Missing output is distinguished from an explicit null field.
- Mismatched fields and missed warnings are visible in text as well as color.
- Network/validation errors remain errors or abstentions; they are not presented as successful semantic understanding.
- A malformed replacement clears the previous comparison so stale rows do not look current.
- Unknown answer keys are labeled unavailable instead of guessed.

## Verification

The complete working-app suite now passes 23 checks: the previous 19 R&D checks plus four checks covering comparison interpretation and GUI behavior. A real-widget render loaded retained fictional formal-document results and displayed mismatches and the missed-warning case. This preview did not run a new model request or modify approval.

## Scope and remaining milestone work

The feature is implemented locally. GitHub receives the source through the separately scheduled imports. Trello connection and online board setup remain pending; instructor invitations require confirmation. Video recording is deferred for today. This increment does not mean the entire Iteration 1 assignment has been submitted or completed.
