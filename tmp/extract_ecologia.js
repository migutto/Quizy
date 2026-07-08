const fs = require("fs");

const html = fs.readFileSync("index.html", "utf8");
const marker = "buildBankEkologia(){";
const start = html.indexOf(marker);

if (start < 0) {
  throw new Error("buildBankEkologia() not found");
}

const bodyStart = start + marker.length;
let depth = 1;
let end = bodyStart;

for (; end < html.length; end += 1) {
  const ch = html[end];
  if (ch === "{") depth += 1;
  if (ch === "}") {
    depth -= 1;
    if (depth === 0) break;
  }
}

if (depth !== 0) {
  throw new Error("Could not find end of buildBankEkologia()");
}

const body = html.slice(bodyStart, end);
const buildBankEkologia = new Function(body);
const questions = buildBankEkologia();

questions.forEach((q, idx) => {
  q._idx = idx;
});

fs.writeFileSync("tmp/ecologia_questions.json", JSON.stringify(questions, null, 2), "utf8");
console.log(`Extracted ${questions.length} ecology questions`);
