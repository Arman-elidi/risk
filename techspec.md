TECHNICAL SPECIFICATION
AI Risk Orchestrator Agent with Portfolio System
Version: 2.7 (CySEC IFR / Full Regulatory)
Date: December 2025
Classification: Internal – Risk Management

0. Passport & Executive Summary
0.1. Document Passport

Name: Technical Specification – AI Risk Orchestrator Agent with Portfolio System

Version: 2.7 (Production‑Ready, Full Regulatory)

Author: A.___

Date: December 2025

Classification: Internal – Risk Management

0.2. Executive Summary

AI Risk Orchestrator — централизованная risk‑платформа для Cyprus Investment Firm (CIF, Class 2), работающей под IFR/IFD и надзором CySEC. Система автоматизирует ежедневный мониторинг рыночного, кредитного, контрагентского, ликвидностного риска, K‑факторов и капитала, а также формирует отчёты для руководства и регулятора.​

Покрытие:

Bond Dealer Book — рыночный, кредитный и ликвидностный риск по облигациям.

Derivatives Portfolio — FX/IR деривативы (включая high‑volume клиентов).

Credit & Counterparty Risk — PD/LGD/EAD/EL, CCR, PFE, CVA.

Liquidity Risk — LCR, funding gaps, liquidation costs.​

Capital Adequacy — K‑factors (K‑NPR, K‑AUM, K‑CMH, K‑COH) и Capital Ratio в логике IFR.​

Stress Testing — IR/credit/FX/vol/liquidity сценарии.

Backtesting — VaR backtesting с Basel‑подходом (traffic light).​

Data Quality — матрица DQ‑правил и workflow.

Integration — Bloomberg/Refinitiv, back‑office, ERP, Treasury, HR, XBRL (COREP/FINREP).​

DR/BCP и Change Management — соответствие ожиданиям CySEC по ICT и model governance.​

Режимы:

Nightly batch: полный пересчёт всех портфелей ≤ 5 минут.

On‑demand API: расчёт по запросу ≤ 3 секунд при кешировании/параллелизме.

Outputs: PDF‑отчёты для Risk/Board, web‑дашборд, XBRL файлы для CySEC.

1. Business Scope & Instruments
1.1. Instruments (MVP)

Bonds:

Government / Sovereign.

Supranational / quasi‑sovereign.

Corporate (Investment Grade / High Yield).

FX Derivatives:

FX forwards.

Vanilla FX options (EURUSD, majors, EM FX).

IR Derivatives:

Interest rate swaps.

Caps/Floors.

European swaptions (plain vanilla).

1.2. Risk Types (Quantitative)

Market risk:

Historical VaR (1d, 95%, 250d).

Stressed VaR (фиксированное стресс‑окно).

DV01, modified duration, Macaulay duration, convexity, spread duration.

Credit risk:

PD, LGD, EAD, EL.

Counterparty credit risk (CCR):

Current Exposure (CE).

PFE (Enhanced Add‑On Method).

EAD_CCR.

CVA.

Liquidity risk:

LCR (Liquidity Coverage Ratio).

Funding gaps (7d/30d).

Liquidation costs.

Concentration risk:

Issuer/country/sector/counterparty.

Capital adequacy:

K‑NPR, K‑AUM, K‑CMH, K‑COH, Total K‑Requirement, Capital Ratio.​

1.3. Out of Scope (Phase 2+)

Exotic derivatives, full SA‑CCR.​

Monte Carlo VaR / ES.

Internal ratings (IRB).

Real‑time streaming pricing, ML‑модели спредов.

1.4. Constraints

Universe:

≤10 000 позиций.

≤250 эмитентов.

≤50 контрагентов.

Jurisdiction: Cyprus‑based CIF (Class 2).

Reporting currency: USD.

Calendar: стандартный trading calendar (совместимый с Bloomberg).

2. Risk Types & Regulatory Context
Система ориентирована на требования IFR/IFD, CySEC практических гайдов и базельских стандартов по LCR, VaR и CVA.​

Покрываемые риски:

Market Risk (VaR, DV01, duration, convexity, Greeks, stress).

