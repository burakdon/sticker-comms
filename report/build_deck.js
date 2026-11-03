/* Build the presentation deck (report/sticker-comms-deck.pptx) from the analysis outputs.
 *
 * Creative slides (cold open, "just kidding", motivation screenshots, closer) are left as
 * clearly marked placeholders; every results slide carries the real figure and numbers.
 *
 * Usage (needs pptxgenjs on NODE_PATH):
 *   node report/build_deck.js
 */
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "outputs", "figures", "slides");
const OUTFILE = path.join(ROOT, "report", "sticker-comms-deck.pptx");
const img = (name) => path.join(FIG, name);
const stk = (id) => path.join(FIG, `stk_${id}.png`);

// ---------------------------------------------------------------- theme
const THEME = {
  name: "Sticker Comms",
  headFontFace: "Avenir Next",
  bodyFontFace: "Avenir Next",
  colors: {
    dk1: "3A4048", lt1: "FBFBF9", dk2: "5C6670", lt2: "ECEDEA",
    accent1: "128C7E", accent2: "25D366", accent3: "EB6834", accent4: "2A78D6", accent5: "6250D6", accent6: "9AA0A8",
    hlink: "128C7E", folHlink: "6250D6",
  },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Burak Dönbekci & Canyang Xu";
pres.title = "What does this sticker actually mean?";
const C = pres.SchemeColor;
const W = 13.33, H = 7.5;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: THEME.colors.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 1.0, fontSize: 34, bold: true, color: C.text1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "Sticker Comms · AIPI 510 · Project 2", options: { x: 0.6, y: 7.05, w: 6, h: 0.3, fontSize: 9, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.05, w: 0.5, h: 0.3, fontSize: 9, color: THEME.colors.accent6 },
});
pres.defineSlideMaster({ title: "BLANK", background: { color: THEME.colors.lt1 }, objects: [] });
pres.defineSlideMaster({ title: "DARK", background: { color: THEME.colors.dk1 }, objects: [] });

