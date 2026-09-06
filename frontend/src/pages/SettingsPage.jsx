import React, { useState } from 'react';
import { User, Bell, Monitor, Info, Check, AlertTriangle, Shield, Trash2, Moon, Sun, Database } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { useInspection } from '../context/InspectionContext';
import { useAuth } from '../context/AuthContext';
import { cn } from '../utils';

// Simple inline Toggle component
function Toggle({ enabled, onChange, disabled = false }) {
  return (
    <button
      type="button"
      className={cn(
        enabled ? 'bg-primary-600' : 'bg-gray-200',
        disabled && 'opacity-50 cursor-not-allowed',
        'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-2'
      )}
      role="switch"
      aria-checked={enabled}
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
    >
      <span
        aria-hidden="true"
        className={cn(
          enabled ? 'translate-x-5' : 'translate-x-0',
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
        )}
      />
    </button>
  );
}

export default function SettingsPage() {
  const { clearAllInspections, loadSampleData, inspections } = useInspection();
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [toastMessage, setToastMessage] = useState('Settings saved successfully!');
  const [showToast, setShowToast] = useState(false);

  // Profile State
  const [profile, setProfile] = useState({
    name: user?.name || 'Officer',
    email: user?.email || 'officer@lm.gov.in',
    location: user?.location || 'Delhi NCR Region',
    phone: '+91 98765 43210'
  });

  // Notifications State
  const [notifs, setNotifs] = useState({
    emailNew: true,
    alerts: true,
    digest: false,
    updates: true
  });

  // Display State
  const [display, setDisplay] = useState({
    theme: 'light',
    view: 'table',
    perPage: '10',
    threshold: 75
  });

  const handleSave = (customMsg) => {
    if (updateUser) {
      updateUser({
        name: profile.name,
        email: profile.email,
        location: profile.location
      });
    }
    setToastMessage(typeof customMsg === 'string' ? customMsg : 'Settings saved successfully!');
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'display', label: 'Display & Prefs', icon: Monitor },
    { id: 'system', label: 'System Info', icon: Info },
  ];

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your account preferences and system configuration.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar Nav */}
        <div className="w-full md:w-64 shrink-0">
          <nav className="flex flex-col space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <Icon className={cn("w-5 h-5", activeTab === tab.id ? "text-primary-700" : "text-gray-400")} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Area */}
        <div className="flex-1 space-y-6">
          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle>Profile Settings</CardTitle>
                <CardDescription>Update your personal information and contact details.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Full Name</label>
                    <Input 
                      value={profile.name} 
                      onChange={e => setProfile({...profile, name: e.target.value})} 
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Email Address</label>
                    <Input 
                      type="email"
                      value={profile.email} 
                      onChange={e => setProfile({...profile, email: e.target.value})} 
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Badge Number <span className="text-gray-400 text-xs font-normal">(Assigned)</span></label>
                    <Input value={user?.badge || 'LMO-DL-2847'} disabled className="bg-gray-50 text-gray-600 font-mono" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Role <span className="text-gray-400 text-xs font-normal">(Assigned)</span></label>
                    <Input value={user?.role || 'Legal Metrology Enforcement Officer'} disabled className="bg-gray-50 text-gray-600" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Location/Jurisdiction</label>
                    <Input 
                      value={profile.location} 
                      onChange={e => setProfile({...profile, location: e.target.value})} 
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Phone Number</label>
                    <Input 
                      value={profile.phone} 
                      onChange={e => setProfile({...profile, phone: e.target.value})} 
                    />
                  </div>
                </div>
                <div className="pt-4 border-t border-gray-100 flex justify-end">
                  <Button variant="brand" onClick={handleSave}>Save Profile</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Choose what alerts and emails you want to receive.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b border-gray-50">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Email for new inspections</h4>
                      <p className="text-sm text-gray-500 mt-0.5">Receive a confirmation email when an inspection is logged.</p>
                    </div>
                    <Toggle enabled={notifs.emailNew} onChange={v => setNotifs({...notifs, emailNew: v})} />
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-gray-50">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Violation alerts</h4>
                      <p className="text-sm text-gray-500 mt-0.5">Immediate notifications for critical compliance violations.</p>
                    </div>
                    <Toggle enabled={notifs.alerts} onChange={v => setNotifs({...notifs, alerts: v})} />
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-gray-50">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Weekly digest</h4>
                      <p className="text-sm text-gray-500 mt-0.5">A summary report of all inspections conducted during the week.</p>
                    </div>
                    <Toggle enabled={notifs.digest} onChange={v => setNotifs({...notifs, digest: v})} />
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-gray-50">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">System updates</h4>
                      <p className="text-sm text-gray-500 mt-0.5">News about PackCheck AI features and maintenance.</p>
                    </div>
                    <Toggle enabled={notifs.updates} onChange={v => setNotifs({...notifs, updates: v})} />
                  </div>
                </div>
                <div className="pt-4 flex justify-end">
                  <Button variant="brand" onClick={handleSave}>Save Preferences</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'display' && (
            <Card>
              <CardHeader>
                <CardTitle>Display & Preferences</CardTitle>
                <CardDescription>Customize how the application looks and behaves.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-8">
                
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-900">Theme</h4>
                  <div className="flex gap-4">
                    <div 
                      className={cn(
                        "border-2 rounded-lg p-4 cursor-pointer flex flex-col items-center gap-2",
                        display.theme === 'light' ? "border-primary-500 bg-primary-50/30" : "border-gray-200"
                      )}
                      onClick={() => setDisplay({...display, theme: 'light'})}
                    >
                      <Sun className="w-6 h-6 text-yellow-500" />
                      <span className="text-sm font-medium">Light Mode</span>
                    </div>
                    <div className="border-2 border-gray-200 rounded-lg p-4 flex flex-col items-center gap-2 opacity-50 cursor-not-allowed bg-gray-50">
                      <Moon className="w-6 h-6 text-gray-500" />
                      <span className="text-sm font-medium">Dark Mode (Soon)</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Default History View</label>
                    <select 
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 outline-none bg-white"
                      value={display.view}
                      onChange={e => setDisplay({...display, view: e.target.value})}
                    >
                      <option value="table">Data Table</option>
                      <option value="card">Card Grid</option>
                    </select>
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-gray-700">Results Per Page</label>
                    <select 
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 outline-none bg-white"
                      value={display.perPage}
                      onChange={e => setDisplay({...display, perPage: e.target.value})}
                    >
                      <option value="10">10 items</option>
                      <option value="25">25 items</option>
                      <option value="50">50 items</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-medium text-gray-700">AI Confidence Warning Threshold</label>
                    <span className="text-sm font-bold text-primary-600">{display.threshold}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="50" max="95" step="5"
                    value={display.threshold}
                    onChange={e => setDisplay({...display, threshold: Number(e.target.value)})}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                  />
                  <p className="text-xs text-gray-500">
                    Flag AI extractions with confidence below this threshold for manual review.
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-100 flex justify-end">
                  <Button variant="brand" onClick={handleSave}>Save Display Settings</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'system' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-500">Version</span>
                    <span className="text-sm font-medium text-gray-900 font-mono">1.0.0-beta</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-500">Build Target</span>
                    <span className="text-sm font-medium text-gray-900">SIH 2026</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-500">API Connection</span>
                    <span className="text-sm font-medium text-green-600 flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div> Connected
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-500">Last Sync</span>
                    <span className="text-sm font-medium text-gray-900">{new Date().toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-sm text-gray-500">Environment</span>
                    <span className="text-sm font-medium text-gray-900">Browser ({navigator.userAgent.split(' ')[0]})</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-gray-200">
                <CardHeader>
                  <CardTitle className="text-base">Demo Data Management</CardTitle>
                  <CardDescription>
                    Currently storing <span className="font-semibold text-gray-900">{inspections.length}</span> inspection record(s) in browser storage.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Button 
                      variant="outline" 
                      className="text-blue-600 border-blue-200 hover:bg-blue-50"
                      onClick={() => {
                        loadSampleData();
                        setToastMessage('Loaded 12 sample inspection commodities!');
                        setShowToast(true);
                        setTimeout(() => setShowToast(false), 3000);
                      }}
                    >
                      <Database className="w-4 h-4 mr-2" /> Load 12 Sample Commodities
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-red-200">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-start gap-3 text-red-600">
                    <AlertTriangle className="w-6 h-6 mt-0.5 shrink-0" />
                    <div>
                      <h4 className="font-semibold">Reset to Empty State</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Clear all locally saved inspections, active drafts, and reset the dashboard to a clean slate.
                      </p>
                    </div>
                  </div>
                  <div className="pl-9">
                    <Button 
                      variant="outline" 
                      className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300" 
                      onClick={() => {
                        if (window.confirm('Are you sure you want to clear all inspections and reset to an empty state?')) {
                          clearAllInspections();
                          setToastMessage('Local inspections cleared. System reset to empty state.');
                          setShowToast(true);
                          setTimeout(() => setShowToast(false), 3000);
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4 mr-2" /> Clear All Local Data
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Global Toast */}
      {showToast && (
        <div className="fixed bottom-6 right-6 bg-gray-900 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-fade-in z-50">
          <div className="bg-green-500/20 text-green-400 p-1 rounded-full">
            <Check className="w-4 h-4" />
          </div>
          <p className="text-sm font-medium">{toastMessage}</p>
        </div>
      )}
    </div>
  );
}
