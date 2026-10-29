/**
 * Google Apps Script backend for the sticker study.
 *
 * Receives JSON from web/app.js and appends rows to a Google Sheet; serves the
 * same rows back to src/collection/export_responses.py.
 *
 * Setup (about 5 minutes, done once by whoever owns the sheet):
 *   1. Create a blank Google Sheet. Name it e.g. "sticker-comms responses".
 *   2. Extensions -> Apps Script. Delete the default code, paste this file.
 *   3. Change EXPORT_TOKEN below to a long random string. SECRET must match
 *      web/config.js (change both if you like).
 *   4. Deploy -> New deployment -> type "Web app".
 *        Execute as: Me.   Who has access: Anyone.
 *      Authorize when prompted. Copy the Web app URL.
 *   5. Paste that URL into ENDPOINT_URL in web/config.js and push.
 *   6. Test: open the task page, complete it, check the sheet gets rows.
 *
 * After editing this file you must redeploy (Deploy -> Manage deployments ->
 * edit -> New version) for the change to go live.
 */

var SECRET = "sticker-comms-2026";          // must match web/config.js
var EXPORT_TOKEN = "CHANGE-ME-to-a-long-random-string"; // keep private; used by export_responses.py

var SHEETS = {
  starts: ["participant_id", "started_at", "device", "user_agent", "received_at"],
  participants: [
    "participant_id", "rotation", "fam_turkish", "fam_chinese", "fam_american",
    "meme_fluency", "native_language", "bilingual", "other_languages",
    "age_bracket", "sticker_use_frequency",
    "device", "user_agent", "screen_width", "started_at", "finished_at",
    "passed_attention_check", "n_trials", "received_at",
  ],
  trials: [
    "participant_id", "sticker_id", "trial_order", "context", "is_attention_check",
    "response", "confidence", "rt_ms", "changed_answer",
  ],
  freetext: ["participant_id", "sticker_id", "text"],
};

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var body = JSON.parse(e.postData.contents);
    if (body.secret !== SECRET) return respond({ ok: false, error: "bad secret" });

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var now = new Date().toISOString();

    if (body.type === "start") {
      var p = body.participant || {};
      p.received_at = now;
      appendRows(ss, "starts", [p]);
      return respond({ ok: true });
    }

    if (body.type === "complete") {
      var participant = body.participant || {};
      if (!participant.participant_id) return respond({ ok: false, error: "no participant_id" });
      if (alreadyStored(ss, participant.participant_id)) {
        return respond({ ok: true, duplicate: true }); // client retry; nothing to do
      }
      participant.received_at = now;
      appendRows(ss, "participants", [participant]);
      appendRows(ss, "trials", body.trials || []);
      appendRows(ss, "freetext", body.freetext || []);
      return respond({ ok: true });
    }

    return respond({ ok: false, error: "unknown type" });
  } catch (err) {
    return respond({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

/**
 * GET ?token=EXPORT_TOKEN            -> all sheets as JSON
 * GET ?token=EXPORT_TOKEN&sheet=trials -> one sheet
 */
function doGet(e) {
  var params = (e && e.parameter) || {};
  if (params.token !== EXPORT_TOKEN) return respond({ ok: false, error: "bad token" });
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var names = params.sheet ? [params.sheet] : Object.keys(SHEETS);
  var out = { ok: true, exported_at: new Date().toISOString(), sheets: {} };
  names.forEach(function (name) {
    out.sheets[name] = readRows(ss, name);
  });
  return respond(out);
}

// ---------- helpers ----------

function getSheet(ss, name) {
  var cols = SHEETS[name];
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(cols);
    sheet.setFrozenRows(1);
    return sheet;
  }
  // Keep the header in sync when columns are added to SHEETS after deployment.
  // New columns are always appended at the end, so older rows stay aligned.
  var header = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  if (header.join("\u0001") !== cols.join("\u0001")) {
    sheet.getRange(1, 1, 1, cols.length).setValues([cols]);
  }
  return sheet;
}

function appendRows(ss, name, objects) {
  if (!objects.length) return;
  var cols = SHEETS[name];
  var sheet = getSheet(ss, name);
  var rows = objects.map(function (obj) {
    return cols.map(function (c) {
      var v = obj[c];
      return v === undefined || v === null ? "" : v;
    });
  });
  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, cols.length).setValues(rows);
}

function alreadyStored(ss, participantId) {
  var sheet = ss.getSheetByName("participants");
  if (!sheet || sheet.getLastRow() < 2) return false;
  var ids = sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getValues();
  for (var i = 0; i < ids.length; i++) {
    if (String(ids[i][0]) === String(participantId)) return true;
  }
  return false;
}

function readRows(ss, name) {
  var sheet = ss.getSheetByName(name);
  if (!sheet || sheet.getLastRow() < 2) return [];
  var values = sheet.getDataRange().getValues();
  var header = values[0];
  return values.slice(1).map(function (row) {
    var obj = {};
    header.forEach(function (h, i) { obj[h] = row[i]; });
    return obj;
  });
}

function respond(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
