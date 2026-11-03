# Presentation script — "What does this sticker actually mean?"

8 minutes. **B** = Burak, **C** = Canyang. Times are cumulative targets; slides 19–22 are appendix (don't present, keep for questions).
Spoken lines are in plain text; stage directions in *italics*. Numbers in **bold** are the ones to say clearly for the grader.

---

## 1 · Cold open video — B · 0:00–0:20

*Video autoplays. Say nothing for the first 4–5 seconds. Then, while still looking at the laptop, not the room:*

B: Sorry, one sec — I think I'm… hold on, that's not… *(click around with the real cursor)* …how do I —

C: *(deadpan, from the side)* Burak. **Burak.**

B: *(click to slide 2)*

## 2 · "Just kidding." — B · 0:20–0:30

B: Just kidding. No data leakage here. But we are going to talk about stickers today.

## 3 · Our group chats run on these — B · 0:30–1:00

B: This is where the project came from. Our class group chat, and every other group chat I'm in, runs on stickers. Half of my chats are Turkish, and the Turkish stickers are *very* Turkish — politicians, actors, in-jokes from TV shows nobody here has seen. And the non-Turkish people in those chats react anyway. Laugh emoji, heart, whatever.

So the question we actually wanted answered was: do they *get* it? Or are they being polite?

## 4 · Hypotheses — C · 1:00–1:45

C: That turns into four testable questions. There's actual literature behind this: Elfenbein and Ambady's 2002 meta-analysis found an **in-group advantage** in reading emotions — people read faces from their own culture better. We're asking whether that holds for stickers, and whether context fixes it.

**H1** is the one we randomized: does seeing the sticker inside a chat help you read it? Formally, the null is that accuracy is the same alone or in chat; the alternative is that chat is higher. Two-sided paired test, alpha point-oh-five.

**H2**: do natives read their own culture's stickers better? That one we can't randomize — you're either Turkish or you're not — so it's measured.

**H4**: with no context at all, can outsiders beat chance? Chance is one in three.

And **H5** is the control that makes the whole thing honest: is it the *sticker* helping, or just the message next to it?

## 5 · Who took part — C · 1:45–2:05

C: Seventy people finished the study in three days. Sixteen Turkish natives, twenty-six Chinese, twenty-one American. Collected through one link on WhatsApp and WeChat, plus a flyer with a QR code — eleven people came in through the flyer. Thanks to the XAI students, and to the random people at Twinnie's.

## 6–7 · Live round 1 — B · 2:05–2:50

*Slide 6: sticker alone.*

B: Before the numbers, you get to be participants. Here's a sticker, on its own. The sender means one of three things: positive, negative, or sarcastic. Hands up for positive. *(count)* Negative. *(count)* Sarcastic.

*Slide 7: in chat.*

B: Now the same sticker, as a reply to "I ate your leftover pizza." Vote again. Positive… negative… sarcastic.

*Reveal.*

B: It's sarcastic. This is İbrahim Tatlıses, a Turkish singer, and this is a joke threat. In the study, non-Turkish readers got this one right **22 percent** of the time alone, and **23 percent** in chat. Context did nothing. Remember that.

## 8–9 · Live round 2 — C · 2:50–3:30

*Slide 8: sticker alone.*

C: One more, from my side. Vote: positive, negative, sarcastic.

*Slide 9: in chat.*

C: Now as a reply to "How are you holding up after staying up all night?" Vote again.

*Reveal.*

C: Also sarcastic. The text says "It's fine, I'm great," and he's lying in a puddle. Outsiders got **21 percent** alone, **35 percent** in chat. So this time, context helped — a bit.

## 10 · The experiment — C · 3:30–4:10

C: Here's the design. **Thirty-six stickers**: twelve Turkish, twelve Chinese, twelve English — six with text on the sticker, six without, balanced across positive, negative and sarcastic.

Every participant saw every sticker exactly once, in one of **three conditions**: alone, inside a chat, or — the control — the chat message with the sticker hidden. Which sticker got which condition was set by a **Latin square**: three sets, three rotations, so across the sample every sticker appeared in every condition equally often. Order shuffled, one attention check.

The answer key is **sender intent**: Burak labeled the Turkish set, I labeled the Chinese set, with what *we* mean when we send them. Then natives in the data checked us — we'll come back to that.

## 11 · Power — C · 4:10–4:40

C: How many people did we need? We planned a **paired t-test** on each person's accuracy — alpha point-oh-five, eighty percent power, and a medium effect, d-z of point-four, because nobody has run a sticker study before, so we used Cohen's convention. Statsmodels says **fifty-two** people. We also simulated the actual design — twelve binary trials per condition, with participant and sticker random effects — and the curves agreed. We got **seventy**, which means after the fact we could detect an effect as small as six points.

## 12 · Context helps — B · 4:40–5:20

B: Main result. Accuracy with the sticker alone: **64 percent**. In chat: **76 percent**. Message only, sticker hidden: **68 percent**.

Chat versus alone is **plus eleven points**, 95 percent confidence interval six-point-six to sixteen, d-z point-five-eight, p under point-oh-oh-oh-one. The differences were normal — Shapiro p of point-two-nine — and the Wilcoxon agrees. A repeated-measures ANOVA across all three conditions is significant, sphericity was fine, and the Holm-corrected post hocs say: chat beats alone, chat beats message-only, and alone versus message-only is a wash.

The one that matters for H5: chat beats message-only by **seven and a half points**. The sticker adds meaning beyond the words. It's not just people reading the message.

## 13 · Natives win, until you hide the sticker — C · 5:20–6:00

C: Now the culture question. This is a mixed logistic regression with random intercepts for participant *and* sticker, because thirty-six trials per person aren't independent.

Green is natives reading their own culture, orange is outsiders. The gap on the left is the **in-group advantage**: odds ratio **1.51**, H2 confirmed.

H3 was our prediction that context would help outsiders *more*. It didn't — both lines go up by about the same amount, the interaction isn't significant. What we found instead is on the right: hide the sticker, and the native advantage **disappears entirely**. Natives were reading the picture, not the caption.

## 14 · Outsiders are not guessing — B · 6:00–6:25

B: H4. Take only the no-text stickers, only outsiders, no context. They scored **67 percent** against a 33 percent chance rate. Exact binomial, p under point-oh-oh-oh-one, Cohen's h point-six-nine. Each dot is one person. Sentiment leaks through the image.

Except when a man points a gun at you as a joke.

## 15 · Sarcasm — C · 6:25–6:55

C: The honest slide. Before collecting, we wrote a rule: if fewer than half the natives agree with the author's label, flag the sticker. **Six of thirty-six** got flagged — and every one of them is sarcastic or negative. Two are mine, two are Burak's. We wrote down what *we* mean, and our own people disagreed, exactly on sarcasm.

We reran everything without those six. Chat still beats alone by nine-point-seven points. Nothing changes.

## 16 · Limitations — B · 6:55–7:25

B: What this can't tell you. It's a convenience sample — friends, classmates, WeChat. Native-or-not was measured, not randomized, so the context effect is causal but the culture effect is quasi-experimental. The answer key is one person's intent per culture. And our attention check was itself ambiguous — the sticker said "select positive" while the question said "what does the sender mean," and six of eight "failures" picked sarcastic, which is a fair reading. We kept them; the pre-registered exclusion gives the same answers.

## 17 · Takeaway — B · 7:25–7:40

B: One sentence: the sticker carries the meaning. Context helps everyone by about eleven points, but the picture is what natives are reading, and sarcasm is the part that doesn't travel.

Practical advice: if you want a sticker to land across cultures — no text, no sarcasm, and send it in a chat.

Now. Draw time.

## 18 · Squishy draw — both · 7:40–8:00

*Video autoplays, 12 seconds. Let the reels land.*

C: Hadley! And Anya! Come get your squishies.

*If a winner isn't present:* B: Not here? Okay — *(advance to backup, or read from the terminal)* — Bahar Alkan.

---

## If asked

- **Why paired t and not independent?** Same people in all three conditions; pairing removes between-person variance. Each person is their own control.
- **Why a mixed model on top of the ANOVA?** The ANOVA uses per-person means, which throws away the sticker-level structure. The mixed model keeps every trial and treats stickers as a random sample — and sticker variance turned out to be four times participant variance.
- **Post hoc correction?** Holm, across the three pairwise context comparisons.
- **Did you pre-register?** Informally: the plan, hypotheses and exclusion rules are in `PROJECT_BRIEF.md`, committed before collection. We deviated on the attention check and say so; both versions are in the repo.
- **Effect size for H2?** Odds ratio 1.51; on the probability scale roughly ten points at the alone condition.
- **Where's the code?** github.com/burakdon/sticker-comms. Scripts, not notebooks; raw and cleaned data committed; both of us have reviewed PRs.
- **Appendix slides 20–22**: all 36 stickers ranked; the full results table; calibration (people know when they're guessing).

## Timing fallback
Running long at slide 12? Cut slide 14 (say the 67% in one breath on slide 13) and shorten 16 to the attention-check point only. Running short? Slide 20 is a good one to show.
