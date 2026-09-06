import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, History, FileText, BookOpen, Settings, LogOut, Shield, ChevronLeft, ChevronRight, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inspection/new', icon: PlusCircle, label: 'New Inspection' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/rules', icon: BookOpen, label: 'Rule Engine' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleLogout = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      logout();
      navigate('/', { replace: true });
    }, 220);
  };

  return (
    <>
      {isTransitioning && (
        <div 
          className="fixed inset-0 z-[9999] bg-[#212529] pointer-events-none logout-fade-transition"
          aria-hidden="true"
        />
      )}
      <div className={`flex flex-col h-full bg-[#212529] text-white transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
        {/* Logo */}
        <div className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-4'} border-b border-slate-700/50`}>
        {!collapsed ? (
          <>
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 bg-[#8338EC] rounded-lg flex items-center justify-center shrink-0">
                <Shield size={16} className="text-white" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-white leading-tight">PackCheck AI</p>
                <p className="text-xs text-slate-400 leading-tight">Legal Metrology</p>
              </div>
            </div>
            <button 
              onClick={onToggle} 
              className="p-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors shrink-0 cursor-pointer"
              title="Collapse sidebar"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft size={16} />
            </button>
          </>
        ) : (
          <button
            onClick={onToggle}
            className="w-8 h-8 bg-[#8338EC] hover:bg-[#7126dc] active:bg-[#5d19bf] rounded-lg flex items-center justify-center transition-all cursor-pointer shadow-sm focus:outline-none focus:ring-2 focus:ring-[#8338EC] focus:ring-offset-2 focus:ring-offset-[#212529] group"
            title="Expand sidebar"
            aria-label="Expand sidebar"
          >
            <Shield size={16} className="text-white transition-transform group-hover:scale-105" />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${
                isActive
                  ? 'bg-[#8338EC] text-white font-medium'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`
            }
            title={collapsed ? label : undefined}
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span className="text-sm truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User profile */}
      <div className="border-t border-slate-700/50 p-3">
        <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 bg-[#8338EC] rounded-full flex items-center justify-center shrink-0">
            <User size={14} className="text-white" />
          </div>
          {!collapsed && user && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate">{user.role}</p>
            </div>
          )}
          {!collapsed && (
            <button onClick={handleLogout} className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors cursor-pointer" title="Logout">
              <LogOut size={14} />
            </button>
          )}
        </div>
        {collapsed && (
          <button onClick={handleLogout} className="mt-2 w-full flex justify-center p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors cursor-pointer" title="Logout">
            <LogOut size={14} />
          </button>
        )}
      </div>
    </div>
    </>
  );
}