// ---------------------------------------------------------------- helpers
function bubble(slide, text, o) {
  // Chat-bubble motif: rounded callout with a small tail. `tone`: white | green | muted
  const tone = o.tone || "white";
  const fill = tone === "green" ? THEME.colors.accent1 : tone === "muted" ? THEME.colors.lt2 : "FFFFFF";
  const color = tone === "green" ? "FFFFFF" : THEME.colors.dk1;
  slide.addShape(pres.ShapeType.wedgeRoundRectCallout, {
    x: o.x, y: o.y, w: o.w, h: o.h, fill: { color: fill }, line: { color: tone === "white" ? THEME.colors.lt2 : fill, width: 1 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 }, objectName: o.name || "bubble",
  });
  slide.addText(text, {
    x: o.x + 0.18, y: o.y + 0.08, w: o.w - 0.36, h: o.h - 0.16, fontSize: o.fontSize || 14, color, valign: o.valign || "middle",
    align: o.align || "left", isTextBox: true, margin: 0, bold: !!o.bold, paraSpaceAfter: 4, objectName: (o.name || "bubble") + " text",
  });
}
function stat(slide, big, small, o) {
  slide.addText(big, { x: o.x, y: o.y, w: o.w, h: o.h * 0.62, fontSize: o.size || 44, bold: true, color: o.color || THEME.colors.accent1, align: o.align || "left", valign: "bottom", isTextBox: true, margin: 0, objectName: "stat " + big });
  slide.addText(small, { x: o.x, y: o.y + o.h * 0.62, w: o.w, h: o.h * 0.38, fontSize: o.smallSize || 12, color: THEME.colors.dk2, align: o.align || "left", valign: "top", isTextBox: true, margin: 0, objectName: "stat label" });
}
function placeholderBox(slide, text, o) {
  slide.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.15, fill: { color: o.dark ? "4A515A" : "FFFFFF", transparency: o.dark ? 0 : 40 }, line: { color: o.dark ? "9AA0A8" : THEME.colors.accent3, width: 1.5, dashType: "dash" }, objectName: "placeholder" });
  slide.addText(text, { x: o.x + 0.3, y: o.y + 0.2, w: o.w - 0.6, h: o.h - 0.4, fontSize: o.fontSize || 14, color: o.dark ? "E7E8E4" : THEME.colors.accent3, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "placeholder text" });
}
function caption(slide, text, y = 6.55) {
  slide.addText(text, { x: 0.6, y, w: 12.1, h: 0.45, fontSize: 11, color: THEME.colors.dk2, isTextBox: true, margin: 0, valign: "top", objectName: "caption" });
}
function chatMock(slide, o) {
  // A WhatsApp-style thread: friend's message on the left, sticker (or hidden box) on the right.
  slide.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.2, fill: { color: "E5DDD5" }, line: { color: "D8D2CA", width: 1 }, objectName: "chat background" });
  slide.addShape(pres.ShapeType.roundRect, { x: o.x, y: o.y, w: o.w, h: 0.55, rectRadius: 0.2, fill: { color: "075E54" }, line: { color: "075E54" }, objectName: "chat header" });
  slide.addShape(pres.ShapeType.rect, { x: o.x, y: o.y + 0.3, w: o.w, h: 0.25, fill: { color: "075E54" }, line: { color: "075E54" }, objectName: "chat header fill" });
  slide.addText("Friend", { x: o.x + 0.25, y: o.y + 0.05, w: 3, h: 0.45, fontSize: 14, bold: true, color: "FFFFFF", isTextBox: true, margin: 0, valign: "middle", objectName: "chat header name" });
  slide.addShape(pres.ShapeType.roundRect, { x: o.x + 0.25, y: o.y + 0.8, w: Math.min(o.w - 1.2, 0.22 * o.line.length + 0.6), h: 0.6, rectRadius: 0.12, fill: { color: "FFFFFF" }, line: { color: "FFFFFF" }, objectName: "friend bubble" });
  slide.addText(o.line, { x: o.x + 0.4, y: o.y + 0.8, w: Math.min(o.w - 1.5, 0.22 * o.line.length + 0.3), h: 0.6, fontSize: 14, color: "111B21", isTextBox: true, margin: 0, valign: "middle", objectName: "friend line" });
  const size = o.h - 1.75;
  if (o.sticker) {
    slide.addImage({ path: stk(o.sticker), x: o.x + o.w - size - 0.3, y: o.y + 1.55, w: size, h: size, objectName: "sticker " + o.sticker });
  } else {
    slide.addShape(pres.ShapeType.roundRect, { x: o.x + o.w - size - 0.3, y: o.y + 1.55, w: size, h: size, rectRadius: 0.25, fill: { color: "F0F0EE" }, line: { color: "898781", width: 1.5, dashType: "dash" }, objectName: "hidden sticker" });
    slide.addText("🙈 Sticker hidden\non purpose", { x: o.x + o.w - size - 0.3, y: o.y + 1.55, w: size, h: size, fontSize: 13, color: "898781", align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "hidden text" });
  }
}
function options(slide, y) {
  ["Positive", "Negative", "Sarcastic"].forEach((t, i) => {
    const x = 2.1 + i * 3.2;
    slide.addShape(pres.ShapeType.roundRect, { x, y, w: 2.9, h: 0.65, rectRadius: 0.3, fill: { color: "FFFFFF" }, line: { color: THEME.colors.lt2, width: 1.5 }, objectName: "option " + t });
    slide.addText(t, { x, y, w: 2.9, h: 0.65, fontSize: 18, bold: true, color: THEME.colors.dk1, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "option text " + t });
  });
}
function titleSlide(section, title, notes) {
  const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}

