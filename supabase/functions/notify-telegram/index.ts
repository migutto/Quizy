type WebhookPayload = {
  type?: string;
  table?: string;
  schema?: string;
  record?: Record<string, unknown> | null;
  old_record?: Record<string, unknown> | null;
};

const TELEGRAM_API = "https://api.telegram.org";

const MODULE_LABELS: Record<string, string> = {
  ekologia: "Ekologia",
  marketing: "Marketing",
  zywnosc: "Żywność roślinna",
};

const SCOPE_LABELS: Record<string, string> = {
  all: "Wszystkie pytania",
  gotowiec: "Gotowiec",
  links: "Pytania z linków",
  "E-Podstawy": "Podstawy ekologii",
  "E-Populacja": "Populacja",
  "E-Zaleznosci": "Zależności międzygatunkowe",
  "E-Ekosystem": "Ekosystem i troficzność",
  "E-Obiegi": "Obiegi biogeochemiczne",
  "E-Biomy": "Biomy i formacje",
  "E-Biosfera": "Biosfera i sfery Ziemi",
  "E-Ochrona": "Ochrona środowiska",
  "E-Zagrozenia": "Zagrożenia i katastrofy",
  "E-Zarzadzanie": "Zarządzanie środowiskowe",
};

function value(row: Record<string, unknown>, key: string): string {
  const v = row[key];
  if (v === null || v === undefined || v === "") return "-";
  return String(v);
}

function clean(row: Record<string, unknown>, key: string): string {
  const v = value(row, key);
  return v === "-" ? "" : v;
}

function label(map: Record<string, string>, raw: string): string {
  if (!raw) return "-";
  return map[raw] || raw;
}

function numberValue(row: Record<string, unknown>, key: string): number | null {
  const n = Number(row[key]);
  return Number.isFinite(n) ? n : null;
}

function percentLabel(row: Record<string, unknown>): string {
  const percent = numberValue(row, "percent");
  if (percent !== null) return `${percent}%`;

  const score = numberValue(row, "score");
  const total = numberValue(row, "total");
  if (score !== null && total !== null && total > 0) {
    return `${Math.round((score / total) * 100)}%`;
  }

  return "-";
}

function timeLabel(row: Record<string, unknown>): string {
  const raw = clean(row, "created_at");
  if (!raw) return "-";

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "short",
    timeStyle: "medium",
    timeZone: "Europe/Warsaw",
  }).format(date);
}

function sessionLengthLabel(row: Record<string, unknown>): string {
  const raw = value(row, "session_length");
  if (raw === "all") return "wszystkie pytania";
  if (raw === "-") return "-";
  return `${raw} pytań`;
}

function optionalLine(prefix: string, text: string): string[] {
  return text ? [`${prefix}: ${text}`] : [];
}

function formatQuizEvent(row: Record<string, unknown>): string {
  const nick = clean(row, "player_name");
  const moduleName = label(MODULE_LABELS, clean(row, "module"));
  const scopeName = label(SCOPE_LABELS, clean(row, "scope"));

  return [
    "🎉 Nowe ukończenie quizu",
    "",
    `📚 Moduł: ${moduleName}`,
    ...optionalLine("👤 Nick", nick),
    `🎯 Wynik: ${value(row, "score")}/${value(row, "total")} (${percentLabel(row)})`,
    `🧩 Zakres: ${scopeName}`,
    `📏 Długość: ${sessionLengthLabel(row)}`,
    `🕒 Czas: ${timeLabel(row)}`,
    `🔎 Sesja: ${value(row, "session_id")}`,
  ].join("\n");
}

function formatQuizScore(row: Record<string, unknown>): string {
  const moduleName = label(MODULE_LABELS, clean(row, "module"));
  const scopeName = label(SCOPE_LABELS, clean(row, "scope"));

  return [
    "🏆 Nowy wynik w rankingu",
    "",
    `👤 Gracz: ${value(row, "player_name")}`,
    `📚 Moduł: ${moduleName}`,
    `🎯 Wynik: ${value(row, "score")}/${value(row, "total")} (${percentLabel(row)})`,
    `🧩 Zakres: ${scopeName}`,
    `🔥 Najlepsza seria: ${value(row, "best_streak")}`,
    `🕒 Czas: ${timeLabel(row)}`,
  ].join("\n");
}

function buildMessage(payload: WebhookPayload): string | null {
  const row = payload.record;
  if (!row) return null;

  if (payload.table === "quiz_events") {
    if (row.event_type !== "quiz_complete") return null;
    return formatQuizEvent(row);
  }

  if (payload.table === "quiz_scores") {
    return formatQuizScore(row);
  }

  return null;
}

async function sendTelegramMessage(token: string, chatId: string, text: string) {
  const response = await fetch(`${TELEGRAM_API}/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      disable_notification: false,
    }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`Telegram sendMessage failed: ${response.status} ${JSON.stringify(data)}`);
  }

  return data;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }

  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const expectedSecret = Deno.env.get("QUIZ_NOTIFY_WEBHOOK_SECRET");
  const requestSecret = req.headers.get("x-webhook-secret");
  if (!expectedSecret) {
    return new Response("Missing QUIZ_NOTIFY_WEBHOOK_SECRET", { status: 500 });
  }
  if (!requestSecret || requestSecret !== expectedSecret) {
    return new Response("Unauthorized", { status: 401 });
  }

  const token = Deno.env.get("TELEGRAM_BOT_TOKEN");
  const chatId = Deno.env.get("TELEGRAM_CHAT_ID");
  if (!token || !chatId) {
    return new Response("Missing Telegram configuration", { status: 500 });
  }

  let payload: WebhookPayload;
  try {
    payload = await req.json();
  } catch (_err) {
    return new Response("Invalid JSON", { status: 400 });
  }

  const message = buildMessage(payload);
  if (!message) {
    return new Response("Ignored", { status: 204 });
  }

  try {
    await sendTelegramMessage(token, chatId, message);
    return Response.json({ ok: true });
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    return Response.json({ ok: false, error: detail }, { status: 502 });
  }
});
