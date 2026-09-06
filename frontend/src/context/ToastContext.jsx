import { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback((message, type) => {
    const id = Date.now().toString();
    setToasts((prev) => {
      const newToasts = [...prev, { id, message, type }];
      if (newToasts.length > 5) {
        return newToasts.slice(newToasts.length - 5);
      }
      return newToasts;
    });

    setTimeout(() => {
      removeToast(id);
    }, 4000);
  }, [removeToast]);

  const toast = {
    success: (message) => addToast(message, 'success'),
    error: (message) => addToast(message, 'error'),
    warning: (message) => addToast(message, 'warning'),
    info: (message) => addToast(message, 'info'),
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(({ id, message, type }) => {
          const icons = {
            success: <CheckCircle className="w-5 h-5 text-green-500" />,
            error: <XCircle className="w-5 h-5 text-red-500" />,
            warning: <AlertCircle className="w-5 h-5 text-amber-500" />,
            info: <Info className="w-5 h-5 text-blue-500" />
          };
          
          const bgColors = {
            success: 'bg-green-50 border-green-200',
            error: 'bg-red-50 border-red-200',
            warning: 'bg-amber-50 border-amber-200',
            info: 'bg-blue-50 border-blue-200'
          };

          return (
            <div 
              key={id}
              className={`flex items-start p-4 mb-2 rounded-lg border shadow-sm pointer-events-auto transition-all duration-300 ease-in-out animate-in slide-in-from-right-8 fade-in ${bgColors[type]}`}
            >
              <div className="flex-shrink-0">{icons[type]}</div>
              <div className="ml-3 mr-4 text-sm font-medium text-gray-800">
                {message}
              </div>
              <button 
                onClick={() => removeToast(id)}
                className="ml-auto flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context.toast;
}