// ================================================================ ACT 1: cold open
pres.addSection({ title: "Cold open" });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Cold open" });
  placeholderBox(s, "PLACEHOLDER · slide 1\n\nFull-bleed WhatsApp Web screen recording (~20 s), stickers pouring in, cursor fumbling for the share button.\nDelete this box, insert the video, set it to autoplay. Nothing else on this slide.", { x: 1.5, y: 1.6, w: 10.33, h: 4.3, dark: true, fontSize: 18 });
  s.addNotes("Let it run a beat too long. Canyang: 'Burak. Burak.'");
}
{
  const s = pres.addSlide({ masterName: "BLANK", sectionTitle: "Cold open" });
  s.addText("Just kidding.", { x: 0.6, y: 1.9, w: 12.1, h: 2.2, fontSize: 104, bold: true, color: THEME.colors.dk1, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "just kidding" });
  s.addText("[PLACEHOLDER: your turn line, e.g. “…but we are going to talk about stickers today.”]", { x: 1.5, y: 4.3, w: 10.33, h: 0.8, fontSize: 22, color: THEME.colors.accent3, align: "center", valign: "middle", isTextBox: true, margin: 0, italic: true, objectName: "turn line placeholder" });
  s.addNotes("The turn. Keep it dry.");
}
{
  const s = titleSlide("Cold open", "AIPI Cohort Survey Results*", "Callback to the olive deck for anyone who saw it. One line, move on. 70 completed; 16 Turkish, 26 Chinese, 21 American natives; 11 came in through the flyer QR code.");
  s.addImage({ path: img("s03_sample_waffle.png"), x: 0.6, y: 1.55, w: 9.3, h: 3.2, objectName: "sample waffle" });
  bubble(s, "11 of them scanned the flyer 🧸", { x: 10.1, y: 1.8, w: 2.7, h: 1.0, tone: "green", bold: true, fontSize: 15, name: "flyer bubble" });
  bubble(s, "Collected Oct 31 – Nov 2 on one link, WhatsApp, WeChat and a flyer.", { x: 10.1, y: 3.1, w: 2.7, h: 1.3, tone: "white", fontSize: 12, name: "collection bubble" });
  s.addText("*This time we actually ran a survey.", { x: 0.6, y: 6.3, w: 12.1, h: 0.4, fontSize: 13, italic: true, color: THEME.colors.dk2, isTextBox: true, margin: 0, objectName: "footnote" });
}

// ================================================================ ACT 2: the question
pres.addSection({ title: "The question" });
{
  const s = titleSlide("The question", "Our group chat runs on these", "Half the chat is Turkish. The other half laughs at Bülent Arınç crying. Do they get it, or are they being polite? Motivation in one breath.");
  [0, 1, 2].forEach((i) => placeholderBox(s, `PLACEHOLDER\ngroup-chat screenshot ${i + 1}\n(faces blurred, names cropped)`, { x: 0.9 + i * 4.2, y: 1.6, w: 3.6, h: 4.9, fontSize: 13 }));
}
{
  const s = titleSlide("The question", "Can you read a sticker from another culture?", "Name the literature in one phrase: the in-group advantage in emotion recognition (Elfenbein & Ambady 2002), but for stickers. H1 is the randomized one; H2 is measured; H4 is the chance test; H5 is the control for 'is it just the message?'.");
  const qs = [
    ["H1", "Does seeing the sticker inside a chat help?", "the randomized one"],
    ["H2", "Do natives read their own stickers better?", "the in-group advantage"],
    ["H4", "Can outsiders beat chance with no context at all?", "sentiment leaking through the image"],
    ["H5", "…and is it the sticker, or just the message?", "the text-only control"],
  ];
  qs.forEach(([h, q, sub], i) => {
    const y = 1.6 + i * 1.22;
    s.addShape(pres.ShapeType.ellipse, { x: 0.7, y: y + 0.18, w: 0.7, h: 0.7, fill: { color: i === 0 ? THEME.colors.accent1 : THEME.colors.lt2 }, line: { color: i === 0 ? THEME.colors.accent1 : THEME.colors.lt2 }, objectName: "h badge " + h });
    s.addText(h, { x: 0.7, y: y + 0.18, w: 0.7, h: 0.7, fontSize: 14, bold: true, color: i === 0 ? "FFFFFF" : THEME.colors.dk1, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "h badge text " + h });
    bubble(s, [{ text: q, options: { bold: true, fontSize: 18, breakLine: true } }, { text: sub, options: { fontSize: 12, color: THEME.colors.dk2 } }], { x: 1.6, y, w: 7.3, h: 1.05, tone: "white", name: "hypothesis " + h });
  });
  [["TR_NOTXT_01", "Turkish"], ["CN_TXT_02", "Chinese"], ["EN_NOTXT_01", "English"]].forEach(([id, lab], i) => {
    s.addImage({ path: stk(id), x: 9.95, y: 1.6 + i * 1.6, w: 1.45, h: 1.45, objectName: "decor " + id });
    s.addText(lab, { x: 11.5, y: 1.6 + i * 1.6, w: 1.3, h: 1.45, fontSize: 13, color: THEME.colors.dk2, valign: "middle", isTextBox: true, margin: 0, objectName: "decor label " + lab });
  });
  s.addText("12 stickers per culture · 36 in total", { x: 9.6, y: 6.45, w: 3.3, h: 0.4, fontSize: 12, color: THEME.colors.dk2, align: "center", isTextBox: true, margin: 0, objectName: "decor caption" });
}

