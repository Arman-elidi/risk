import type { RiskSnapshot } from '../types';
import './MetricsCards.css';

interface Props {
  snapshot: RiskSnapshot;
}

export default function MetricsCards({ snapshot }: Props) {
  const formatCurrency = (value: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

  const formatPercent = (value: number) => 
    `${(value * 100).toFixed(2)}%`;

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">VaR (1d 95%)</div>
        <div className="metric-value">{formatCurrency(snapshot.market.var_1d_95)}</div>
        <div className="metric-change">Stressed: {formatCurrency(snapshot.market.stressed_var)}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">DV01</div>
        <div className="metric-value">{formatCurrency(snapshot.market.dv01_total)}</div>
        <div className="metric-change">Duration: {snapshot.market.duration.toFixed(2)}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Total Exposure</div>
        <div className="metric-value">{formatCurrency(snapshot.credit.total_exposure)}</div>
        <div className="metric-change">Expected Loss: {formatCurrency(snapshot.credit.expected_loss)}</div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Capital Ratio</div>
        <div className="metric-value capital-ratio">
          {snapshot.capital.capital_ratio.toFixed(2)}
        </div>
        <div className="metric-change">
          Own Funds: {formatCurrency(snapshot.capital.own_funds)}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">LCR</div>
        <div className="metric-value lcr">
          {formatPercent(snapshot.liquidity.lcr_ratio)}
        </div>
        <div className="metric-change">
          Liq Score: {(snapshot.liquidity.liquidity_score * 100).toFixed(0)}%
        </div>
      </div>

      <div className="metric-card alerts-card">
        <div className="metric-label">Alerts</div>
        <div className="alerts-summary">
          <span className="alert-badge critical">{snapshot.alerts_summary.CRITICAL}</span>
          <span className="alert-badge red">{snapshot.alerts_summary.RED}</span>
          <span className="alert-badge yellow">{snapshot.alerts_summary.YELLOW}</span>
          <span className="alert-badge green">{snapshot.alerts_summary.GREEN}</span>
        </div>
      </div>
    </div>
  );
}
