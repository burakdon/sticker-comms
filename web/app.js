/* Sticker sentiment task.
 *
 * Flow: intro -> pre-survey -> instructions -> 36 trials + 1 attention check
 *       -> optional free-text block -> thank-you (submit).
 *
 * Randomization happens here, on the client:
 *   - rotation (0/1/2) is drawn at random and maps sticker sets A/B/C onto the
 *     context conditions (alone / chat / text_only) via conditions.json
 *   - trial order is shuffled per participant
 *   - the attention check is inserted at a random position in the middle
 *
 * Data goes to the Apps Script endpoint in config.js as one JSON payload at the
 * end (plus a tiny "start" ping so drop-outs can be counted). Payloads are kept
 * in localStorage until the server confirms them, and re-sent on the next visit.
 */
(() => {
  "use strict";

  const CFG = window.STICKER_CONFIG || {};
  const PENDING_PREFIX = "sticker_pending_";
  const LOCAL_PREFIX = "sticker_local_";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  let conditions = null;
  let state = null;
  let stimulusLoad = 0;

  // A missing/slow image must never become an answerable blank trial.
  function waitForStimulus(container, ready, failed) {
    const token = ++stimulusLoad;
    const img = $(container).querySelector("img.sticker");
    if (!img) { ready(); return; } // text_only intentionally has no image
    let settled = false;
    let timer;
    const settle = (ok) => {
      if (settled || token !== stimulusLoad) return;
      settled = true;
      clearTimeout(timer);
      img.onload = img.onerror = null;
      (ok ? ready : failed)();
    };
    img.onload = () => settle(img.naturalWidth > 0);
    img.onerror = () => settle(false);
    timer = setTimeout(() => settle(false), 15000);
    if (img.complete) settle(img.naturalWidth > 0);
  }

  // ---------- helpers ----------

  const uid = () =>
    Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-4);

  const isoNow = () => new Date().toISOString();

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  const deviceType = () =>
    /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ? "mobile" : "desktop";

  // Stimulus paths in stimuli.csv are relative to the repo root; the page lives in web/.
  const assetUrl = (file) => (/^https?:\/\//i.test(file) ? file : "../" + file);

  const escapeHtml = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function show(id) {
    $$(".screen").forEach((el) => (el.hidden = true));
    $(id).hidden = false;
    window.scrollTo(0, 0);
  }

  function preload(stickers) {
    stickers.forEach((s) => {
      if (!s.file) return;
      const img = new Image();
      img.src = assetUrl(s.file);
    });
  }

  // ---------- trial construction ----------

  function buildTrials(rotation) {
    const rot = conditions.rotations[String(rotation)]; // e.g. {alone:"A", chat:"B", text_only:"C"}
    const setToContext = {};
    Object.entries(rot).forEach(([ctx, set]) => (setToContext[set] = ctx));

    const stickers = conditions.stickers.filter((s) => s.culture !== "ATTN" && s.set);
    const trials = shuffle(stickers.map((s) => ({ sticker: s, context: setToContext[s.set] })));

    const attn = conditions.stickers.find((s) => s.culture === "ATTN");
    if (attn) {
      const pos = Math.floor(trials.length / 3) + Math.floor(Math.random() * Math.floor(trials.length / 3));
      trials.splice(pos, 0, { sticker: attn, context: "alone", attention: true });
    }
    return trials;
  }

  function renderStimulus(trial) {
    const s = trial.sticker;
    const img = `<img class="sticker" src="${assetUrl(s.file)}" alt="" draggable="false">`;
    if (trial.context === "alone") return `<div class="alone">${img}</div>`;

    const you =
      trial.context === "chat"
        ? img
        : `<div class="sticker hidden-sticker"><span>sticker hidden</span></div>`;
    return `
      <div class="chat">
        <div class="chat-header"><span class="avatar">👤</span>Friend</div>
        <div class="chat-body">
          <div class="bubble them">${escapeHtml(s.chat_line || "")}<span class="time">10:42</span></div>
          <div class="bubble me sticker-bubble">${you}<span class="time">10:43</span></div>
        </div>
      </div>`;
  }

  // ---------- screens ----------

  function onStart() {
    show("#screen-survey");
  }

  function onSurveySubmit(ev) {
    ev.preventDefault();
    const form = ev.target;
    let ok = true;
    $$("#survey-form fieldset").forEach((fs) => {
      if (fs.hidden) return;
      const req = fs.querySelector("[required]");
      if (!req) return;
      let valid = req.type === "radio" ? !!fs.querySelector("input:checked") : req.value.trim() !== "";
      if (req.type === "number" && valid) valid = Number(req.value) >= 18 && Number(req.value) <= 99;
      fs.classList.toggle("invalid", !valid);
      ok = ok && valid;
    });
    // "Which ones?" is required only when bilingual = yes.
    const langField = $("#other-languages-field");
    if (!langField.hidden) {
      const valid = $("#other_languages").value.trim() !== "";
      langField.classList.toggle("invalid", !valid);
      ok = ok && valid;
    }
    $("#survey-error").hidden = ok;
    if (!ok) return;

    const data = Object.fromEntries(new FormData(form).entries());
    const rotation = Math.floor(Math.random() * 3);
    state = {
      participant: {
        participant_id: uid(),
        rotation,
        fam_turkish: data.fam_turkish,
        fam_chinese: data.fam_chinese,
        fam_american: data.fam_american,
        meme_fluency: Number(data.meme_fluency),
        native_language: data.native_language.trim(),
        bilingual: data.bilingual,
        other_languages: data.bilingual === "yes" ? (data.other_languages || "").trim() : "",
        // Stored under the existing `age_bracket` column (now a plain number) so
        // the sheet layout and backend don't need to change.
        age_bracket: Number(data.age),
        sticker_use_frequency: data.sticker_use_frequency,
        device: deviceType(),
        user_agent: navigator.userAgent,
        screen_width: window.screen.width,
        started_at: isoNow(),
        finished_at: null,
        passed_attention_check: null,
      },
      trials: buildTrials(rotation),
      i: 0,
      results: [],
      freetext: [],
      current: null,
    };

    sendStartPing();
    show("#screen-instructions");
  }

  function beginTrials() {
    show("#screen-trial");
    showTrial();
  }

  function showTrial() {
    const t = state.trials[state.i];
    const n = state.trials.length;
    $("#progress").textContent = `${state.i + 1} / ${n}`;
    $("#progress-fill").style.width = `${(state.i / n) * 100}%`;
    $("#stimulus").innerHTML = renderStimulus(t);
    $("#confidence").hidden = true;
    $("#choices").hidden = false;
    $$(".choice").forEach((b) => (b.disabled = true));
    state.current = null;
    $("#stimulus-error").hidden = true;
    $("#stimulus-loading").hidden = false;
    waitForStimulus("#stimulus", () => {
      $("#stimulus-loading").hidden = true;
      state.current = { shownAt: performance.now(), changes: 0 };
      $$(".choice").forEach((b) => (b.disabled = false));
    }, () => {
      $("#stimulus-loading").hidden = true;
      $("#stimulus-error").hidden = false;
    });
  }

  // Back from the confidence step to the three options. The first reaction
  // time is kept; the change is flagged so it can be inspected in cleaning.
  function onChangeAnswer() {
    if (!state.current || !state.current.response) return;
    state.current.response = null;
    state.current.changes += 1;
    $("#confidence").hidden = true;
    $("#choices").hidden = false;
    $$(".choice").forEach((b) => (b.disabled = false));
  }

  function onChoice(ev) {
    const btn = ev.currentTarget;
    if (!state.current || state.current.response) return;
    state.current.response = btn.dataset.response;
    if (state.current.rt_ms === undefined) {
      state.current.rt_ms = Math.round(performance.now() - state.current.shownAt);
    }
    $$(".choice").forEach((b) => (b.disabled = true));
    $("#choices").hidden = true;
    $("#confidence").hidden = false;
    $$(".conf").forEach((b) => (b.disabled = false));
  }

  function onConfidence(ev) {
    if (!state.current || !state.current.response) return;
    $$(".conf").forEach((b) => (b.disabled = true));
    const t = state.trials[state.i];
    state.results.push({
      participant_id: state.participant.participant_id,
      sticker_id: t.sticker.sticker_id,
      trial_order: state.i + 1,
      context: t.context,
      is_attention_check: t.attention ? 1 : 0,
      response: state.current.response,
      confidence: Number(ev.currentTarget.dataset.confidence),
      rt_ms: state.current.rt_ms,
      changed_answer: state.current.changes,
    });
    state.current = null;
    state.i += 1;
    if (state.i < state.trials.length) showTrial();
    else startBonus();
  }

  // ---------- bonus free-text block ----------

  function startBonus() {
    const n = Number(CFG.N_BONUS) || 0;
    const pool = shuffle(conditions.stickers.filter((s) => s.culture !== "ATTN" && s.file));
    state.bonus = pool.slice(0, n);
    state.bonusIdx = 0;
    if (!state.bonus.length) return finish();
    show("#screen-bonus");
    showBonus();
  }

  function showBonus() {
    const s = state.bonus[state.bonusIdx];
    $("#bonus-progress").textContent = `${state.bonusIdx + 1} of ${state.bonus.length}`;
    $("#bonus-progress-fill").style.width = `${(state.bonusIdx / state.bonus.length) * 100}%`;
    $("#bonus-stimulus").innerHTML = `<div class="alone"><img class="sticker" src="${assetUrl(s.file)}" alt="" draggable="false"></div>`;
    $("#bonus-text").value = "";
    $("#bonus-error").hidden = true;
    $("#btn-bonus-next").disabled = true;
    $("#bonus-text").disabled = true;
    waitForStimulus("#bonus-stimulus", () => {
      $("#btn-bonus-next").disabled = false;
      $("#bonus-text").disabled = false;
    }, () => { $("#bonus-error").hidden = false; });
  }

  function onBonusNext(skip) {
    const s = state.bonus[state.bonusIdx];
    const text = skip ? "" : $("#bonus-text").value.trim();
    if (text) {
      state.freetext.push({ participant_id: state.participant.participant_id, sticker_id: s.sticker_id, text });
    }
    state.bonusIdx += 1;
    if (state.bonusIdx < state.bonus.length) showBonus();
    else finish();
  }

  // ---------- submission ----------

  function buildPayload() {
    const attn = state.results.find((r) => r.is_attention_check);
    state.participant.finished_at = isoNow();
    state.participant.passed_attention_check = attn ? (attn.response === "positive" ? 1 : 0) : null;
    state.participant.n_trials = state.results.length;
    return {
      type: "complete",
      secret: CFG.SECRET,
      participant: state.participant,
      trials: state.results,
      freetext: state.freetext,
    };
  }

  async function post(payload) {
    // text/plain avoids a CORS preflight, which Apps Script cannot answer.
    const res = await fetch(CFG.ENDPOINT_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(payload),
      redirect: "follow",
    });
    const json = await res.json();
    return json && json.ok === true;
  }

  function sendStartPing() {
    if (!CFG.ENDPOINT_URL) return;
    const p = state.participant;
    post({
      type: "start",
      secret: CFG.SECRET,
      participant: { participant_id: p.participant_id, started_at: p.started_at, device: p.device, user_agent: p.user_agent },
    }).catch(() => {});
  }

  function setStatus(text) {
    $("#save-status").textContent = text;
  }

  function download(payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `sticker-comms_${payload.participant.participant_id}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  async function finish() {
    show("#screen-done");
    if (CFG.CONTACT) $("#contact").textContent = `Questions? ${CFG.CONTACT}`;
    const payload = buildPayload();
    const key = (CFG.ENDPOINT_URL ? PENDING_PREFIX : LOCAL_PREFIX) + payload.participant.participant_id;
    try { localStorage.setItem(key, JSON.stringify(payload)); } catch (_) { /* private mode */ }

    $("#btn-download").onclick = () => download(payload);

    if (!CFG.ENDPOINT_URL) {
      $("#done-title").textContent = "Thank you!";
      $("#closing").hidden = false;
      setStatus("Done.");
      $("#local-note").hidden = false;
      $("#save-actions").hidden = false;
      $("#btn-retry").hidden = true;
      return;
    }

    const attempt = async () => {
      setStatus("Saving your answers, hang on a second. The squishy draw is next 🧸");
      $("#save-actions").hidden = true;
      let ok = false;
      try { ok = await post(payload); } catch (_) { ok = false; }
      if (ok) {
        try { localStorage.removeItem(key); } catch (_) {}
        $("#done-title").textContent = "Thank you!";
        setStatus("Saved. Two quick things before you go:");
        $("#giveaway-form").hidden = false;
        $("#secret-form").hidden = false;
        $("#closing").hidden = false;
      } else {
        setStatus("Could not reach the server. Check your connection and tap Retry, or download your answers and send them to us.");
        $("#save-actions").hidden = false;
      }
    };
    $("#btn-retry").onclick = attempt;
    attempt();
  }

  // Giveaway entry: name + contact go to their own sheet tab, linked only by
  // participant_id, and are never exported with the study data.
  async function onGiveawaySubmit(ev) {
    ev.preventDefault();
    const name = $("#gw-name").value.trim();
    const contact = $("#gw-contact").value.trim();
    const status = $("#gw-status");
    status.hidden = false;
    if (!name || !contact) {
      status.textContent = "Please fill in both fields.";
      return;
    }
    const btn = $("#giveaway-form button");
    btn.disabled = true;
    status.textContent = "Entering…";
    let ok = false;
    try {
      ok = await post({
        type: "giveaway",
        secret: CFG.SECRET,
        entry: { participant_id: state.participant.participant_id, name, contact },
      });
    } catch (_) { ok = false; }
    if (ok) {
      status.textContent = "You're in the draw. Good luck!";
      $("#gw-name").disabled = true;
      $("#gw-contact").disabled = true;
    } else {
      status.textContent = "Could not reach the server. Please try again.";
      btn.disabled = false;
    }
  }

  // Secret question: AIPI cohort + two course grades, stored in their own
  // sheet tab keyed by participant_id. Optional; skipping sends nothing.
  async function onSecretSubmit(ev) {
    ev.preventDefault();
    const status = $("#secret-status");
    const cohort = ($("input[name=aipi_cohort]:checked") || {}).value;
    status.hidden = false;
    if (!cohort) {
      status.textContent = "Pick yes or no, or tap Skip.";
      return;
    }
    const entry = {
      participant_id: state.participant.participant_id,
      aipi_cohort: cohort,
      aipi520_midterm: cohort === "yes" ? $("#g520").value.trim() : "",
      aipi510_project1: cohort === "yes" ? $("#g510").value.trim() : "",
    };
    const btns = $$("#secret-form button");
    btns.forEach((b) => (b.disabled = true));
    status.textContent = "Sending…";
    let ok = false;
    try { ok = await post({ type: "extra", secret: CFG.SECRET, entry }); } catch (_) { ok = false; }
    if (ok) {
      status.textContent = cohort === "yes" ? "Got it. Our lips are sealed." : "Got it, thanks!";
      $$("#secret-form input").forEach((i) => (i.disabled = true));
    } else {
      status.textContent = "Could not reach the server. Please try again.";
      btns.forEach((b) => (b.disabled = false));
    }
  }

  // Re-send anything a previous visit could not deliver. Safe to repeat: the
  // server ignores participant_ids it already has.
  async function resendPending() {
    if (!CFG.ENDPOINT_URL) return;
    let keys = [];
    try { keys = Object.keys(localStorage).filter((k) => k.startsWith(PENDING_PREFIX)); } catch (_) { return; }
    for (const key of keys) {
      try {
        const payload = JSON.parse(localStorage.getItem(key));
        if (await post(payload)) localStorage.removeItem(key);
      } catch (_) { /* try again next time */ }
    }
  }

  // ---------- init ----------

  async function init() {
    try {
      const res = await fetch("conditions.json", { cache: "no-store" });
      conditions = await res.json();
    } catch (_) {
      $("#load-error").hidden = false;
      $("#btn-start").disabled = true;
      return;
    }
    preload(conditions.stickers);
    $("#n-stickers").textContent = conditions.stickers.filter((s) => s.set || s.culture === "ATTN").length;

    $("#btn-start").addEventListener("click", onStart);
    $("#survey-form").addEventListener("submit", onSurveySubmit);
    $$("input[name=bilingual]").forEach((r) =>
      r.addEventListener("change", () => {
        $("#other-languages-field").hidden = r.value !== "yes";
      })
    );
    $("#btn-begin").addEventListener("click", beginTrials);
    $("#btn-stimulus-retry").addEventListener("click", showTrial);
    $("#btn-bonus-retry").addEventListener("click", showBonus);
    $$(".choice").forEach((b) => b.addEventListener("click", onChoice));
    $$(".conf").forEach((b) => b.addEventListener("click", onConfidence));
    $("#btn-change").addEventListener("click", onChangeAnswer);
    $("#giveaway-form").addEventListener("submit", onGiveawaySubmit);
    $("#secret-form").addEventListener("submit", onSecretSubmit);
    $("#btn-secret-skip").addEventListener("click", () => ($("#secret-form").hidden = true));
    $$("input[name=aipi_cohort]").forEach((r) =>
      r.addEventListener("change", () => ($("#secret-grades").hidden = r.value !== "yes"))
    );
    $("#btn-bonus-next").addEventListener("click", () => onBonusNext(false));
    $("#btn-bonus-skip").addEventListener("click", () => onBonusNext(true));

    resendPending();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