// ================================================================ ACT 3: the experiment
pres.addSection({ title: "The experiment" });
const LIVE = [
  { id: "TR_NOTXT_02", line: "I ate your leftover pizza", intent: "sarcastic", alone: "22%", chat: "23%", who: "a Turkish singer, İbrahim Tatlıses" },
  { id: "CN_TXT_05", line: "How are you holding up after staying up all night?", intent: "sarcastic", alone: "21%", chat: "35%", who: "“没事啊 我很好啊” — “It's fine, I'm great”" },
];
LIVE.forEach((L, k) => {
  const a = pres.addSlide({ masterName: "BLANK", sectionTitle: "The experiment" });
  a.addText(`Live round ${k + 1} · What does the sender mean?`, { x: 0.6, y: 0.4, w: 12.1, h: 0.6, fontSize: 20, color: THEME.colors.dk2, isTextBox: true, margin: 0, objectName: "live title" });
  a.addImage({ path: stk(L.id), x: 4.67, y: 1.2, w: 4.0, h: 4.0, objectName: "live sticker " + L.id });
  options(a, 5.6);
  a.addNotes(`Show alone, class votes by hand. Then next slide: same sticker in chat, vote again. Sender intent: ${L.intent}.`);

  const b = pres.addSlide({ masterName: "BLANK", sectionTitle: "The experiment" });
  b.addText(`Live round ${k + 1} · …and now inside the chat`, { x: 0.6, y: 0.4, w: 12.1, h: 0.6, fontSize: 20, color: THEME.colors.dk2, isTextBox: true, margin: 0, objectName: "live title chat" });
  chatMock(b, { x: 3.4, y: 1.15, w: 6.5, h: 4.2, line: L.line, sticker: L.id });
  options(b, 5.6);
  b.addText(`Reveal: sender intent = ${L.intent} · outsiders got it ${L.alone} alone, ${L.chat} in chat · ${L.who}`, { x: 0.6, y: 6.5, w: 12.1, h: 0.5, fontSize: 12, color: THEME.colors.accent6, align: "center", isTextBox: true, margin: 0, objectName: "reveal" });
  b.addNotes(`Vote again, then reveal. Non-native readers: ${L.alone} correct alone, ${L.chat} in chat.`);
});
{
  const s = titleSlide("The experiment", "36 stickers, 3 cultures, 3 ways to see them", "Within-subject. Every participant sees every sticker exactly once, in one of three contexts. A Latin square (three sets of 12, three rotations) means every sticker appears in every context equally often across people. Context is randomized; native-or-not is measured. The answer key is sender intent: the author of each set labeled what they mean when they send it.");
  const shots = [["task_alone.png", "Sticker alone"], ["task_chat.png", "Sticker in chat"], ["task_text_only.png", "Message only"]];
  shots.forEach(([f, lab], i) => {
    const x = 0.6 + i * 2.45;
    s.addImage({ path: img(f), x, y: 1.5, w: 2.25, h: 4.6, objectName: "task " + lab });
    s.addText(lab, { x, y: 6.15, w: 2.25, h: 0.4, fontSize: 13, bold: true, color: THEME.colors.dk1, align: "center", isTextBox: true, margin: 0, objectName: "task label " + lab });
  });
  const facts = [
    ["12 per culture", "6 with text on the sticker, 6 without · 2 positive / 2 negative / 2 sarcastic in each half"],
    ["Every sticker once", "37 trials per person (36 + an attention check), order shuffled"],
    ["Latin square", "3 sets × 3 rotations, so each sticker gets each context equally often"],
    ["Answer key = sender intent", "the author of each culture's set labeled their own stickers; natives then checked them"],
  ];
  facts.forEach(([h, d], i) => bubble(s, [{ text: h, options: { bold: true, fontSize: 15, breakLine: true } }, { text: d, options: { fontSize: 12, color: THEME.colors.dk2 } }], { x: 8.2, y: 1.5 + i * 1.22, w: 4.6, h: 1.08, tone: "white", name: "fact " + h }));
}
{
  const s = titleSlide("The experiment", "How many people did we need?", "Paired t-test on per-person accuracy, alpha .05, 80% power, d_z = 0.4 (moderate) gives n = 52 with statsmodels TTestPower. We also simulated the real trial structure (12 binary trials per condition, participant and sticker random effects): a 10-point lift needs about 40 people. We collected 70; after the fact, the observed SD of the chat-minus-alone difference (0.18) means 70 people detect a 6-point lift. Natives per culture: 16, 26, 21, all above the 15 floor for the answer-key check.");
  s.addImage({ path: img("s08_power.png"), x: 0.6, y: 1.5, w: 8.3, h: 4.3, objectName: "power curve" });
  stat(s, "52", "planned · paired t, α = .05, power .80, d_z = 0.4", { x: 9.4, y: 1.5, w: 3.4, h: 1.3 });
  stat(s, "70", "collected · 16 / 26 / 21 natives per culture", { x: 9.4, y: 3.0, w: 3.4, h: 1.3, color: THEME.colors.accent1 });
  stat(s, "6 pts", "smallest context effect we could detect with 70 (observed SD = 0.18)", { x: 9.4, y: 4.5, w: 3.4, h: 1.4, size: 36 });
  caption(s, "Analytic: statsmodels TTestPower. Simulation: 1,000 synthetic studies per point with the real Latin-square structure. Effect size from Cohen's conventions (no prior study on stickers); pilot of 9 people used to sanity-check the SD.", 6.1);
}

