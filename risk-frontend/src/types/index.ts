export interface RiskSnapshot {
  risk_snapshot_id: string;
  portfolio_id: number;
  snapshot_date: string;
  calculation_timestamp: string;
  calculation_status: string;
  market: MarketMetrics;
  credit: CreditMetrics;
  ccr: CCRMetrics;
  liquidity: LiquidityMetrics;
  capital: CapitalMetrics;
  alerts_summary: AlertsSummary;
  error_message?: string;
}

export interface MarketMetrics {
  var_1d_95: number;
  stressed_var: number;
  dv01_total: number;
  duration: number;
  convexity: number;
}

export interface CreditMetrics {
  total_exposure: number;
  credit_var: number;
  cva_total: number;
  expected_loss: number;
}

export interface CCRMetrics {
  pfe_current: number;
  pfe_peak: number;
  ead_total: number;
}

export interface LiquidityMetrics {
  liquidation_cost_1d: number;
  liquidation_cost_5d: number;
  liquidity_score: number;
  lcr_ratio: number;
  funding_gap_short_term: number;
}

export interface CapitalMetrics {
  k_npr: number;
  k_aum: number;
  k_cmh: number;
  k_coh: number;
  total_k_req: number;
  own_funds: number;
  capital_ratio: number;
}

export interface AlertsSummary {
  GREEN: number;
  YELLOW: number;
  RED: number;
  CRITICAL: number;
}

export interface Alert {
  id: number;
  portfolio_id?: number;
  alert_type: string;
  severity: 'GREEN' | 'YELLOW' | 'RED' | 'CRITICAL';
  metric_name?: string;
  current_value?: number;
  threshold_value?: number;
  description: string;
  recommendation?: string;
  acknowledged: boolean;
  created_at: string;
}

export interface Portfolio {
  id: number;
  name: string;
  portfolio_type: string;
  base_currency: string;
  status: string;
}
