import { AlertCircle, SearchX, FileX, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-10 h-10 border-3 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}

export function ErrorState({ message = 'Something went wrong', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center">
        <AlertCircle className="text-red-500" size={24} />
      </div>
      <p className="text-sm font-medium text-slate-700">{message}</p>
      {onRetry && <Button variant="secondary" size="sm" onClick={onRetry} icon={RefreshCw}>Retry</Button>}
    </div>
  );
}

export function EmptyState({ title = 'No data', description, action, icon: Icon = SearchX }) {
  const renderIcon = () => {
    if (!Icon) return null;
    if (typeof Icon === 'function' || (typeof Icon === 'object' && Icon !== null && 'render' in Icon)) {
      return <Icon className="text-slate-400" size={28} />;
    }
    return Icon;
  };

  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-14 h-14 bg-slate-50 rounded-full flex items-center justify-center">
        {renderIcon()}
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-slate-700">{title}</p>
        {description && <p className="text-xs text-slate-500 mt-1 max-w-xs">{description}</p>}
      </div>
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse bg-slate-200 rounded-lg ${className}`} />;
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
      <Skeleton className="h-5 w-1/2" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  );
}

export default EmptyState;
