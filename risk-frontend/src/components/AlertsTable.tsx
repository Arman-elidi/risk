import type { Alert } from '../types';
import { riskApi } from '../api/client';
import './AlertsTable.css';

interface Props {
  alerts: Alert[];
}

export default function AlertsTable({ alerts }: Props) {
  const handleAcknowledge = async (alertId: number) => {
    try {
      await riskApi.acknowledgeAlert(alertId);
      // Refresh alerts
      window.location.reload();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getSeverityClass = (severity: string) => {
    return `severity-${severity.toLowerCase()}`;
  };

  return (
    <div className="alerts-table-container">
      <table className="alerts-table">
        <thead>
          <tr>
            <th>Severity</th>
            <th>Type</th>
            <th>Metric</th>
            <th>Description</th>
            <th>Value</th>
            <th>Threshold</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map(alert => (
            <tr key={alert.id} className={getSeverityClass(alert.severity)}>
              <td>
                <span className={`severity-badge ${getSeverityClass(alert.severity)}`}>
                  {alert.severity}
                </span>
              </td>
              <td>{alert.alert_type}</td>
              <td>{alert.metric_name || 'N/A'}</td>
              <td>{alert.description}</td>
              <td>{alert.current_value?.toFixed(2) || 'N/A'}</td>
              <td>{alert.threshold_value?.toFixed(2) || 'N/A'}</td>
              <td>{new Date(alert.created_at).toLocaleString()}</td>
              <td>
                {!alert.acknowledged && (
                  <button 
                    onClick={() => handleAcknowledge(alert.id)}
                    className="ack-button"
                  >
                    Acknowledge
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {alerts.length === 0 && (
        <div className="no-alerts">No active alerts</div>
      )}
    </div>
  );
}