Credit Risk и CCR (PD/LGD/EAD, EL, PFE/EAD_CCR, CVA).​

Liquidity Risk (LCR, funding gap, liquidation cost).​

Concentration Risk (issuer/country/sector/counterparty).

Capital Adequacy Risk (K‑factors, capital ratio, buffer).

Частично/качественно:

Operational, Legal, Compliance, Custody, Business/Strategic, Reputational, Systemic/Macro — через отчётность и дашборды.​

Model Risk — через backtesting, validation, change management.

3. Architecture & Data Model
3.1. High‑Level Architecture

Слои:

Presentation:

React+TS Dashboard (Plotly/Chart.js).

PDF‑отчёты (WeasyPrint/ReportLab или аналог).

Alert UI (email/SMS/push).

API Gateway:

FastAPI, JWT auth, RBAC, rate limiting, /api/v1.

Business Logic:

Risk Engine (bonds, derivatives, liquidity, capital, stress, CVA, K‑factors).

Alert Engine (rules, thresholds, escalation).

AI Layer (Dify или аналог) — summaries и пояснения.

Data Access:

SQLAlchemy ORM (async).

Storage:

PostgreSQL:

portfolios, positions, counterparties, reference_data, market_data_snapshots.

yield_curves, vol_surfaces, limits, alerts, risk_snapshots.

var_backtesting, data_quality_issues, stress_test_results, audit_log, model_governance, news_events.

Redis:

кеширование кривых, vol surfaces, сценариев, последних risk_snapshots.

Object storage (S3):

PDF‑отчёты, XBRL, архивы.

Integrations:

Bloomberg, Refinitiv.​

Back‑office (positions, trades, balances).

ERP, Treasury, HR.

CySEC XBRL upload.

Infrastructure:

Docker/Kubernetes (multi‑AZ).

CI/CD (GitLab/Jenkins).

Monitoring: Prometheus + Grafana, ELK.

Secrets: Vault/KMS.

3.2. Key Tables (Logical)

portfolios:

id, name, type (BOND_DEALER / DERIVATIVES_CLIENT / PROPRIETARY), base_currency, status.

positions:

portfolio_id, instrument_id, ISIN, ticker, type, quantity/notional, direction, trade_date, maturity_date, coupon, coupon_freq, day_count, underlying, strike, option_type, exercise_type.

counterparties:

id, name, type, country, external_rating, internal_rating, limits, CSA/ISDA flags.

reference_data:

issuer_id, issuer_name, country, sector, ratings, issue_size, seniority.

market_data_snapshots:

as_of_date, instrument_id, clean_price, yield, spread_bps, bid/ask, bid_ask_spread_bps, volume, days_since_trade, liquidity_score, fx_rates, cds_spread.

yield_curves, vol_surfaces:

curve_id, currency, tenors, rates; vol_surface by underlying/tenor/strike.

risk_snapshots:

portfolio_id, as_of_date, mv_total, dv01_total, duration, convexity, var_1d_95, stressed_var, credit_EL, CCR_EAD, CVA_total, LCR, K_NPR, K_AUM, K_CMH, K_COH, K_total, capital_ratio, engine_version, market_data_snapshot_id.

alerts:

id, type, severity, metric, current_value, limit_value, status, created_at, resolved_at.

var_backtesting:

date, portfolio_id, var_forecast, pnl_actual, is_exception.

data_quality_issues:

issue_id, type, severity, source, instrument_id, snapshot_id, created_at, resolved_at.

stress_test_results:

scenario_id, portfolio_id, date, pnl, delta_var, delta_greeks, delta_capital, lcr_impact, top_contributors.

model_governance:

model_id, version, change_description, approver, approval_date, parallel_run_period, validation_summary.

news_events:

id, source, datetime, entity_type (issuer/country/counterparty), entity_id, event_type, sentiment, importance, url, raw_payload.

4. Bond Risk & Metrics
4.1. Pricing & Yields

Price = сумма дисконтированных cashflow при annual compounding.

CF_t = coupon × nominal или coupon + principal при погашении.

Discount factor: 
D
F
t
=
1
(
1
+
y
)
t
DF 
t
 = 
(1+y) 
t
 
