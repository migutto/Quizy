-- ============================================================================
-- ETAP 2 — podział na moduły (marketing / żywność roślinna) + wyczyszczenie rankingu
-- Wklej całość w Supabase → SQL Editor → Run.
-- ============================================================================

-- 1) Nowa kolumna modułu. Domyślnie 'marketing', aby ewentualne stare wiersze
--    trafiły do modułu marketingowego. Idempotentne (if not exists).
alter table public.quiz_scores
  add column if not exists module text not null default 'marketing';

-- 2) Indeks pod ranking per-moduł (moduł + dokładnie taki sort jak robi front)
create index if not exists quiz_scores_module_rank_idx
  on public.quiz_scores (module, percent desc, score desc, created_at asc);

-- 3) Wyczyść ranking do zera (pusta tabela, świeży start dla obu modułów)
truncate table public.quiz_scores;
