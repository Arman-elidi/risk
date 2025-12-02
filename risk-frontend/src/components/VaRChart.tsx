import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { RiskSnapshot } from '../types';

interface Props {
  snapshots: RiskSnapshot[];
}

export default function VaRChart({ snapshots }: Props) {
  const data = snapshots.map(s => ({
    date: new Date(s.snapshot_date).toLocaleDateString(),
    var_1d_95: s.market.var_1d_95,
    stressed_var: s.market.stressed_var,
  })).reverse();

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="var_1d_95" stroke="#3498db" name="VaR 1d 95%" />
        <Line type="monotone" dataKey="stressed_var" stroke="#e74c3c" name="Stressed VaR" strokeDasharray="5 5" />
      </LineChart>
    </ResponsiveContainer>
  );
}
