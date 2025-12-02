import { useQuery } from '@tanstack/react-query';
import { riskApi } from '../api/client';
import MetricsCards from '../components/MetricsCards';
import VaRChart from '../components/VaRChart';
import AlertsTable from '../components/AlertsTable';
import './Dashboard.css';

export default function Dashboard() {
  const { data: portfolios } = useQuery({
    queryKey: ['portfolios'],
    queryFn: async () => {
      const res = await riskApi.getPortfolios();
      return res.data;
    },
  });

  const { data: snapshots } = useQuery({
    queryKey: ['risk-snapshots'],
    queryFn: async () => {
      const res = await riskApi.listRiskSnapshots();
      return res.data;
    },
  });

  const { data: alerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const res = await riskApi.getAlerts({ acknowledged: false });
      return res.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const latestSnapshot = snapshots?.[0];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>AI Risk Orchestrator</h1>
        <div className="header-info">
          <span>Last Update: {latestSnapshot?.calculation_timestamp || 'N/A'}</span>
          <span>Status: {latestSnapshot?.calculation_status || 'Unknown'}</span>
        </div>
      </header>

      {latestSnapshot && (
        <>
          <MetricsCards snapshot={latestSnapshot} />
          
          <div className="charts-grid">
            <div className="chart-container">
              <h2>Value at Risk Trend</h2>
              <VaRChart snapshots={snapshots || []} />
            </div>
          </div>

          <div className="alerts-section">
            <h2>Active Alerts</h2>
            <AlertsTable alerts={alerts || []} />
          </div>
        </>
      )}

      {!latestSnapshot && (
        <div className="no-data">
          <p>No risk data available. Please run risk calculation.</p>
        </div>
      )}
    </div>
  );
}
