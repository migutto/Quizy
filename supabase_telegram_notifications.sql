-- ============================================================================
-- Telegram notifications for completed quizzes.
--
-- Safe to keep in the repository because it contains placeholders only.
-- Before running in Supabase SQL Editor, replace:
--   <PROJECT_REF> with your Supabase project ref
--   <QUIZ_NOTIFY_WEBHOOK_SECRET> with the same secret set in Edge Function env
--
-- Recommended: notify on every completed quiz via public.quiz_events.
-- Optional: notify only when a leaderboard score is inserted via public.quiz_scores.
--
-- This version uses the pg_net extension directly. It is useful when the
-- Supabase Dashboard helper schema `supabase_functions` is not available.
-- ============================================================================

create extension if not exists pg_net with schema extensions;

create schema if not exists private;
revoke all on schema private from public;

create or replace function private.quiz_notify_telegram_webhook()
returns trigger
language plpgsql
security definer
set search_path = public, net, extensions
as $$
begin
  perform net.http_post(
    url := 'https://<PROJECT_REF>.supabase.co/functions/v1/notify-telegram',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-webhook-secret', '<QUIZ_NOTIFY_WEBHOOK_SECRET>'
    ),
    body := jsonb_build_object(
      'type', TG_OP,
      'table', TG_TABLE_NAME,
      'schema', TG_TABLE_SCHEMA,
      'record', to_jsonb(new),
      'old_record', null
    ),
    timeout_milliseconds := 1000
  );

  return new;
end;
$$;

revoke all on function private.quiz_notify_telegram_webhook() from public;

-- Every completed quiz. This also works when the player did not enter a nick.
drop trigger if exists quiz_notify_telegram_on_complete on public.quiz_events;

create trigger quiz_notify_telegram_on_complete
after insert on public.quiz_events
for each row
when (new.event_type = 'quiz_complete')
execute function private.quiz_notify_telegram_webhook();

-- Optional alternative: only leaderboard scores.
-- This includes player_name and module, but fires only if the user entered a nick
-- and the session qualifies for the ranking.
--
-- drop trigger if exists quiz_notify_telegram_on_score on public.quiz_scores;
--
-- create trigger quiz_notify_telegram_on_score
-- after insert on public.quiz_scores
-- for each row
-- execute function private.quiz_notify_telegram_webhook();