1
 , где y — YTM.

4.2. Duration & Convexity

Macaulay duration:

D
m
a
c
=
∑
t
t
⋅
C
F
t
(
1
+
y
)
t
∑
t
C
F
t
(
1
+
y
)
t
D 
mac
 = 
∑ 
t
  
(1+y) 
t
 
CF 
t
 
 
∑ 
t
 t⋅ 
(1+y) 
t
 
CF 
t
 
 
 
Modified duration:

D
m
o
d
=
D
m
a
c
1
+
y
D 
mod
 = 
1+y
D 
mac
 
 
DV01:

D
V
01
=
D
m
o
d
×
M
V
×
0.0001
DV01=D 
mod
 ×MV×0.0001
Convexity (стандартная формула по дисконтированным cashflow).​

4.3. Portfolio Metrics

MV_total = Σ MV_i.

Portfolio modified duration:

D
m
o
d
,
p
o
r
t
=
∑
i
D
m
o
d
,
i
×
M
V
i
M
V
t
o
t
a
l
D 
mod,port
 = 
MV 
total
 
∑ 
i
 D 
mod,i
 ×MV 
i
 
 
Portfolio DV01:

D
V
01
p
o
r
t
=
∑
i
D
V
01
i
DV01 
port
 = 
i
∑
 DV01 
i
 
Spread duration и другие производные показатели — аналогично на основе spread‑shifts.

5. VaR (Historical & Stressed)
5.1. Historical VaR 1d, 95%

Input: 250 дневных P&L портфеля (rolling).​

Алгоритм:

Отсортировать P&L по возрастанию.

N = 250; index = floor(0.05 × N).

VaR_1d_95 = |P&L_sorted[index]|.

5.2. Stressed VaR

Используется тот же алгоритм, но данные берутся из фиксированного стресс‑периода (например, 2008/2020).​

Stressed_VaR в risk_snapshots хранится отдельно.

6. Credit Risk (PD/LGD/EAD/EL)
6.1. Основные формулы

PD: по рейтингу/таблицам (внешние источники / внутренние шкалы).​

LGD: по типу инструмента (senior/subordinated, collateral).

EAD: позиция по эмитенту/контрагенту (номинал × цена или EAD_CCR для деривативов).

Expected Loss:

E
L
=
P
D
×
L
G
D
×
E
A
D
EL=PD×LGD×EAD
7. CCR, PFE, EAD_CCR, CVA
7.1. Base CCR

Current Exposure (CE):

C
E
=
max
⁡
(
M
t
M
,
0
)
CE=max(MtM,0)
7.2. PFE (Enhanced Add‑On Method)

7.2.1. FX Derivatives

Формула:

PFE_addon = Notional × CCF × √(T/250) × Vol_multiplier.

CCF:

FX Majors: 1.0%.

EM FX: 2.5%.

Vol_multiplier:

Normal: 1.0.

Elevated (VIX > 20): 1.3.

Crisis (VIX > 30): 1.5.​

7.2.2. IR Derivatives

PFE_addon = Notional × CCF × √(T/250) × Vol_multiplier.

CCF:

0–1Y: 0.0%.

1–5Y: 0.5%.

5–10Y: 1.0%.

10Y: 1.5%.

Vol_multiplier:

Normal: 1.0.

Elevated rate vol: 1.2.

7.2.3. Options

Long options: PFE = min(premium_paid, cap_policy).

Short options: PFE = delta_adjusted_notional × CCF.

7.2.4. Netting & Collateral

Net_PFE (при ISDA netting):

Net_PFE = √(Σ PFE_i²) × 0.6.

Adjusted_PFE (с учётом CSA):

Adjusted_PFE = max(0, Net_PFE − Collateral_held + Threshold).

7.2.5. Portfolio Adjustment

Если trades_per_counterparty > 10:

Portfolio_PFE = Σ PFE_i × Portfolio_factor.

Portfolio_factor:

Same direction: 0.8.

Mixed: 1.0.

Hedged (net delta ≈ 0): 0.5.

7.3. EAD_CCR

EAD_CCR = CE + Adjusted_PFE.

