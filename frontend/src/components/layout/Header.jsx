import { useState, useRef, useEffect } from 'react';
import { Bell, Menu, ChevronRight, CheckCheck, AlertTriangle, CheckCircle, Info, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { initialNotifications } from '../../data/mockDashboard';

export function Header({ title, breadcrumbs = [], onMenuToggle }) {
  const { user } = useAuth();
  // Default to empty array with NO automatic sample seeding
  const [notifications, setNotifications] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const bellButtonRef = useRef(null);

  // Derived unread count - only count notifications that are NOT read
  const unreadCount = notifications.filter(n => !n.read).length;

  useEffect(() => {
    function handleClickOutside(event) {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target) &&
        bellButtonRef.current &&
        !bellButtonRef.current.contains(event.target)
      ) {
        setDropdownOpen(false);
      }
    }

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [dropdownOpen]);

  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const handleNotificationClick = (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const getNotifIcon = (type) => {
    switch (type) {
      case 'violation':
        return (
          <div className="w-8 h-8 rounded-full bg-red-50 text-red-600 flex items-center justify-center shrink-0">
            <AlertTriangle size={15} />
          </div>
        );
      case 'completed':
        return (
          <div className="w-8 h-8 rounded-full bg-green-50 text-green-600 flex items-center justify-center shrink-0">
            <CheckCircle size={15} />
          </div>
        );
      case 'system':
        return (
          <div className="w-8 h-8 rounded-full bg-purple-50 text-[#8338EC] flex items-center justify-center shrink-0">
            <Sparkles size={15} />
          </div>
        );
      case 'inspection':
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Info size={15} />
          </div>
        );
    }
  };

  return (
    <header className="bg-[#212529] border-b border-slate-700/60 px-4 lg:px-6 py-3 flex items-center gap-4 sticky top-0 z-30">
      {/* Mobile menu */}
      <button onClick={onMenuToggle} className="lg:hidden p-1.5 rounded-md hover:bg-slate-800 text-slate-300">
        <Menu size={20} />
      </button>

      {/* Title / breadcrumbs */}
      <div className="flex-1 min-w-0">
        {breadcrumbs.length > 0 ? (
          <nav className="flex items-center gap-1 text-xs text-slate-400 mb-0.5">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight size={12} />}
                {crumb.to ? (
                  <Link to={crumb.to} className="hover:text-[#8338EC] transition-colors">{crumb.label}</Link>
                ) : (
                  <span>{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        ) : null}
        <h1 className="text-lg font-semibold text-white truncate">{title}</h1>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 shrink-0 relative">
        {/* Notification Bell */}
        <div className="relative">
          <button
            ref={bellButtonRef}
            onClick={() => setDropdownOpen(prev => !prev)}
            className="relative p-2 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#8338EC]"
            aria-label="Notifications"
            aria-expanded={dropdownOpen}
          >
            <Bell size={18} />
            {/* Small orange dot ONLY when unread count > 0 */}
            {unreadCount > 0 && (
              <span 
                className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#FB5607] rounded-full ring-2 ring-[#212529]" 
                aria-hidden="true"
              />
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {dropdownOpen && (
            <div
              ref={dropdownRef}
              className="fixed sm:absolute inset-x-3 top-16 sm:inset-x-auto sm:right-0 sm:top-full sm:mt-2 sm:w-96 bg-white rounded-xl shadow-2xl border border-slate-200 text-slate-900 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100"
              style={{ maxHeight: 'calc(100vh - 80px)' }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/80">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
                  {unreadCount > 0 && (
                    <span className="text-[11px] font-bold px-1.5 py-0.5 bg-[#8338EC]/10 text-[#8338EC] rounded-full">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-xs text-[#8338EC] hover:text-[#7126dc] font-medium flex items-center gap-1 hover:underline cursor-pointer"
                  >
                    <CheckCheck size={14} />
                    <span>Mark all as read</span>
                  </button>
                )}
              </div>

              {/* Notification List */}
              <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
                {notifications.length > 0 ? (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => handleNotificationClick(notif.id)}
                      className={`p-3.5 flex items-start gap-3 hover:bg-slate-50 transition-colors cursor-pointer text-left ${
                        !notif.read ? 'bg-[#8338EC]/5' : ''
                      }`}
                    >
                      {getNotifIcon(notif.type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <p className={`text-xs font-semibold ${!notif.read ? 'text-slate-900' : 'text-slate-700'}`}>
                            {notif.title}
                          </p>
                          <span className="text-[11px] text-slate-400 shrink-0">{notif.time}</span>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                          {notif.message}
                        </p>
                      </div>
                      {/* Unread indicator dot */}
                      {!notif.read && (
                        <span 
                          className="w-2 h-2 rounded-full bg-[#FB5607] shrink-0 mt-1.5" 
                          title="Unread notification"
                        />
                      )}
                    </div>
                  ))
                ) : (
                  /* Clean Empty State */
                  <div className="py-12 px-4 text-center">
                    <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                      <Bell size={22} className="text-slate-400" />
                    </div>
                    <p className="text-sm font-medium text-slate-600">No new notifications</p>
                  </div>
                )}
              </div>

              {/* Footer - shown when there are notifications */}
              {notifications.length > 0 && (
                <div className="p-2.5 bg-slate-50 border-t border-slate-100 text-center">
                  <button
                    onClick={() => setDropdownOpen(false)}
                    className="text-xs font-semibold text-[#8338EC] hover:text-[#7126dc] hover:underline inline-flex items-center gap-1 cursor-pointer"
                  >
                    View All Notifications &rarr;
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* User Avatar */}
        <div className="w-8 h-8 bg-[#8338EC] rounded-full flex items-center justify-center">
          <span className="text-xs font-semibold text-white">
            {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
          </span>
        </div>
      </div>
    </header>
  );
}
