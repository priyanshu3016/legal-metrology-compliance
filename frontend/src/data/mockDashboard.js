export const monthlyData = [
  { month: 'Sep', count: 120 },
  { month: 'Oct', count: 145 },
  { month: 'Nov', count: 130 },
  { month: 'Dec', count: 160 },
  { month: 'Jan', count: 155 },
  { month: 'Feb', count: 140 },
  { month: 'Mar', count: 175 },
  { month: 'Apr', count: 180 },
  { month: 'May', count: 165 },
  { month: 'Jun', count: 190 },
  { month: 'Jul', count: 210 },
  { month: 'Aug', count: 225 }
];

export const statusData = [
  { id: 'Compliant', label: 'Compliant', value: 1420, color: 'hsl(142, 71%, 45%)' },
  { id: 'Violation', label: 'Violation', value: 430, color: 'hsl(348, 83%, 47%)' },
  { id: 'Review Required', label: 'Review Required', value: 145, color: 'hsl(48, 89%, 50%)' }
];

export const weeklyTrend = [
  { day: 'Mon', compliant: 12, violations: 4, review: 1 },
  { day: 'Tue', compliant: 15, violations: 3, review: 2 },
  { day: 'Wed', compliant: 18, violations: 5, review: 0 },
  { day: 'Thu', compliant: 14, violations: 2, review: 3 },
  { day: 'Fri', compliant: 20, violations: 6, review: 1 },
  { day: 'Sat', compliant: 5, violations: 1, review: 0 },
  { day: 'Sun', compliant: 2, violations: 0, review: 0 }
];

export const violationCategories = [
  { category: 'Missing MRP', count: 125 },
  { category: 'Missing Unit Sale Price', count: 98 },
  { category: 'Improper Net Quantity', count: 85 },
  { category: 'Missing Consumer Care', count: 62 },
  { category: 'Date Marking Error', count: 45 },
  { category: 'Manufacturer Details Incomplete', count: 15 }
];

export const officerStats = [
  { name: 'Rajesh Kumar', inspections: 450, violationsFound: 112, avgScore: 82 },
  { name: 'Amit Sharma', inspections: 420, violationsFound: 98, avgScore: 85 },
  { name: 'Vikram Singh', inspections: 380, violationsFound: 85, avgScore: 86 },
  { name: 'Priya Desai', inspections: 310, violationsFound: 70, avgScore: 88 },
  { name: 'Sanjay Verma', inspections: 290, violationsFound: 50, avgScore: 90 }
];

export const recentActivity = [
  { id: 'act-1', type: 'INSPECTION_COMPLETED', user: 'Rajesh Kumar', product: 'Imported Almonds', status: 'REVIEW_REQUIRED', time: '10 mins ago' },
  { id: 'act-2', type: 'VIOLATION_LOGGED', user: 'Amit Sharma', product: 'Green Tea Bags', status: 'VIOLATION', time: '1 hour ago' },
  { id: 'act-3', type: 'INSPECTION_COMPLETED', user: 'Vikram Singh', product: 'Real Mango Fruit Juice', status: 'COMPLIANT', time: '2 hours ago' },
  { id: 'act-4', type: 'REPORT_GENERATED', user: 'System', product: 'Monthly Enforcement Report', status: 'INFO', time: '5 hours ago' },
  { id: 'act-5', type: 'INSPECTION_COMPLETED', user: 'Priya Desai', product: 'Choco Delight Biscuits', status: 'REVIEW_REQUIRED', time: '1 day ago' }
];

export const initialNotifications = [
  {
    id: 'notif-001',
    title: 'New Inspection Assigned',
    message: 'A new priority inspection (INS-2026-0845) has been assigned to your station in Delhi NCR.',
    time: '5m ago',
    read: false,
    type: 'inspection'
  },
  {
    id: 'notif-002',
    title: 'Violation Detected',
    message: 'Non-compliance (Rule 6(1)(b) MRP) was flagged in inspection INS-2026-0842.',
    time: '25m ago',
    read: false,
    type: 'violation'
  },
  {
    id: 'notif-003',
    title: 'Inspection Completed',
    message: 'Official report for inspection INS-2026-0841 was completed successfully.',
    time: '2h ago',
    read: true,
    type: 'completed'
  },
  {
    id: 'notif-004',
    title: 'System Update',
    message: 'New features and updated Legal Metrology rules have been added to PackCheck AI.',
    time: '1d ago',
    read: true,
    type: 'system'
  }
];

export default {
  monthlyData,
  statusData,
  weeklyTrend,
  violationCategories,
  officerStats,
  recentActivity,
  initialNotifications
};