// ================================================================ ACT 4: results
pres.addSection({ title: "Results" });
{
  const s = titleSlide("Results", "Context helps. +11 points.", "H1 confirmed: chat > alone by 11.3 points, 95% CI 6.6 to 16.0, d_z = 0.58, t(69) = 4.82, p < .0001. Differences were normal (Shapiro p = .29); Wilcoxon agrees. H5 too: chat > message-only by 7.5 points, p = .002, so the sticker adds meaning beyond the words. RM-ANOVA over the three contexts F = 10.8, p < .0001, partial eta squared .14, sphericity fine; Holm post hocs: alone < chat, chat > message-only, alone vs message-only not significant.");
  s.addImage({ path: img("s09_context_pictogram.png"), x: 0.6, y: 1.45, w: 12.1, h: 3.6, objectName: "context pictogram" });
  bubble(s, "Paired t-test, n = 70: chat − alone = +11.3 pts, 95% CI [6.6, 16.0], d_z = 0.58, p < .0001", { x: 0.6, y: 5.25, w: 5.9, h: 0.85, tone: "green", fontSize: 13, bold: true, name: "h1 bubble" });
  bubble(s, "Repeated-measures ANOVA across the three contexts: F = 10.8, p < .0001, η²p = .14. Holm post hocs: chat > alone (p < .0001), chat > message-only (p = .004), alone ≈ message-only (p = .17).", { x: 6.8, y: 5.25, w: 5.9, h: 0.85, tone: "white", fontSize: 11.5, name: "anova bubble" });
  caption(s, "Each square is 10% of trials answered correctly. Error bars are 95% CIs of the per-person mean. The sticker adds +7.5 points over the message alone (H5, p = .002).", 6.3);
}
{
  const s = titleSlide("Results", "Natives win… until you hide the sticker", "H2 confirmed: natives are better on their own culture's stickers, odds ratio 1.51 (95% CI 1.26 to 1.81) from a mixed logistic regression with crossed random intercepts for participant and sticker. H3 was NOT what we predicted: chat helped insiders and outsiders about equally (chat × native interaction OR 1.33, p = .13). The interaction that did show up: hide the sticker and natives lose their edge entirely (message-only × native OR 0.65, p = .005). Natives are reading the picture, not the caption.");
  s.addImage({ path: img("s10_interaction.png"), x: 0.6, y: 1.45, w: 8.0, h: 4.4, objectName: "interaction plot" });
  bubble(s, [{ text: "In-group advantage", options: { bold: true, fontSize: 15, breakLine: true } }, { text: "OR 1.51 [1.26, 1.81], p < .001 · mixed logistic regression, random intercepts for participant and sticker", options: { fontSize: 11.5, color: THEME.colors.dk2 } }], { x: 8.9, y: 1.5, w: 3.9, h: 1.3, tone: "white", name: "h2 bubble" });
  bubble(s, [{ text: "Context helps everyone", options: { bold: true, fontSize: 15, breakLine: true } }, { text: "chat × native interaction OR 1.33 [0.92, 1.90], p = .13 · H3 not supported", options: { fontSize: 11.5, color: THEME.colors.dk2 } }], { x: 8.9, y: 3.0, w: 3.9, h: 1.3, tone: "white", name: "h3 bubble" });
  bubble(s, [{ text: "Hide the sticker, lose the edge", options: { bold: true, fontSize: 15, breakLine: true } }, { text: "message-only × native OR 0.65 [0.48, 0.88], p = .005", options: { fontSize: 11.5, color: "FFFFFF" } }], { x: 8.9, y: 4.5, w: 3.9, h: 1.3, tone: "green", name: "interaction bubble" });
  caption(s, "Per-person means ± 95% CI. 'Some' familiarity excluded here (pre-registered: native vs none). Sticker-to-sticker variance is 4× participant variance: which sticker matters more than who is reading.", 6.1);
}
{
  const s = titleSlide("Results", "Outsiders are not guessing", "H4: on no-text stickers from other cultures, with no chat context, outsiders scored 67% against a 33% chance rate. Exact binomial p < .0001, Cohen's h = 0.69; per-person one-sample t also p < .0001. Sentiment leaks through the image. Except when a man points a gun at you as a joke.");
  stat(s, "67%", "of outsiders' answers correct on no-text stickers with no context · chance is 33% · binomial p < .0001, h = 0.69", { x: 0.6, y: 1.4, w: 4.2, h: 2.2, size: 72 });
  s.addImage({ path: img("s11_chance_swarm.png"), x: 5.0, y: 1.4, w: 7.8, h: 3.0, objectName: "chance swarm" });
  s.addText("Hardest for outsiders", { x: 0.6, y: 4.6, w: 5, h: 0.4, fontSize: 14, bold: true, color: THEME.colors.dk1, isTextBox: true, margin: 0, objectName: "hardest label" });
  [["TR_NOTXT_02", "22%", "a joke threat"], ["EN_TXT_05", "24%", "“No, this is Patrick!”"], ["CN_TXT_05", "29%", "“It's fine, I'm great”"]].forEach(([id, pct, why], i) => {
    const x = 0.6 + i * 2.2;
    s.addImage({ path: stk(id), x, y: 5.05, w: 1.3, h: 1.3, objectName: "hard " + id });
    s.addText([{ text: pct, options: { bold: true, fontSize: 18, color: THEME.colors.accent3, breakLine: true } }, { text: why, options: { fontSize: 10, color: THEME.colors.dk2 } }], { x: x + 1.35, y: 5.05, w: 0.95, h: 1.3, isTextBox: true, margin: 0, valign: "middle", objectName: "hard text " + id });
  });
  caption(s, "Sarcastic stickers are the ones that fail: a sticker that says one thing and means another needs the culture to decode it.", 6.5);
}
{
  const s = titleSlide("Results", "Sarcasm is where authors and natives part ways", "The pre-registered answer-key check: for each sticker, do natives (with the sticker visible) agree with the author's label at least 50% of the time? 6 of 36 fail, all sarcastic or negative. We wrote down what WE mean when we send these; our own communities disagreed on exactly the sarcastic ones. All conclusions hold with these six removed (H1 +9.7 points, p = .0006).");
  s.addImage({ path: img("s12_flagged.png"), x: 0.6, y: 1.4, w: 9.2, h: 4.9, objectName: "flagged stickers" });
  bubble(s, "6 of 36 stickers flagged. All six are sarcastic or negative.", { x: 10.1, y: 1.6, w: 2.7, h: 1.2, tone: "green", bold: true, fontSize: 14, name: "flag count" });
  bubble(s, "Rerun without them: chat − alone = +9.7 pts, p = .0006. Nothing changes.", { x: 10.1, y: 3.0, w: 2.7, h: 1.3, tone: "white", fontSize: 12, name: "flag robust" });
  bubble(s, "Rule was written before data collection: < 50% native agreement, at least 5 ratings.", { x: 10.1, y: 4.5, w: 2.7, h: 1.3, tone: "muted", fontSize: 12, name: "flag rule" });
}

