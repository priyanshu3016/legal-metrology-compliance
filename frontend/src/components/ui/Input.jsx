import { classNames } from '../../utils';

export function Input({ label, error, helper, className = '', required, ...props }) {
  return (
    <div className={classNames('flex flex-col gap-1', className)}>
      {label && (
        <label className="text-sm font-medium text-slate-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <input
        className={classNames(
          'w-full rounded-lg border px-3 py-2 text-sm text-slate-900 placeholder-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          error ? 'border-red-300 bg-red-50' : 'border-slate-300 bg-white hover:border-slate-400'
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
      {helper && !error && <p className="text-xs text-slate-500">{helper}</p>}
    </div>
  );
}

export function Select({ label, error, helper, className = '', required, children, ...props }) {
  return (
    <div className={classNames('flex flex-col gap-1', className)}>
      {label && (
        <label className="text-sm font-medium text-slate-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <select
        className={classNames(
          'w-full rounded-lg border px-3 py-2 text-sm text-slate-900 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white',
          error ? 'border-red-300 bg-red-50' : 'border-slate-300 hover:border-slate-400'
        )}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {helper && !error && <p className="text-xs text-slate-500">{helper}</p>}
    </div>
  );
}

export function Textarea({ label, error, helper, className = '', required, ...props }) {
  return (
    <div className={classNames('flex flex-col gap-1', className)}>
      {label && (
        <label className="text-sm font-medium text-slate-700">
          {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      )}
      <textarea
        className={classNames(
          'w-full rounded-lg border px-3 py-2 text-sm text-slate-900 placeholder-slate-400 resize-y transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          error ? 'border-red-300 bg-red-50' : 'border-slate-300 bg-white hover:border-slate-400'
        )}
        rows={3}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
      {helper && !error && <p className="text-xs text-slate-500">{helper}</p>}
    </div>
  );
}

export default Input;
