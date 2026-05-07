# Lovkode.no — Law Firm Outreach Batch 2026-05-07

**Mål:** Løse opp i stoppet salgspipeline for lovkode.no ved å levere ferdige, personlige e-postutkast til 8 norske advokatfirmaer i Oslo.

**Bakgrunn:**
- NOK 15 000 AI-workflow-sprint-tilbud er klart. Calendly er live.
- Alle 8 kontakter har status «Ingen tidligere kontakt» i CRM.
- RSM-utkastet (PER-100) var savnet; det er gjenopprettet her.
- Paperclip-API er midlertidig utilgjengelig, så denne batchen leveres som repo-assets.

**Kontakter denne omgang:**

| # | Firma | Kontakt | Tier | Ansatt | E-post | Status |
|---|-------|---------|------|--------|--------|--------|
| 1 | Advokat Hessen | Anita Hessen | A | 1–5 | anita@advokathessen.no | Utkast ferdig |
| 2 | Langseth Advokatfirma DA | — | A | 16 | post@ladv.no | Utkast ferdig |
| 3 | RSM Advokatfirma AS | — | A | 15 | firmapost@rsmnorge.no | Utkast ferdig (gjenopprettet) |
| 4 | Advokatfirma Nohlin | Olle Nohlin | B | Solo | olle_nohlin@hotmail.com | Utkast ferdig |
| 5 | Advokatfirma Philipson | Bjørn Philipson | B | Solo | bjorn@philipson.no | Utkast ferdig |
| 6 | Advokatfirma Reiersen | — | B | Solo | post@advokatreiersen.no | Utkast ferdig |
| 7 | Advokatfirma Orlin | Johan Orlin | B | Solo | johan.orlin@hotmail.com | **Prioritet** — utkast ferdig |

**Mangler før utsendelse:**
1. Sett inn faktisk Calendly-lenke i alle 7 utkast.
2. Legg til ola@lovkode.no som avsender i e-postklient (hvis ikke allerede konfigurert).
3. Send batch 1 (tier-A: Hessen, Langseth, RSM) og batch 2 (tier-B: Nohlin, Philipson, Reiersen, Orlin) med 48-timers mellomrom.
4. Logg sending i `interactions.csv` med type `outreach` og oppfølging i reconnect_items.

**Neste steg etter utsendelse:**
- Følg opp ubesvarte e-poster etter 5 virkedager.
- Logg svar og interesse i CRM.
- Oppdater digest med pipeline-status.
