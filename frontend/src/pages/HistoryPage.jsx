import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ChevronDown, 
  ChevronUp, 
  ChevronLeft, 
  ChevronRight,
  Eye,
  Download
} from 'lucide-react';

import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/States';
import { Input } from '../components/ui/Input';
import { useInspection } from '../context/InspectionContext';
import { cn } from '../utils';

export default function HistoryPage() {
  const { inspections = [] } = useInspection();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [scoreFilter, setScoreFilter] = useState('All');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  
  const [sortCol, setSortCol] = useState('date');
  const [sortDesc, setSortDesc] = useState(true);
  
  const [page, setPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDesc(!sortDesc);
    } else {
      setSortCol(col);
      setSortDesc(true);
    }
  };

  const filteredData = useMemo(() => {
    return inspections.filter((item) => {
      // Search
      const searchLower = search.toLowerCase();
      const prod = (item.product || item.productName || '').toLowerCase();
      const mfr = (item.manufacturer || '').toLowerCase();
      const id = String(item.id || '').toLowerCase();
      if (search && !id.includes(searchLower) && !prod.includes(searchLower) && !mfr.includes(searchLower)) {
        return false;
      }
      // Status (case-insensitive check)
      if (statusFilter !== 'All') {
        const itemStatus = (item.status || '').toUpperCase();
        const filterStatus = statusFilter.toUpperCase().replace(/\s+/g, '_');
        if (itemStatus !== filterStatus && itemStatus !== statusFilter.toUpperCase()) {
          return false;
        }
      }
      // Score
      if (scoreFilter !== 'All') {
        if (scoreFilter === '>=90' && item.score < 90) return false;
        if (scoreFilter === '>=75' && (item.score < 75 || item.score >= 90)) return false;
        if (scoreFilter === '<75' && item.score >= 75) return false;
      }
      // Date
      if (dateFrom && new Date(item.date) < new Date(dateFrom)) return false;
      if (dateTo && new Date(item.date) > new Date(dateTo)) return false;

      return true;
    }).sort((a, b) => {
      let valA = sortCol === 'product' || sortCol === 'productName' ? (a.product || a.productName) : a[sortCol];
      let valB = sortCol === 'product' || sortCol === 'productName' ? (b.product || b.productName) : b[sortCol];
      if (sortCol === 'date') {
        valA = new Date(valA || 0).getTime();
        valB = new Date(valB || 0).getTime();
      }
      
      if (valA < valB) return sortDesc ? 1 : -1;
      if (valA > valB) return sortDesc ? -1 : 1;
      return 0;
    });
  }, [inspections, search, statusFilter, scoreFilter, dateFrom, dateTo, sortCol, sortDesc]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / itemsPerPage));
  const currentData = filteredData.slice((page - 1) * itemsPerPage, page * itemsPerPage);

  const stats = useMemo(() => {
    const total = inspections.length;
    const compliant = inspections.filter(i => (i.status || '').toUpperCase() === 'COMPLIANT').length;
    const violations = inspections.filter(i => (i.status || '').toUpperCase() === 'VIOLATION').length;
    const review = inspections.filter(i => (i.status || '').toUpperCase() === 'REVIEW_REQUIRED' || (i.status || '').toUpperCase() === 'REVIEW').length;
    return { total, compliant, violations, review };
  }, [inspections]);

  const clearFilters = () => {
    setSearch('');
    setStatusFilter('All');
    setScoreFilter('All');
    setDateFrom('');
    setDateTo('');
    setPage(1);
  };

  const SortIcon = ({ col }) => {
    if (sortCol !== col) return <ChevronDown className="w-4 h-4 text-gray-300 ml-1 inline" />;
    return sortDesc ? <ChevronDown className="w-4 h-4 text-gray-700 ml-1 inline" /> : <ChevronUp className="w-4 h-4 text-gray-700 ml-1 inline" />;
  };

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inspection History</h1>
          <p className="text-gray-500">View and manage past packaging inspections.</p>
        </div>
        
        <div className="flex flex-wrap gap-2 text-sm font-medium">
          <div className="bg-gray-100 px-3 py-1.5 rounded-full text-gray-700">Total: {stats.total}</div>
          <div className="bg-green-100 px-3 py-1.5 rounded-full text-green-700">Compliant: {stats.compliant}</div>
          <div className="bg-red-100 px-3 py-1.5 rounded-full text-red-700">Violations: {stats.violations}</div>
          <div className="bg-yellow-100 px-3 py-1.5 rounded-full text-yellow-700">Review: {stats.review}</div>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <input 
                  type="text"
                  placeholder="Search by ID, product, manufacturer..." 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full h-10 rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-[#8338EC] focus:border-transparent hover:border-slate-400"
                />
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Status Filter */}
            <div className="w-full lg:w-36 shrink-0">
              <select 
                className="w-full h-10 border border-slate-300 bg-white rounded-lg px-3 text-sm text-slate-700 focus:ring-2 focus:ring-[#8338EC] focus:border-transparent outline-none hover:border-slate-400 cursor-pointer"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="All">All Statuses</option>
                <option value="Compliant">Compliant</option>
                <option value="Violation">Violation</option>
                <option value="Review Required">Review Required</option>
              </select>
            </div>

            {/* Score Filter */}
            <div className="w-full lg:w-32 shrink-0">
              <select 
                className="w-full h-10 border border-slate-300 bg-white rounded-lg px-3 text-sm text-slate-700 focus:ring-2 focus:ring-[#8338EC] focus:border-transparent outline-none hover:border-slate-400 cursor-pointer"
                value={scoreFilter}
                onChange={(e) => setScoreFilter(e.target.value)}
              >
                <option value="All">All Scores</option>
                <option value=">=90">&ge; 90</option>
                <option value=">=75">75 - 89</option>
                <option value="<75">&lt; 75</option>
              </select>
            </div>

            {/* From Date */}
            <label className="w-full lg:w-[205px] shrink-0 flex items-center h-10 rounded-lg border border-slate-300 bg-white px-2.5 focus-within:ring-2 focus-within:ring-[#8338EC] focus-within:border-transparent hover:border-slate-400 cursor-pointer">
              <span className="text-xs font-medium text-slate-500 mr-1.5 shrink-0 select-none">From Date</span>
              <input 
                type="date"
                title="From Date"
                aria-label="From Date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full text-xs text-slate-700 bg-transparent focus:outline-none cursor-pointer [&::-webkit-calendar-picker-indicator]:cursor-pointer"
              />
            </label>

            {/* To Date */}
            <label className="w-full lg:w-[205px] shrink-0 flex items-center h-10 rounded-lg border border-slate-300 bg-white px-2.5 focus-within:ring-2 focus-within:ring-[#8338EC] focus-within:border-transparent hover:border-slate-400 cursor-pointer">
              <span className="text-xs font-medium text-slate-500 mr-1.5 shrink-0 select-none">To Date</span>
              <input 
                type="date"
                title="To Date"
                aria-label="To Date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full text-xs text-slate-700 bg-transparent focus:outline-none cursor-pointer [&::-webkit-calendar-picker-indicator]:cursor-pointer"
              />
            </label>

            {/* Clear Filters Button */}
            <div className="shrink-0">
              <Button 
                variant="outline" 
                onClick={clearFilters}
                className="w-full lg:w-auto h-10 px-3 text-sm whitespace-nowrap"
              >
                <Filter className="w-4 h-4 mr-1.5" />
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-sm text-gray-500">
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('id')}>
                  ID <SortIcon col="id" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('productName')}>
                  Product <SortIcon col="productName" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('manufacturer')}>
                  Manufacturer <SortIcon col="manufacturer" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('date')}>
                  Date <SortIcon col="date" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('officer')}>
                  Officer <SortIcon col="officer" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('score')}>
                  Score <SortIcon col="score" />
                </th>
                <th className="p-4 font-medium cursor-pointer" onClick={() => handleSort('status')}>
                  Status <SortIcon col="status" />
                </th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-sm">
              {currentData.length > 0 ? (
                currentData.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4 font-medium text-gray-900">{item.id}</td>
                    <td className="p-4 text-gray-700">{item.product || item.productName}</td>
                    <td className="p-4 text-gray-500">{item.manufacturer}</td>
                    <td className="p-4 text-gray-500">{item.date}</td>
                    <td className="p-4 text-gray-500">{item.officer}</td>
                    <td className="p-4 font-medium">
                      <span className={cn(
                        item.score >= 90 ? 'text-green-600' :
                        item.score >= 75 ? 'text-yellow-600' : 'text-red-600'
                      )}>
                        {item.score}%
                      </span>
                    </td>
                    <td className="p-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="p-4 text-right">
                      <Link to={`/history/${item.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4 mr-1" /> View
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="p-8">
                    {inspections.length === 0 ? (
                      <EmptyState 
                        title="No inspection records found" 
                        description="You have not conducted any packaging inspections yet. Start your first inspection to analyze compliance."
                        action={
                          <Link to="/inspection/new">
                            <Button variant="brand">Start New Inspection</Button>
                          </Link>
                        }
                      />
                    ) : (
                      <EmptyState 
                        title="No matching inspections" 
                        description="No inspections match your current filters."
                        icon={<Filter className="w-8 h-8 text-gray-400" />}
                        action={
                          <Button variant="outline" onClick={clearFilters}>Clear Filters</Button>
                        }
                      />
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {filteredData.length > 0 && (
          <div className="p-4 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>Show</span>
              <select 
                value={itemsPerPage} 
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setPage(1);
                }}
                className="border border-gray-300 rounded px-2 py-1 outline-none"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
              <span>per page</span>
            </div>
            
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-500">
                Page {page} of {totalPages || 1}
              </span>
              <div className="flex gap-1">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-2"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages || totalPages === 0}
                  className="px-2"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
