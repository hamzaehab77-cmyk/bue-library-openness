/**
 * BUE library reading task – Google Apps Script back end.
 * Paste into Extensions > Apps Script of the response spreadsheet (file name: Code.gs).
 * The page itself goes in an HTML file named "index".
 */
const SHEET_ID = '1M2smZMlEVz3xZ1tjvzytVw_WRcW4K48dzbOUGwNUAxE'; // "BUE reading task - responses"
const SHEET_NAME = 'Responses';
const KEY = ['C','A','D','B','D','A','C','B','D','A','B','C','D','B','A','C','D','A','C','B']; // task v2 (14 Nov 2026)
const AREAS = { A: 32, B: 24, C: 20, D: 28, E: 48 };   // standard layout, 152 seats (17 Nov 2026)

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('Study Spaces in the BUE Library')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// Text typed by participants is stored as plain text, never as a formula.
function clean_(v, max) {
  let s = String(v == null ? '' : v).slice(0, max || 2000);
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  return s;
}

const Q_COL = 9;            // column I = Q1
const WRONG = '#ffff00';    // yellow = wrong answer (blank = not attempted, left white)

// Header for each answer column, with the correct letter: "Q1 (C)".
function qHeaders_() { return KEY.map(function (k, i) { return 'Q' + (i + 1) + ' (' + k + ')'; }); }

function wrongColours_(ans) { return ans.map(function (a, i) { return a && a !== KEY[i] ? WRONG : null; }); }

// Run once by hand from the editor: puts the key in the header and colours wrong answers in the rows
// already in the sheet. Rows marked with the old (v1) key are left alone: a row is coloured only if its
// stored "Correct" count matches the current key.
function formatSheet() {
  const sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
  sh.getRange(1, Q_COL, 1, KEY.length).setValues([qHeaders_()]);
  const n = sh.getLastRow() - 1;
  if (n < 1) return 'no rows';
  const vals = sh.getRange(2, Q_COL, n, KEY.length + 2).getValues();
  const done = [];
  vals.forEach(function (row, j) {
    const ans = row.slice(0, KEY.length).map(String);
    const correct = ans.filter(function (a, i) { return a === KEY[i]; }).length;
    if (correct === Number(row[KEY.length + 1])) {
      sh.getRange(j + 2, Q_COL, 1, KEY.length).setBackgrounds([wrongColours_(ans)]);
      done.push(j + 2);
    }
  });
  Logger.log('Coloured rows: ' + done.join(', '));
  return done;
}

function saveResponse(r) {
  const area = String(r.area || '');
  const seatNo = parseInt(String(r.seat || '').split('-')[1], 10);
  if (!AREAS[area] || !(seatNo >= 1 && seatNo <= AREAS[area])) throw new Error('Invalid seat code');
  if (!Array.isArray(r.answers) || r.answers.length !== KEY.length) throw new Error('Invalid answers');

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
    if (sh.getLastRow() === 0) {
      sh.appendRow(['Received', 'Response code', 'Seat code', 'Area', 'Task start', 'Task end', 'Task time (s)', 'Ended by']
        .concat(qHeaders_())
        .concat(['Attempted (quantity)', 'Correct', 'Quality (proportion correct)', 'Open Q1', 'Open Q2', 'GPA band', 'Seat reason', 'Seat reason (other)', 'Consent', 'Format']));
      sh.setFrozenRows(1);
    }
    // A repeated Submit (automatic retry) must not add a second row for the same response code.
    const code = clean_(r.code, 12);
    if (sh.getLastRow() > 1) {
      const codes = sh.getRange(2, 2, sh.getLastRow() - 1, 1).getValues();
      for (let i = 0; i < codes.length; i++) { if (String(codes[i][0]) === code) return true; }
    }
    let attempted = 0, correct = 0;
    const ans = KEY.map(function (k, i) {
      const a = /^[ABCD]$/.test(r.answers[i]) ? r.answers[i] : '';
      if (a) { attempted++; if (a === k) correct++; }
      return a;
    });
    const start = new Date(Number(r.start)), end = new Date(Number(r.end));
    const seconds = Math.round((end - start) / 100) / 10;
    sh.appendRow([new Date(), code, area + '-' + seatNo, area, start, end, seconds, clean_(r.endedBy, 20)]
      .concat(ans)
      .concat([attempted, correct, attempted ? correct / attempted : '', clean_(r.open1), clean_(r.open2),
               clean_(r.gpa, 60), clean_(r.reason, 120), clean_(r.reasonOther, 300), clean_(r.consent, 5), 'Online']));
    sh.getRange(sh.getLastRow(), Q_COL, 1, KEY.length).setBackgrounds([wrongColours_(ans)]);
    return true;
  } finally {
    lock.releaseLock();
  }
}