// ================================================================ ACT 5: close
pres.addSection({ title: "Close" });
{
  const s = titleSlide("Close", "What the data cannot tell us", "Convenience sample; native-or-not measured not randomized; one author's intent per culture as the key; the attention check was ambiguous and we say how we handled it. The pre-registered exclusion gives the same conclusions.");
  const lims = [
    ["🧑‍🤝‍🧑", "Convenience sample", "Friends, classmates, WeChat groups. Young, online, mostly students."],
    ["🎲", "Native-or-not was measured, not randomized", "The context effect is causal; the in-group effect is quasi-experimental."],
    ["✍️", "The answer key is one person's intent per culture", "Validated by natives, but sarcasm is inherently contested, and 6 stickers show it."],
    ["🪤", "Our attention check was itself ambiguous", "“Select POSITIVE” vs “what does the sender mean?” 6 of 8 ‘failures’ chose sarcastic. We kept them (they behaved like everyone else); the pre-registered exclusion gives the same answers."],
  ];
  lims.forEach(([icon, h, d], i) => {
    const x = 0.6 + (i % 2) * 6.2, y = 1.5 + Math.floor(i / 2) * 2.5;
    s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.2, w: 0.8, h: 0.8, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.lt2 }, objectName: "lim icon " + i });
    s.addText(icon, { x, y: y + 0.2, w: 0.8, h: 0.8, fontSize: 22, align: "center", valign: "middle", isTextBox: true, margin: 0, objectName: "lim emoji " + i });
    bubble(s, [{ text: h, options: { bold: true, fontSize: 15, breakLine: true } }, { text: d, options: { fontSize: 12, color: THEME.colors.dk2 } }], { x: x + 1.0, y, w: 4.9, h: 2.1, tone: "white", name: "lim " + i });
  });
}
{
  const s = titleSlide("Close", "Takeaway", "One sentence, then the draw. Two winners: one from everyone, one reserved for AIPI students in the room.");
  bubble(s, "The sticker carries the meaning. Context helps everyone by about 11 points, but the picture is what natives are reading, and sarcasm is the part that doesn't travel.", { x: 0.6, y: 1.6, w: 6.6, h: 2.3, tone: "green", bold: true, fontSize: 20, name: "takeaway" });
  bubble(s, "If you want a sticker to land across cultures: no text, no sarcasm, and send it in a chat, not on its own.", { x: 0.6, y: 4.1, w: 6.6, h: 1.3, tone: "white", fontSize: 14, name: "recommendation" });
  s.addImage({ path: img("squishy.png"), x: 7.9, y: 1.5, w: 4.9, h: 3.6, objectName: "squishy" });
  s.addText("Draw time 🧸", { x: 7.9, y: 5.2, w: 4.9, h: 0.7, fontSize: 30, bold: true, color: THEME.colors.accent1, align: "center", isTextBox: true, margin: 0, objectName: "draw time" });
  s.addText("[PLACEHOLDER: winner reveal · closing joke footnote]", { x: 0.6, y: 6.2, w: 12.1, h: 0.5, fontSize: 13, italic: true, color: THEME.colors.accent3, isTextBox: true, margin: 0, objectName: "closer placeholder" });
}

