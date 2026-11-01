# Expanded evaluation findings

## Why I expanded the tests

I wanted more realistic fictional paperwork rather than relying on a short scheduling paragraph. I added longer multipart fixtures and separate supported, exception-bearing, and scanned inputs. I also authored a 12-case manifest with four alternating-week scenarios, four explicit 14-day patterns, and four incomplete/conflicting/unsupported scenarios. Six are development cases and six are held-out cases.

## What the longer documents exposed

My first local-model run on the five-page supported packet returned alternating single days instead of seven-day blocks. The anchor and exchange metadata were correct, and the quotation existed on the claimed page. Schema validation and quotation membership therefore failed to detect the wrong ownership pattern. The first seven-page exception run also omitted warnings despite an explicit holiday override.

The baseline got the anchor and cycle right on the supported packet but omitted explicit exchange metadata. It correctly abstained on the exception-bearing packet. The scanned fixture was correctly rejected before model inference.

## Changes and rerun

I added deterministic checks for contradictions against recognizable source rotations and rejected empty warnings when exception language is present. I also added narrowly supported exchange weekday/time extraction to the baseline. I clarified consecutive-block instructions in the model prompt, then froze that prompt before starting the held-out run.

In the development-fixture rerun, baseline and model both matched all four supported fields. The local model took 28.02 seconds. On the exception-bearing packet, the model returned warnings and was correctly blocked from approval; that run took 40.98 seconds. I retain the earlier failed results rather than replacing them with only the successful rerun.

## Desktop integration check

I exercised the real model worker and Qt signal path using the longer supported fictional fixture. The check verified the known anchor/cycle, required approval, and generated 30 calendar rows. A timer recorded 314 event-loop ticks while the request ran. This was an automated offscreen check, not a manual demonstration of native file dialogs.

The first attempt found an incorrect widget-font call on the non-widget worker. I moved it to the main window and added a regression check. The expanded automated suite passes 18 checks.

## Evaluation boundaries

The synthetic cases use controlled phrasing and a small number of patterns. The held-out cases have not been used to tune the frozen prompt, but they share the application's defined grammar and are not a representative legal-document benchmark. Rejection protects the workflow but does not prove that the model understood why a case was unsupported. Current deterministic checks cover selected wording and can overflag ordinary exception-related words; they are not a general legal-clause interpreter.

## Frozen-prompt held-out results

| Measure | Baseline | Local model with validation |
|---|---|---|
| Exact supported plans | 2 of 4 | 3 of 4 |
| Unsupported cases blocked | 2 of 2 | 1 of 2 |
| Non-null supported fields correct | 4 of 8 | 6 of 8 |
| Field precision on returned supported predictions | 100% | 100% |
| Field recall across supported expected values | 50% | 75% |

I interpret precision cautiously: rejected responses produce no accepted predictions, so this figure does not mean that the raw model made no mistakes. The model proposed the wrong weekly ownership in one case and was rejected. It also omitted holiday warnings and was blocked by a deterministic check. The narrow baseline abstained on both explicit 14-day patterns, while the model matched them.

The most important failure was an incomplete plan: the model invented remaining ownership without warnings and the then-current guard accepted it. This result prevents a claim of reliable unsupported-document handling.

## Post-evaluation correction

After recording those results, I expanded the warning guard to include explicit phrases such as “not specified,” “not provided,” and “no start date,” and added a regression check for invented ownership following an incomplete source statement. This correction was informed by a held-out failure. I have not rewritten the original metrics as if the correction had existed beforehand; those six cases are now observed examples and cannot serve as an untouched test set for further tuning.

Broader natural-language coverage, field-level evidence, unsupported-case explanations, a fresh untouched evaluation set, and a manual UI walkthrough remain important follow-up work.
