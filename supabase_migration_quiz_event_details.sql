-- ============================================================================
-- Adds optional module and player_name details to quiz_events.
-- Run this once in Supabase SQL Editor before deploying the updated frontend.
-- ============================================================================

alter table public.quiz_events
  add column if not exists module text,
  add column if not exists player_name text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'quiz_events_module_len'
      and conrelid = 'public.quiz_events'::regclass
  ) then
    alter table public.quiz_events
      add constraint quiz_events_module_len
      check (module is null or char_length(module) between 1 and 40);
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'quiz_events_player_name_len'
      and conrelid = 'public.quiz_events'::regclass
  ) then
    alter table public.quiz_events
      add constraint quiz_events_player_name_len
      check (player_name is null or char_length(player_name) between 1 and 40);
  end if;
end
$$;
