// Utility functions for PackCheck AI

export const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  } catch { return dateStr; }
};

export const formatDateTime = (dateStr, timeStr) => {
  if (!dateStr) return 'N/A';
  const d = formatDate(dateStr);
  return timeStr ? (d + ', ' + timeStr) : d;
};

export const getStatusColor = (status) => {
  switch (status) {
    case 'COMPLIANT': case 'PASS': return 'text-green-700 bg-green-50 border-green-200';
    case 'VIOLATION': case 'FAIL': return 'text-red-700 bg-red-50 border-red-200';
    case 'REVIEW_REQUIRED': case 'REVIEW': return 'text-amber-700 bg-amber-50 border-amber-200';
    default: return 'text-slate-600 bg-slate-50 border-slate-200';
  }
};

export const getStatusLabel = (status) => {
  switch (status) {
    case 'COMPLIANT': return 'Compliant';
    case 'VIOLATION': return 'Violation';
    case 'REVIEW_REQUIRED': return 'Review Required';
    case 'PASS': return 'Pass';
    case 'FAIL': return 'Fail';
    case 'REVIEW': return 'Review';
    default: return status;
  }
};

export const getSeverityColor = (severity) => {
  switch (severity) {
    case 'CRITICAL': return 'text-red-800 bg-red-100 border-red-300';
    case 'HIGH': return 'text-orange-700 bg-orange-50 border-orange-200';
    case 'MEDIUM': return 'text-amber-700 bg-amber-50 border-amber-200';
    case 'LOW': return 'text-blue-700 bg-blue-50 border-blue-200';
    default: return 'text-slate-600 bg-slate-50 border-slate-200';
  }
};

export const getScoreColor = (score) => {
  if (score >= 90) return 'text-green-600';
  if (score >= 75) return 'text-amber-600';
  return 'text-red-600';
};

export const getScoreBg = (score) => {
  if (score >= 90) return 'bg-green-500';
  if (score >= 75) return 'bg-amber-500';
  return 'bg-red-500';
};

export const getConfidenceColor = (confidence) => {
  if (confidence >= 0.90) return 'text-green-600';
  if (confidence >= 0.75) return 'text-amber-600';
  return 'text-red-600';
};

export const getConfidenceBg = (confidence) => {
  if (confidence >= 0.90) return 'bg-green-500';
  if (confidence >= 0.75) return 'bg-amber-500';
  return 'bg-red-500';
};

export const formatConfidence = (confidence) => {
  if (confidence === undefined || confidence === null) return 'N/A';
  const val = confidence <= 1 ? confidence * 100 : confidence;
  return `${Math.round(val)}%`;
};

export const generateInspectionId = () => {
  const year = new Date().getFullYear();
  const rand = Math.floor(Math.random() * 9000) + 1000;
  return `INS-${year}-${rand}`;
};

export const generateId = generateInspectionId;

export const truncate = (str, maxLen = 40) => {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
};

export const classNames = (...classes) => classes.filter(Boolean).join(' ');
export const cn = classNames;
