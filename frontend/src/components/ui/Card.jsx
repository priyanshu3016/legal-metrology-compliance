import { classNames } from '../../utils';

export function Card({ children, className = '', padding = true }) {
  return (
    <div className={classNames('bg-white rounded-xl border border-slate-200 shadow-sm', padding ? 'p-5' : '', className)}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action, className = '' }) {
  return (
    <div className={classNames('flex items-start justify-between gap-4', className)}>
      <div>
        {title && <h3 className="text-base font-semibold text-slate-900">{title}</h3>}
        {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function StatCard({ label, value, icon: Icon, change, changeType = 'neutral', color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  const changeColors = { up: 'text-green-600', down: 'text-red-600', neutral: 'text-slate-500' };
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {Icon && (
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
            <Icon size={20} />
          </div>
        )}
      </div>
      <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
      {change !== undefined && (
        <p className={`mt-1 text-xs font-medium ${changeColors[changeType]}`}>{change}</p>
      )}
    </div>
  );
}

// Shadcn-style sub-components for compatibility with generated pages
export function CardTitle({ children, className = '' }) {
  return <h3 className={`text-base font-semibold text-slate-900 ${className}`}>{children}</h3>;
}

export function CardContent({ children, className = '' }) {
  return <div className={`pt-4 ${className}`}>{children}</div>;
}

export function CardDescription({ children, className = '' }) {
  return <p className={`text-sm text-slate-500 ${className}`}>{children}</p>;
}

export default Card;

