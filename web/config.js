// Collection settings for the task page. Edit this file, nothing else, to deploy.
window.STICKER_CONFIG = {
  // Google Apps Script web-app URL (see backend/Code.gs). Leave empty for local
  // mode: responses stay in the browser and can be downloaded as JSON.
  ENDPOINT_URL: "https://script.google.com/macros/s/AKfycbwkAYp6vEZkZxtNRTT4UrmB7KSH07KXg5drR3Zl4sfFc3_VXxc-P9suVWvOwl7XptlY/exec",

  // Must match SECRET in backend/Code.gs. It only keeps random junk out of the
  // sheet; it is visible to anyone who reads this file.
  SECRET: "sticker-comms-2026",

  // How many stickers to show in the optional free-text block at the end.
  N_BONUS: 3,

  // Shown on the thank-you screen (e.g. a Duke email) so people can ask questions.
  CONTACT: "",
};
