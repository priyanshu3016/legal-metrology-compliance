import { getScoreBg } from '../../utils';

const colorMap = {
  red: 'bg-red-500', green: 'bg-green-500', blue: 'bg-blue-500',
  amber: 'bg-amber-500', yellow: 'bg-yellow-500', purple: 'bg-purple-500',
  slate: 'bg-slate-400',
};

export function ProgressBar({ value, max = 100, color, size = 'md', showLabel = false }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const barColor = color ? (colorMap[color] || color) : getScoreBg(pct);
  const heights = { xs: 'h-1', sm: 'h-2', md: 'h-3', lg: 'h-4' };
  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 bg-slate-100 rounded-full overflow-hidden ${heights[size]}`}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && <span className="text-xs font-medium text-slate-600 w-8 text-right">{Math.round(pct)}%</span>}
    </div>
  );
}

export function CircularProgress({ value, max = 100, size = 80, strokeWidth = 8 }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (pct / 100) * circumference;
  const color = pct >= 90 ? '#16a34a' : pct >= 75 ? '#d97706' : '#dc2626';
  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={strokeWidth} />
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth}
        strokeDasharray={circumference} strokeDashoffset={circumference - dash}
        strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
    </svg>
  );
}

export default ProgressBar;