7.4. CVA (Simplified Regulatory Method)

7.4.1. Общая формула

CVA = LGD × Σ(PD_t × DF_t × EAD_t).​

LGD = 1 − Recovery_Rate (typically 40%).

Buckets t: [0.25Y, 0.5Y, 1Y, 2Y, 3Y, 5Y] до max maturity.

EAD_t = CE_current + PFE_t (PFE растёт как √t).

PD_t:

если есть CDS: PD_t = 1 − exp(−CDS_spread × t / LGD);

если нет: rating‑based PD (табличные значения).

DF_t = exp(−r_riskfree × t).

7.4.2. Aggregation

CVA_counterparty = Σ_t (LGD × PD_t × DF_t × EAD_t).

CVA_total = Σ по всем counterparties.

7.4.3. Capital Interaction

В простом варианте K_CVA ≈ CCR capital requirement или выделяется в составе K‑NPR (в зависимости от регуляторной интерпретации).​

8. Liquidity & LCR
8.1. LCR (High‑Level)

Формула:

L
C
R
=
H
Q
L
A
N
e
t
 
C
a
s
h
 
O
u
t
f
l
o
w
s
30
d
≥
100
%
LCR= 
Net Cash Outflows 
30d
 
HQLA
 ≥100%
8.2. HQLA (Detailed)

Категории:

Level 1 (100% без лимита): cash, central bank reserves, высококачественные gov bonds.​

Level 2A (haircut 15%, лимит 40% HQLA).

Level 2B (haircut 25–50%, лимит 15% HQLA).​

Упрощённый расчёт:

HQLA = Level1 × 1.0 + Level2A_adj + Level2B_adj.

8.3. Cash Outflows 30d

Retail deposits: 3–10%.

Unsecured wholesale funding: 5–40%.

Secured funding: 0–100% в зависимости от коллатерала.

Derivatives: ожидаемые margin calls / collateral postings.

Committed facilities, debt maturities: 30–100%.

Total_Outflows_30d = Σ(amount × run_off_rate).

8.4. Cash Inflows 30d

Gross_Inflows = Σ(amount × inflow_rate).

Capped_Inflows = min(Gross_Inflows, 0.75 × Total_Outflows_30d).

8.5. Net Cash Outflows

Net_Cash_Outflows_30d = Total_Outflows_30d − Capped_Inflows.

LCR = HQLA / Net_Cash_Outflows_30d.

8.6. Alerts

LCR < 110% → YELLOW.

LCR < 105% → RED.

LCR < 100% → CRITICAL (регуляторный breach).​

9. K‑Factors (IFR/IFD, CySEC)
9.1. Overview

K‑факторы для CIF Class 2 по IFR/IFD и CySEC практическим гайдам: K‑NPR, K‑AUM, K‑CMH, K‑COH.​

9.2. K‑NPR (Net Position Risk)

Два подхода:

VaR‑based (при разрешении):

K‑NPR = max(VaR_t, VaR_60d_avg) × multiplier, где multiplier зависит от backtesting‑результата (см. 11.1).​

Standardised (по умолчанию):

K‑NPR = √(K‑IR² + K‑FX² + K‑EQ² + K‑COM² + K‑CREDNR²).

Для текущего портфеля основное внимание: K‑IR, K‑FX, K‑CREDNR.

K‑IR:

Нетто‑позиции по maturity buckets.

Risk weights: 0.7–2.0% в зависимости от срока.

K‑IR = Σ(|net_bucket| × risk_weight).

K‑CREDNR:

По рейтингу:

AAA–AA: 0.5%, A: 1.0%, BBB: 2.0%, BB: 4.0%, B и ниже: 8.0%.

K‑CREDNR = Σ(MV_i × credit_risk_weight).

K‑FX:

K‑FX = 8% × max(Σ net_long, |Σ net_short|) по каждой non‑base currency.​

Упрощённо для MVP:
K‑NPR ≈ K‑IR + K‑CREDNR + K‑FX (с явным сохранением компонент).

9.3. K‑AUM

K‑AUM = 0.02% × AUM_quarterly_average (discretionary/mandate).

Для текущей фирмы (broker‑dealer, без asset management): K‑AUM = 0.​

