-- ============================================================================
-- ETAP 3 — rzetelność rankingu: indeks pod filtr min. długości sesji + pozycję gracza
-- Wklej całość w Supabase → SQL Editor → Run. Idempotentne (można uruchomić ponownie).
--
-- OPCJONALNE: aplikacja działa poprawnie bez tej migracji (filtr total>=20 i liczenie
-- pozycji gracza robi front). Ten indeks tylko przyspiesza zapytania przy większym rankingu.
-- ============================================================================

-- Indeks pod: filtr module + total>=20 oraz sort/porównania percent, score.
-- Pokrywa zapytania: top 10 (module, total>=20, sort percent/score) oraz
-- "Twoja pozycja" (count wierszy lepszych od najlepszego wyniku gracza).
create index if not exists quiz_scores_module_total_rank_idx
  on public.quiz_scores (module, total, percent desc, score desc);
