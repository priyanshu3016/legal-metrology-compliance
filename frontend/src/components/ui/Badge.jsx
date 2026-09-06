import { getStatusColor, getStatusLabel, getSeverityColor } from '../../utils';

export function StatusBadge({ status, size = 'sm' }) {
  const colors = getStatusColor(status);
  const label = getStatusLabel(status);
  const sizeClass = size === 'lg' ? 'px-3 py-1 text-sm font-semibold' : 'px-2 py-0.5 text-xs font-medium';
  return (
    <span className={`inline-flex items-center rounded-full border ${colors} ${sizeClass}`}>
      {label}
    </span>
  );
}

export function SeverityBadge({ severity, size = 'sm' }) {
  const colors = getSeverityColor(severity);
  const sizeClass = size === 'lg' ? 'px-3 py-1 text-sm font-semibold' : 'px-2 py-0.5 text-xs font-medium';
  return (
    <span className={`inline-flex items-center rounded-full border ${colors} ${sizeClass}`}>
      {severity}
    </span>
  );
}

export function ConfidenceBadge({ confidence }) {
  const pct = confidence !== undefined && confidence !== null ? Math.round(confidence * 100) : null;
  if (pct === null) return <span className="text-xs text-slate-400">N/A</span>;
  const color = pct >= 90 ? 'text-green-700 bg-green-50 border-green-200'
    : pct >= 75 ? 'text-amber-700 bg-amber-50 border-amber-200'
    : 'text-red-700 bg-red-50 border-red-200';
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${color}`}>
      {pct}%
    </span>
  );
}

export const Badge = StatusBadge;
export default StatusBadge;
