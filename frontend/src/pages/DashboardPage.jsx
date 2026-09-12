import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList, CheckCircle, AlertTriangle, Clock,
  Search, ChevronRight, Plus, Activity
} from 'lucide-react';
import {
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

import { useAuth } from '../context/AuthContext';
import { useInspection } from '../context/InspectionContext';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, StatCard } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/States';
import { ProgressBar } from '../components/ui/ProgressBar';
import { formatDate, getScoreColor } from '../utils';

const COLORS = ['#10b981', '#ef4444', '#f59e0b'];

export default function DashboardPage() {
  const { user } = useAuth();
  const { inspections = [] } = useInspection();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const currentDate = new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

  const filtered = inspections
    .filter(i =>
      (i.product || i.productName || '').toLowerCase().includes(search.toLowerCase()) ||
      String(i.id || '').toLowerCase().includes(search.toLowerCase()) ||
      (i.manufacturer || '').toLowerCase().includes(search.toLowerCase())
    )
    .slice(0, 6);

  const totalInspections = inspections.length;
  const compliantCount = inspections.filter(i => i.status === 'COMPLIANT').length;
  const violationCount = inspections.filter(i => i.status === 'VIOLATION').length;
  const reviewCount = inspections.filter(i => i.status === 'REVIEW_REQUIRED').length;

  // Dynamic status distribution from real user inspections
  const dynamicStatusData = [
    { name: 'Compliant', value: compliantCount, color: '#10b981' },
    { name: 'Violation', value: violationCount, color: '#ef4444' },
    { name: 'Review', value: reviewCount, color: '#f59e0b' },
  ].filter(d => d.value > 0);

  // Dynamic monthly trend based on user's inspections
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const currentMonthIdx = new Date().getMonth();
  const trendData = months.slice(Math.max(0, currentMonthIdx - 5), currentMonthIdx + 1).map(m => {
    return {
      month: m,
      compliant: inspections.filter(i => i.status === 'COMPLIANT').length,
      violations: inspections.filter(i => i.status === 'VIOLATION').length,
      review: inspections.filter(i => i.status === 'REVIEW_REQUIRED').length,
    };
  });

  // Extract real violations from user inspections
  const violationMap = {};
  inspections.forEach(i => {
    (i.violations || []).forEach(v => {
      const title = v.title || 'Packaging Discrepancy';
      violationMap[title] = (violationMap[title] || 0) + 1;
    });
  });
  const userViolationCategories = Object.entries(violationMap).map(([category, count]) => ({ category, count }));
  const maxViolation = userViolationCategories[0]?.count || 1;

  return (
    <div className="p-4 lg:p-6 space-y-6 max-w-7xl mx-auto">

      {/* Welcome banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{greeting}, {user?.name || 'Officer'}</h1>
          <p className="text-slate-500 mt-1 text-sm">{currentDate} &nbsp;|&nbsp; Badge: {user?.badge || 'LMO-DL-2847'}</p>
        </div>
        <Button variant="brand" onClick={() => navigate('/inspection/new')} size="lg" icon={Plus}>
          Start New Inspection
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard label="Total Inspections" value={totalInspections} icon={ClipboardList} color="blue" change={totalInspections > 0 ? `${totalInspections} recorded` : "No inspections yet"} changeType="neutral" />
        <StatCard label="Compliant" value={compliantCount} icon={CheckCircle} color="green" change={totalInspections > 0 ? `${Math.round((compliantCount/totalInspections)*100)}% compliance` : "0% compliance rate"} changeType={compliantCount > 0 ? "up" : "neutral"} />
        <StatCard label="Violations Found" value={violationCount} icon={AlertTriangle} color="red" change={violationCount > 0 ? `${violationCount} infractions` : "No violations"} changeType={violationCount > 0 ? "down" : "neutral"} />
        <StatCard label="Review Required" value={reviewCount} icon={Clock} color="amber" change={reviewCount > 0 ? `${reviewCount} under review` : "0 pending review"} changeType="neutral" />
      </div>

      {/* Charts */}
      {totalInspections > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <CardHeader title="Compliance Trend" subtitle="Recent performance" className="mb-4" />
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '12px' }} />
                  <Line type="monotone" dataKey="compliant" name="Compliant" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="violations" name="Violations" stroke="#ef4444" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="review" name="Review" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <CardHeader title="Status Distribution" subtitle="All-time breakdown" className="mb-4" />
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={dynamicStatusData} cx="50%" cy="50%" innerRadius={65} outerRadius={95} paddingAngle={3} dataKey="value">
                    {dynamicStatusData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center">
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto">
              <ClipboardList size={24} />
            </div>
            <h3 className="text-base font-semibold text-slate-900">No Inspection Analytics Yet</h3>
            <p className="text-sm text-slate-500">
              Your compliance trend, status distribution, and violation analytics will automatically populate here as you perform package inspections.
            </p>
            <div className="pt-2">
              <Button variant="brand" size="sm" onClick={() => navigate('/inspection/new')} icon={Plus}>
                Perform First Inspection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom: Table + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Recent inspections */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between p-5 border-b border-slate-100">
            <div>
              <h3 className="font-semibold text-slate-900">Recent Inspections</h3>
              <p className="text-xs text-slate-500 mt-0.5">Latest inspection records</p>
            </div>
            {totalInspections > 0 && (
              <Button variant="ghost" size="sm" onClick={() => navigate('/history')}>
                View All <ChevronRight size={14} className="ml-1" />
              </Button>
            )}
          </div>
          <div className="p-5">
            {totalInspections > 0 ? (
              <>
                <div className="relative mb-4">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search inspections..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                {filtered.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100">
                          <th className="text-left text-xs font-medium text-slate-500 pb-2 pr-4">ID</th>
                          <th className="text-left text-xs font-medium text-slate-500 pb-2 pr-4">Product</th>
                          <th className="text-left text-xs font-medium text-slate-500 pb-2 pr-4">Date</th>
                          <th className="text-left text-xs font-medium text-slate-500 pb-2 pr-4">Status</th>
                          <th className="text-left text-xs font-medium text-slate-500 pb-2 pr-4">Score</th>
                          <th className="text-left text-xs font-medium text-slate-500 pb-2"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {filtered.map(item => (
                          <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 pr-4 font-mono text-xs text-slate-600">{item.id}</td>
                            <td className="py-3 pr-4">
                              <div className="font-medium text-slate-900 text-sm">{item.product || item.productName}</div>
                              <div className="text-xs text-slate-500 truncate max-w-[120px]">{item.manufacturer}</div>
                            </td>
                            <td className="py-3 pr-4 text-xs text-slate-500 whitespace-nowrap">{formatDate(item.date)}</td>
                            <td className="py-3 pr-4"><StatusBadge status={item.status} /></td>
                            <td className="py-3 pr-4">
                              <span className={`text-sm font-semibold ${getScoreColor(item.score)}`}>{item.score}</span>
                            </td>
                            <td className="py-3">
                              <Button variant="ghost" size="xs" onClick={() => navigate(`/history/${item.id}`)}>View</Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState icon={Search} title="No matching inspections" description="Try a different search term." />
                )}
              </>
            ) : (
              <EmptyState 
                icon={ClipboardList} 
                title="No Inspections Yet" 
                description="You haven't conducted any packaging compliance inspections yet."
                action={
                  <Button variant="brand" size="sm" onClick={() => navigate('/inspection/new')} icon={Plus}>
                    Start First Inspection
                  </Button>
                }
              />
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* Violation categories */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <CardHeader title="Top Violation Types" subtitle="By frequency" className="mb-4" />
            {userViolationCategories.length > 0 ? (
              <div className="space-y-3">
                {userViolationCategories.slice(0, 5).map((cat, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-700 font-medium">{cat.category}</span>
                      <span className="text-slate-500">{cat.count}</span>
                    </div>
                    <ProgressBar value={cat.count} max={maxViolation} size="sm" />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-6 text-center">No violations recorded yet.</p>
            )}
          </div>

          {/* Activity feed */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <CardHeader title="Recent Activity" className="mb-4" />
            {inspections.length > 0 ? (
              <div className="space-y-4">
                {inspections.slice(0, 4).map((item) => (
                  <div key={item.id} className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-2 shrink-0 ${item.status === 'VIOLATION' ? 'bg-red-500' : item.status === 'REVIEW_REQUIRED' ? 'bg-amber-500' : 'bg-green-500'}`} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">
                        {item.product || item.productName}
                      </p>
                      <p className="text-xs text-slate-500">{item.officer} &middot; {item.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-6 text-center">No recent activity.</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
