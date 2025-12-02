import axios from 'axios';
import type { RiskSnapshot, Alert, Portfolio } from '../types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const riskApi = {
  // Portfolios
  getPortfolios: () => api.get<Portfolio[]>('/portfolios'),
  
  getPortfolio: (id: number) => api.get<Portfolio>(`/portfolios/${id}`),
  
  // Risk Snapshots
  getRiskSnapshot: (snapshotId: number) => 
    api.get<RiskSnapshot>(`/risk_snapshots/${snapshotId}`),
  
  listRiskSnapshots: (portfolioId?: number) => 
    api.get<RiskSnapshot[]>('/risk_snapshots', {
      params: { portfolio_id: portfolioId }
    }),
  
  calculateRisk: (portfolioId: number, request: any) =>
    api.post(`/portfolios/${portfolioId}/risk/calculate`, request),
  
  // Alerts
  getAlerts: (params?: {
    portfolio_id?: number;
    severity?: string;
    acknowledged?: boolean;
  }) => api.get<Alert[]>('/alerts', { params }),
  
  acknowledgeAlert: (alertId: number, comment?: string) =>
    api.post(`/alerts/${alertId}/ack`, { comment }),
  
  // Reports
  generatePdfReport: (reportDate?: string) =>
    api.post('/reports/pdf/generate', { report_date: reportDate }),
  
  downloadPdfReport: (reportDate: string) =>
    api.get(`/reports/pdf/download`, {
      params: { report_date: reportDate },
      responseType: 'blob',
    }),
};

export default api;