9.4. K‑CMH

K‑CMH = 0.4% × avg(segregated_client_funds).

При наличии гарантирования/страхования допускается снижение до 0.3% (по согласованию).​

9.5. K‑COH

Покрывает операционный риск, связанный с обработкой клиентских ордеров (RtC).

В практике IFR:

может выражаться как процент от annual volume of client orders;

значения и формула уточняются в соответствии с CySEC формами (см. COREP guidance).​

9.6. Total K‑Requirement & Capital

sum_K = K‑NPR + K‑AUM + K‑CMH + K‑COH.

Total_K_Requirement = max(K‑NPR, sum_K).​

Permanent_Min_Capital = 75,000 EUR (Class 2).

Required_Capital = max(Permanent_Min_Capital, Total_K_Requirement).

Own Funds:

Tier 1: share capital, retained earnings.

Tier 2: subordinated loans (≤25% Tier 1).

Total_Own_Funds = Tier1 + Tier2.

Capital Ratio:

Capital_Ratio = Total_Own_Funds / Required_Capital.

Regulatory минимум: 100%.

Internal target: 120–150%.

9.7. Alerts & Breaches

Capital_Ratio < 110% → YELLOW.

Capital_Ratio < 105% → RED.

Capital_Ratio < 100% → CRITICAL (регуляторный breach, уведомление CySEC).​

Увеличение любого K‑фактора >20% d/d → YELLOW.

50% d/d → RED.

9.8. Reporting to CySEC

Daily: internal monitoring.

Monthly/Quarterly: COREP/FINREP XBRL submission.​

При Capital_Ratio < 100%:

немедленное уведомление CySEC;

план восстановления капитала ≤3 business days;

еженедельные обновления до восстановления.

10. Derivatives Risk Framework
(High‑volume FX/IR clients)

Метрики:

Delta, Gamma, Vega, Theta, Rho per instrument/underlying/client.

Bucketed Greeks:

по strike (ITM/ATM/OTM).

по maturity (short/medium/long).

Cross‑Greek: delta‑vega, gamma‑vega.

Margin & Collateral:

Initial/Variation Margin, Margin Usage%, shortfall alerts.

CCR:

EAD_CCR, PFE, CVA per counterparty.

Stress:

FX/IR/vol/liquidity сценарии (см. 11).

Limits:

Greek limits per client/underlying; margin usage; CCR limits.

(Детализация — как ты уже описывал в v2.5; в этом документе оставляем как раздел с ссылкой на формулы CCR/PFE/CVA выше.)

11. Stress Testing Framework
11.1. Scenarios

A) Interest Rate Shocks

IR‑01: +200 bps parallel.

IR‑02: −100 bps parallel.

IR‑03: Steepening (short +50, long +150).

IR‑04: Flattening (short +150, long +50).

IR‑05: Twist (5Y pivot).

B) Credit Spread Shocks

CS‑01: +100 bps all corporates.

CS‑02: +200 bps HY (BB and below).

CS‑03: +50 bps IG (BBB and above).

CS‑04: +300 bps single‑name (top‑5 exposures).

C) FX Shocks

FX‑01: USD +10%.

FX‑02: USD −10%.

FX‑03: EUR/USD −15%.

FX‑04: EM FX crisis −25%.

D) Volatility Shocks

VOL‑01: vol ×1.2.

VOL‑02: vol ×1.4.

VOL‑03: smile flattening.

VOL‑04: skew shift.

E) Combined (Historical)

CRISIS‑2008, CRISIS‑2020, TAPER‑2013 — набор комбинированных IR/credit/FX/vol шоков.

F) Liquidity Stress

LIQ‑01: bid‑ask ×3.

LIQ‑02: market depth −50%.

LIQ‑03: deposits −20%.

LIQ‑04: simultaneous margin calls.

11.2. Outputs

Для каждой комбинации scenario × portfolio:

Portfolio P&L.

ΔVaR, ΔGreeks.

ΔK‑factors, ΔCapital Ratio.

LCR impact.

Top‑10 positions по вкладу в P&L.

