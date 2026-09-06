import { classNames } from '../../utils';

const variants = {
  primary: 'bg-[#FB5607] text-white hover:bg-[#e04b04] active:bg-[#c54002] shadow-sm',
  brand: 'bg-[#8338EC] text-white hover:bg-[#7126dc] active:bg-[#5d19bf] shadow-sm',
  secondary: 'bg-white text-[#212529] border border-slate-300 hover:bg-[#E9ECEF] active:bg-slate-200 shadow-sm',
  outline: 'bg-transparent text-[#212529] border border-slate-300 hover:bg-[#E9ECEF] active:bg-slate-200 shadow-sm',
  danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 shadow-sm',
  ghost: 'text-[#212529] hover:bg-[#E9ECEF] active:bg-slate-200',
  success: 'bg-green-600 text-white hover:bg-green-700 active:bg-green-800 shadow-sm',
};
const sizes = {
  xs: 'px-2.5 py-1 text-xs',
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
};

export function Button({ children, variant = 'primary', size = 'md', className = '', disabled, loading, onClick, type = 'button', icon: Icon, ...props }) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={classNames(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-[#8338EC] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : Icon ? <Icon size={size === 'xs' || size === 'sm' ? 14 : 16} /> : null}
      {children}
    </button>
  );
}

export default Button;
