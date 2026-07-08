# Audyt modułu Ekologia
## Zakres
- Pytania z `index.html`: 280.
- Źródła PDF:
  - `egz eko (1).pdf`: 20 stron
  - `EZS-NS-W1-W2.pdf`: 72 stron
  - `EZS-NS-W3-W4.pdf`: 89 stron
  - `EZS-NS-W5-W6.pdf`: 114 stron
  - `EZS-NS-W7.pdf`: 46 stron

## Statystyki banku
- Typy pytań: {'single': 222, 'tf': 8, 'multi': 50}
- Trudność: {1: 26, 2: 122, 3: 132}
- Kategorie:
  - `E-Biomy`: 14
  - `E-Biosfera`: 7
  - `E-Ekosystem`: 37
  - `E-Obiegi`: 34
  - `E-Ochrona`: 38
  - `E-Podstawy`: 33
  - `E-Populacja`: 29
  - `E-Zagrozenia`: 20
  - `E-Zaleznosci`: 36
  - `E-Zarzadzanie`: 32

## Kontrola odpowiedzi i biasów
- Prawidłowa liczba odpowiedzi: problemów formalnych 0.
- Prawda/Fałsz: 8 pytań, poprawne etykiety {'falsz': 2, 'prawda': 6}, pierwsza opcja poprawna w 6 przypadkach (75.0%).
- Single w źródle: rozkład pozycji poprawnej odpowiedzi {1: 222}. W praktyce aplikacja losuje single/multi, ale przy wyłączonym `shuffleAnswers` wszystkie single miałyby poprawną odpowiedź jako A.
- Single: poprawna odpowiedź jest najdłuższa w 27 z 222 pytań (12.2%). Średnia długość poprawnej: 39.1 znaków, błędnej: 31.9 znaków.
- Multi: poprawne odpowiedzi są zapisane przed błędnymi w 50 z 50 pytań (100.0%). W runtime single/multi są losowane, TF nie są losowane.

### Najbardziej podejrzane długie poprawne odpowiedzi single
- L1409, ratio 5.0: Konsumentami III rzędu są: -> Organizmy odżywiające się mięsożernymi konsumentami II rzędu
- L1427, ratio 2.16: Poziom troficzny producentów w łańcuchu pokarmowym stanowią: -> Organizmy autotroficzne
- L1444, ratio 1.66: Recykling materiałowy polega na: -> Ponownym przetwarzaniu odpadów w produkt o wartości użytkowej
- L1446, ratio 2.19: Dlaczego biochemiczne zapotrzebowanie na tlen oznacza się w ciągu 5 dni (BZT5)? -> Bo szybkość biologicznego utleniania jest największa w początkowych 5 dniach
- L1448, ratio 1.5: Skrót RLM (równoważna liczba mieszkańców) opiera się na założeniu, że: -> 1 mieszkaniec wytwarza ładunek odpowiadający 60 g BZT5 na dobę
- L1450, ratio 3.59: Roztwór zerowy (ślepa próba) to: -> Próba wykonana z tymi samymi odczynnikami, ale bez oznaczanego składnika — uwzględnia wpływ odczynników
- L1451, ratio 2.16: Jakie powinno być stężenie tlenu rozpuszczonego w wodzie do picia? -> Bliskie 100% stanu nasycenia w danej temperaturze
- L1593, ratio 2.93: Hałas o częstotliwości drgań niższej niż 20 Hz to hałas: -> Infradźwiękowy (niesłyszalny, ale odczuwalny)