// ================================================================ appendix
pres.addSection({ title: "Appendix" });
{
  const s = titleSlide("Appendix", "All 36 stickers, ranked by how outsiders read them", "Non-native readers, sticker visible. Bar colour is the sticker's culture.");
  s.addImage({ path: img("s15_ranking.png"), x: 0.6, y: 1.45, w: 12.1, h: 5.3, objectName: "ranking" });
}
{
  const s = titleSlide("Appendix", "The numbers", "Everything the report tests, on one slide.");
  const hdr = { bold: true, color: "FFFFFF", fill: { color: THEME.colors.accent1 }, fontSize: 11, fontFace: "Avenir Next" };
  const cell = { fontSize: 10.5, color: THEME.colors.dk1, fontFace: "Avenir Next", valign: "middle" };
  const rows = [
    [{ text: "Hypothesis", options: hdr }, { text: "Test", options: hdr }, { text: "Result", options: hdr }, { text: "Effect size", options: hdr }, { text: "p", options: hdr }],
    ["H1 chat > alone", "Paired t-test on per-person accuracy (n = 70); Shapiro p = .29; Wilcoxon agrees", "+11.3 pts, 95% CI [6.6, 16.0]", "d_z = 0.58", "< .0001"],
    ["Context (3 levels)", "One-way repeated-measures ANOVA; Mauchly p = .18 (no correction needed); Friedman agrees", "F = 10.8", "η²p = .14", "< .0001"],
    ["Post hocs (Holm)", "alone vs chat · chat vs message-only · alone vs message-only", "−11.3 · +7.5 · −3.8 pts", "d = −0.76 · 0.48 · −0.25", "< .0001 · .004 · .17"],
    ["H5 chat > message-only", "Paired t-test", "+7.5 pts, 95% CI [2.9, 12.1]", "d_z = 0.39", ".002"],
    ["H2 in-group advantage", "Mixed logistic regression, random intercepts: participant + sticker (1,543 trials)", "OR 1.51 [1.26, 1.81]", "", "< .001"],
    ["H3 context × in-group", "same model, interaction terms", "chat × native OR 1.33 [0.92, 1.90]; message-only × native OR 0.65 [0.48, 0.88]", "", ".13 · .005"],
    ["H4 outsiders > chance", "Exact binomial vs 1/3 (276 trials); per-person one-sample t (n = 55)", "67% vs 33%", "h = 0.69; d = 1.54", "< .0001"],
    ["Sensitivity", "Pre-registered attention exclusion (n = 57); 6 flagged stickers removed", "H1 +9.7 pts in both", "d_z = 0.51 / 0.43", ".0003 / .0006"],
  ].map((r, i) => (i === 0 ? r : r.map((t) => ({ text: t, options: cell }))));
  s.addTable(rows, { x: 0.6, y: 1.45, w: 12.1, colW: [2.1, 4.2, 2.6, 1.6, 1.6], border: { type: "solid", color: THEME.colors.lt2, pt: 0.75 }, fill: { color: "FFFFFF" }, rowH: 0.5, autoPage: false, objectName: "results table" });
}
{
  const s = titleSlide("Appendix", "People know when they are guessing", "Accuracy climbs with confidence from 45% to 80%. Meme fluency, sticker-use frequency, bilingualism and age did not predict out-group accuracy (all p > .16 in the covariate model).");
  s.addImage({ path: img("s16_calibration.png"), x: 0.6, y: 1.45, w: 7.6, h: 4.0, objectName: "calibration" });
  bubble(s, "What did NOT predict decoding other cultures' stickers: meme fluency (p = .36), daily sticker use (p = .64), being bilingual (p = .78), age (p = .16).", { x: 8.5, y: 1.6, w: 4.3, h: 2.2, tone: "white", fontSize: 13, name: "covariates" });
  bubble(s, "Reaction times: median 3.7 s per sticker; the task took about 5 minutes.", { x: 8.5, y: 4.0, w: 4.3, h: 1.1, tone: "muted", fontSize: 12, name: "rt" });
}

// ---------------------------------------------------------------- write
(async () => {
  await pres.writeFile({ fileName: OUTFILE });
  await applyTheme(OUTFILE, THEME);
  console.log("wrote", OUTFILE);
})();
