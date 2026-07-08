# Telegram notifications for quiz completions

This Edge Function sends a Telegram message after a Supabase Database Webhook.
Do not put real secrets in this repository.

## 1. Create the Telegram bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Copy the bot token.
4. Send any message to your new bot.
5. Open this URL in a browser, replacing the token:

```text
https://api.telegram.org/botYOUR_TOKEN/getUpdates
```

6. Find `chat.id` in the JSON response. That is your `TELEGRAM_CHAT_ID`.

## 2. Set Supabase secrets

In Supabase Dashboard, open:

```text
Project Settings -> Edge Functions -> Secrets
```

Add:

```text
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
QUIZ_NOTIFY_WEBHOOK_SECRET=make-a-long-random-secret
```

## 3. Deploy the function

Using Supabase CLI:

```bash
supabase functions deploy notify-telegram
```

If you deploy from Dashboard, make sure JWT verification is disabled for this
function. This repository also includes `supabase/config.toml` with:

```toml
[functions.notify-telegram]
verify_jwt = false
```

The function still checks `x-webhook-secret`, so it is not open for casual use.

## 4. Create the database webhook

Use `supabase_telegram_notifications.sql` from the repository root.
Replace:

```text
<PROJECT_REF>
<QUIZ_NOTIFY_WEBHOOK_SECRET>
```

Then run it in Supabase SQL Editor.

The SQL file uses `pg_net`. If Supabase says the extension is unavailable,
enable `pg_net` in:

```text
Database -> Extensions
```

Then run the SQL again.

The recommended trigger uses `quiz_events` and sends a message for every
`quiz_complete`. If you prefer only leaderboard entries with nicknames, use the
optional `quiz_scores` trigger from the same SQL file instead.

## 5. Optional details in Telegram messages

If you want Telegram messages to include `module` and `player_name`, run this
SQL file in Supabase SQL Editor:

```text
supabase_migration_quiz_event_details.sql
```

Then redeploy this Edge Function and publish the updated `index.html`.
The nick is included when the player enters it before the quiz is completed.