Хранение: stress_test_results.
Отчёт: отдельный раздел в PDF + вкладка на дашборде.

11.3. Frequency

Standard scenarios: daily (nightly batch).

Ad‑hoc: on‑demand.

Custom: создаются через UI Risk Manager’ом.

11.4. Regulatory Reporting

Quarterly stress‑отчёт для CySEC / Board (результаты, меры, буферы).​

12. VaR Backtesting & Model Governance
12.1. Daily Backtesting

Утро:

сохраняем VaR_forecast (из вчерашнего расчёта) в var_backtesting.

Вечер:

считаем P&L_actual = MtM_EOD − MtM_BOD.

is_exception = (P&L_actual < −VaR_forecast).

Rolling window 250 дней:

exception_rate = #exceptions / 250 (должно ≈ 5% для 95% VaR).​

12.2. Traffic Light (Basel)

0–4 exceptions → Green (model OK).

5–9 → Yellow (review).

10+ → Red (model rejected, multiplier ↑).​

12.3. Statistical Tests

Unconditional coverage (Kupiec).

Independence (clustering).

Conditional coverage (combination).​

12.4. Quarterly Report

Exception charts (30/90/250 дней).

Traffic light status.

P&L distribution vs VaR.

Summary по тестам.

Management commentary и recommendations.

12.5. Model Adjustments

Изменение multiplier.

Расширение historical window.

Добавление стресс‑периода.

Все изменения документируются в model_governance.

13. Performance & Data Quality
13.1. Performance Targets

On‑demand: ≤3 s при ~5k позиций.

Nightly batch: ≤5 min.

Redis‑кеш, параллельный расчёт, bulk‑fetches.

13.2. Data Quality Framework

Подробно описано во вводимом разделе DQ‑правил:

Price Data:

DQ‑01–DQ‑08 (jump, zero/NULL, bid>ask, spread thresholds, stale, volume, yield outliers).

FX Data:

DQ‑10–DQ‑12 (missing FX, FX jumps, arbitrage).

Curves:

DQ‑20–DQ‑22 (inversion, missing tenors, large shifts).

Reference & Positions:

DQ‑30–DQ‑43 (rating changes, missing issuer, maturity mismatch, duplicates, trade_date > today, maturity < today, MtM outliers).

Workflow:

ETL → data_quality_issues (issue_id, severity, source, timestamps).

Alert Engine → алерты.

Dashboard → DQ widget.

Risk team → resolve/accept.

Если issue >24h нерешён → escalation.

PDF‑раздел: число issues по типам, нерешённые, тренд за 30 дней.

14. Security & Access Control
JWT auth, RBAC (Admin/Risk/Trader/Viewer).

HTTPS/TLS, сертификаты, PKI.

Secrets: Vault/KMS.

Audit logging всех операций изменения (limits, configs, approvals).

PII минимизируется, согласовывается с DPO/Legal (GDPR).​

15. News & Events Layer
Источники: Bloomberg/Refinitiv news, регуляторы, эмитенты.​

news_events:

metadata, event_type (RATING_ACTION, SANCTIONS, MACRO, CORPORATE), sentiment, importance, link.

ETL:

fetch → match по ISIN/issuer/country/counterparty → enrich → deduplicate.

Alerts:

rating actions, sanctions, negative news clusters.

Dashboard:

отдельная вкладка News & Events, виджеты на главной.

AI Layer:

связывает движения цен/спредов и алерты с новостями, формирует root‑cause summaries.

16. Integration Architecture
16.1. Market Data (Bloomberg, Refinitiv)

Bloomberg:

BLPAPI, terminal‑based / server API.​

Datasets: reference data, BVAL/prices, BDH (hist), curves, news.

Schedule:

EOD prices: 17:00 EET.

Intraday: on‑demand.

News: streaming with throttling.

Error handling: retries, fallbacks to T‑1, DQ alerts.

Refinitiv:

Eikon Data API (REST).

Используется как backup/secondary source; cross‑check цен и новостей.

16.2. Back‑Office

Protocol: SFTP (CSV/XML) или REST.

Files:

positions_YYYYMMDD.csv (daily, 06:00).

trades_YYYYMMDD.csv (intraday, hourly).