## Duplikaty i podobieństwa
- Dokładne duplikaty pytań: 0.
- Silnie podobne pary (>=0.86): 11 pokazanych w JSON.
- 0.981: L1470 `Krzywa przeżywania typu A jest charakterystyczna dla:` / L1471 `Krzywa przeżywania typu C jest charakterystyczna dla:`
- 0.957: L1443 `Do biomów słodkowodnych zalicza się:` / L1535 `Do biomów słonowodnych zalicza się:`
- 0.954: L1386 `Komensalizm to zależność, w której:` / L1389 `Amensalizm to zależność, w której:`
- 0.921: L1384 `Mutualizm to zależność, w której:` / L1391 `Neutralizm to zależność, w której:`
- 0.892: L1443 `Do biomów słodkowodnych zalicza się:` / L1523 `Do biomów lądowych zalicza się:`
- 0.889: L1384 `Mutualizm to zależność, w której:` / L1389 `Amensalizm to zależność, w której:`
- 0.875: L1384 `Mutualizm to zależność, w której:` / L1386 `Komensalizm to zależność, w której:`
- 0.875: L1389 `Amensalizm to zależność, w której:` / L1391 `Neutralizm to zależność, w której:`
- 0.875: L1523 `Do biomów lądowych zalicza się:` / L1535 `Do biomów słonowodnych zalicza się:`
- 0.869: L1621 `Funkcja bodźcowa (stymulacyjna) instrumentów ekonomicznych polega na:` / L1622 `Funkcja regulacyjna instrumentów ekonomicznych polega na:`
- 0.862: L1386 `Komensalizm to zależność, w której:` / L1391 `Neutralizm to zależność, w której:`

## Dopasowanie do źródeł PDF
- Najlepsze źródło według dopasowania tokenów: {'egz eko (1).pdf': 66, 'EZS-NS-W1-W2.pdf': 78, 'EZS-NS-W3-W4.pdf': 57, 'EZS-NS-W5-W6.pdf': 47, 'EZS-NS-W7.pdf': 32}.
- Mocne dopasowanie >=0.36: 267; słabe 0.16-0.24: 1; bardzo słabe <0.16: 0.
- Przykłady bardzo słabo podpartych automatycznie, do ręcznej kontroli:

## Ręczne wnioski merytoryczne
- Nie znalazłem twardych błędów formalnych odpowiedzi względem podanych PDF-ów: każde pytanie ma właściwą liczbę odpowiedzi poprawnych, a automatyczne dopasowanie wskazuje źródło dla wszystkich 280 pytań.
- Kilka pytań jest poprawnych względem wykładu, ale może być nieaktualnych lub zbyt absolutnych, jeżeli quiz ma sprawdzać aktualną wiedzę, a nie materiał z PDF-ów: CO2 ok. 0,035%, energetyka jądrowa 16% energii świata i zerowa emisja CO2, bilans CO2 biomasy równy zero, oraz nazwy organów/nadzoru w części KOBiZE.
- Pytanie o CO2 w atmosferze (`L1517`) jest zgodne ze slajdem W3-W4, ale warto oznaczyć je jako historyczne/wykładowe albo zaktualizować do współczesnego poziomu.
- Pytanie o energetykę jądrową (`L1547`) jest zgodne ze slajdem W3-W4, ale lepiej doprecyzować jako `ok. 16% według wykładu / dawnych danych` albo zmienić pytanie na jakościowe: `energetyka jądrowa ma bardzo niską emisję operacyjną CO2`.
- Pytanie o biomasę (`L1545`) jest zgodne ze slajdem, lecz `bilans CO2 = zero` jest uproszczeniem. Bezpieczniejsze brzmienie: `w uproszczonym bilansie obiegu krótkiego węgla`.
- Pary podobnych pytań w większości są dydaktycznie uzasadnione: porównują typy zależności, krzywe przeżywania albo typy biomów. Nie są duplikatami, ale zwiększają pamięciowy charakter banku.

## Rekomendacje
1. Dodać 6-10 pytań TF z poprawną odpowiedzią `Fałsz`, albo losować kolejność `Prawda/Fałsz`, bo teraz strategia `wybieraj Prawdę` daje 75% trafień.
2. W single skrócić lub wyrównać 8 wskazanych odpowiedzi, gdzie poprawna jest wyraźnie dłuższa od dystraktorów.
3. Utrzymać losowanie odpowiedzi jako obowiązkowe dla single/multi; przy wyłączeniu losowania wszystkie single mają poprawne A, a wszystkie multi mają poprawne odpowiedzi zgrupowane przed błędnymi.
4. Zdecydować, czy quiz ma być `egzamin z tych PDF-ów`, czy `aktualna ekologia i prawo środowiskowe`. Dla wersji aktualnej trzeba zrewidować liczby i nazwy instytucji.