client_balances_YYYYMMDD.csv (daily, EOD).

Validation:

checksums, DQ‑rules, reconciliation.

16.3. Internal Systems (ERP, Treasury, HR)

ERP (Finance):

Own funds, fixed costs, budget (для K‑COH, capital).

Treasury:

funding, HQLA, cash (для LCR, liquidity stress).

HR:

headcount, ключевые роли (для опер. риска и BCP).

16.4. CySEC Reporting Interface

Format: XBRL (COREP/FINREP).​

Frequency: monthly/quarterly.

Delivery: secure upload portal / regulatory gateway.

System:

Maps internal metrics to XBRL templates (K‑factors, capital, LCR, financials).

Runs validation (technical + business rules) перед отправкой.

Хранит XBRL файлы, статусы (draft, validated, submitted) и ответственных.

17. Disaster Recovery & Business Continuity
17.1. Backup Strategy

PostgreSQL:

Full backup daily (02:00 EET) → S3‑совместимое хранилище, encrypted.

Incremental/WAL archiving каждые 6h.

Retention: 30 дней online, 7 лет archive (reporting data).​

Application:

Git repo, Docker images (registry), configs в Vault (с backup).

Reports:

PDF и XBRL → S3 с версионированием, retention 7 лет.

17.2. RTO / RPO

RTO: 4 часа (полное восстановление).

RPO: 1 час (максимальная потеря данных).

Nightly batch:

auto‑retry ×3.

при failure → алерт + manual intervention.

deadline: 08:00 до открытия торгов.

17.3. Redundancy

DB:

Primary region A, replica region B, async replication.

Manual failover, quarterly tests.

App:

Multi‑AZ K8s, auto‑scaling, LB.

17.4. Disaster Scenarios

DB corruption → restore + WAL replay, RTO ~2h.

Region outage → failover to replica region, RTO ≤4h.

Bloomberg outage → Refinitiv fallback, T‑1 prices.

Critical bug → rollback Docker image + rerun batch.

17.5. Testing

Quarterly DR drills:

DB restore, failover, batch run, report generation.

Runbooks:

step‑by‑step для всех ролей.

Sign‑off: CRO + CTO.

17.6. Communication

System outage:

email Risk/Management;

SMS on‑call;

status page update;

ETA.

Workarounds:

Excel templates для грубых DV01/VaR/LCR;

manual position extract;

next‑day catch‑up.

18. Change Management & Versioning
18.1. Versioning

Semantic: MAJOR.MINOR.PATCH (2.7.1 и т.д.).

MAJOR: breaking changes (новый VaR, новая CVA‑модель).

MINOR: новые фичи (новые сценарии, K‑фактор).

PATCH: bugfixes/perf.

risk_snapshots и прочие ключевые таблицы:

engine_version, calculation_timestamp, market_data_snapshot_id.

18.2. Model Change Process

Trigger: изменение risk‑методологии (VaR, PFE, CVA, LCR, K‑factors, stress).

Steps:

Proposal от Risk (описание, rationale).

Parallel run (30+ дней).

Validation report (сравнения, тесты).

Model Risk Committee review.

CRO approval.

Обновление model inventory/documentation.

Post‑implementation review через 30 дней.

18.3. Configuration Changes

Limits, thresholds и пр. — через Admin UI, 4‑eyes principle.

Audit_log: кто, когда, что изменил, причина.

Approval matrix:

Limit increase: Risk Manager + CRO.

Limit decrease: Risk Manager.

Alert thresholds: Risk Manager.

K‑factor method: CRO + Board/Risk Committee.

18.4. Emergency Changes

При критическом дефекте:

Hotfix по verbal approval CRO.

Формальный approval ≤24h.

Post‑mortem ≤3 дней.

18.5. Release Schedule

Major: quarterly.

Minor: monthly.

Patches: as needed.

Release window: Sat 22:00 – Sun 06:00.

Rollback plan: готов для любого релиза.

18.6. Communication

До релиза:

Release notes → Risk team за 1 неделю.

Training/демо при major.

После релиза:

Email announcement.

Обновлённая документация.

2 недели на сбор feedback.

