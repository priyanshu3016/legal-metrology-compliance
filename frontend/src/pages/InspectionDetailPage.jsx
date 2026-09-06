import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  MapPin, 
  Calendar, 
  User, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon
} from 'lucide-react';

import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { ErrorState, EmptyState } from '../components/ui/States';
import { CircularProgress } from '../components/ui/ProgressBar';
import { useInspection } from '../context/InspectionContext';
import { mockInspections } from '../data/mockInspections';
import { cn } from '../utils';

function CheckCard({ check }) {
  const [expanded, setExpanded] = useState(false);
  
  const statusUpper = (check.status || '').toUpperCase();
  const isPass = statusUpper === 'PASS';
  const isFail = statusUpper === 'FAIL';
  
  const Icon = isPass ? CheckCircle : isFail ? XCircle : AlertTriangle;
               
  const colorClass = isPass ? 'text-green-600 bg-green-50' : 
                     isFail ? 'text-red-600 bg-red-50' : 
                     'text-amber-600 bg-amber-50';

  const ruleTitle = check.name || check.rule || check.ruleRef || 'Compliance Check';
  const description = check.explanation || check.description || check.expectedRequirement || '';
  const extractedValue = check.detectedValue || check.extractedValue || 'N/A';
  const expectedFormat = check.expectedRequirement || check.expectedFormat || 'Standard Legal Metrology format';
  const confidence = check.confidence !== undefined ? Math.round(check.confidence <= 1 ? check.confidence * 100 : check.confidence) : 95;

  return (
    <Card className="overflow-hidden border-gray-200 shadow-sm">
      <div 
        className="p-4 flex items-start gap-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={cn("p-2 rounded-full mt-1 shrink-0", colorClass)}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <h4 className="font-medium text-gray-900">{ruleTitle}</h4>
            {expanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
          </div>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{description}</p>
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 border-t border-gray-100 bg-gray-50">
          <div className="space-y-4">
            <div>
              <h5 className="text-sm font-semibold text-gray-700 mb-1">Extracted Value</h5>
              <p className="text-sm text-gray-900">{extractedValue}</p>
            </div>
            <div>
              <h5 className="text-sm font-semibold text-gray-700 mb-1">Expected Format/Value</h5>
              <p className="text-sm text-gray-900">{expectedFormat}</p>
            </div>
            <div>
              <h5 className="text-sm font-semibold text-gray-700 mb-1">AI Confidence</h5>
              <p className="text-sm text-gray-900">{confidence}%</p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

export default function InspectionDetailPage() {
  const { id } = useParams();
  const { inspections = [] } = useInspection();
  const [activeTab, setActiveTab] = useState('overview');
  
  const inspection = inspections.find(i => i.id === id) || mockInspections.find(i => i.id === id);
  
  if (!inspection) {
    return (
      <div className="max-w-3xl mx-auto py-12">
        <ErrorState 
          title="Inspection Not Found"
          message={`Could not find an inspection with ID: ${id}`}
          action={
            <Link to="/history">
              <Button><ArrowLeft className="w-4 h-4 mr-2" /> Back to History</Button>
            </Link>
          }
        />
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'checks', label: 'Compliance Checks' },
    { id: 'violations', label: 'Violations' },
    { id: 'evidence', label: 'Evidence & Images' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div>
          <Link to="/history" className="text-sm text-gray-500 hover:text-primary-600 flex items-center mb-4 inline-flex">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to History
          </Link>
          <div className="flex flex-col md:flex-row justify-between md:items-end gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold text-gray-900">{inspection.id}</h1>
                <StatusBadge status={inspection.status} />
                <Badge variant={
                  inspection.score >= 90 ? 'success' :
                  inspection.score >= 75 ? 'warning' : 'danger'
                }>
                  Score: {inspection.score}%
                </Badge>
              </div>
              <h2 className="text-xl text-gray-700">{inspection.product || inspection.productName}</h2>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3 text-sm text-gray-600 bg-white p-3 rounded-lg border border-gray-200 shadow-sm">
              <div className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-gray-400"/> {inspection.date}</div>
              <div className="hidden sm:block text-gray-300">|</div>
              <div className="flex items-center gap-1.5"><User className="w-4 h-4 text-gray-400"/> {inspection.officer}</div>
              <div className="hidden sm:block text-gray-300">|</div>
              <div className="flex items-center gap-1.5"><MapPin className="w-4 h-4 text-gray-400"/> {inspection.location || 'N/A'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition-colors",
                activeTab === tab.id
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Product Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Product Name</div>
                      <div className="mt-1 text-sm text-gray-900">{inspection.product || inspection.productName}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Manufacturer</div>
                      <div className="mt-1 text-sm text-gray-900">{inspection.manufacturer}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Category</div>
                      <div className="mt-1 text-sm text-gray-900">{inspection.category || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-500">Net Quantity</div>
                      <div className="mt-1 text-sm text-gray-900">{inspection.netQuantity || 'N/A'}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Inspection Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {inspection.summary || `Inspection completed on ${inspection.date} by ${inspection.officer}. The product received a score of ${inspection.score}%. Overall status is marked as ${inspection.status}.`}
                  </p>
                </CardContent>
              </Card>
            </div>
            
            <div className="space-y-6">
              <Card>
                <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-4">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">Compliance Score</h3>
                  <div className="w-32 h-32 relative">
                    <CircularProgress 
                      value={inspection.score} 
                      size={128} 
                      strokeWidth={12} 
                      colorClass={
                        inspection.score >= 90 ? 'text-green-500' :
                        inspection.score >= 75 ? 'text-yellow-500' : 'text-red-500'
                      }
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-3xl font-bold text-gray-900">{inspection.score}%</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500">
                    {inspection.score >= 90 ? 'Excellent compliance.' :
                     inspection.score >= 75 ? 'Minor issues found.' : 'Significant violations detected.'}
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'checks' && (
          <div className="space-y-4">
            {inspection.checks && inspection.checks.length > 0 ? (
              inspection.checks.map((check, idx) => (
                <CheckCard key={idx} check={check} />
              ))
            ) : (
              <EmptyState 
                title="No checks recorded"
                description="Detailed compliance checks are not available for this inspection."
                icon={<CheckCircle className="w-8 h-8 text-gray-400" />}
              />
            )}
          </div>
        )}

        {activeTab === 'violations' && (
          <div className="space-y-4">
            {inspection.violations && inspection.violations.length > 0 ? (
              inspection.violations.map((violation, idx) => (
                <Card key={idx} className="border-red-200 bg-red-50/30">
                  <CardContent className="p-4 flex gap-4">
                    <div className="p-2 bg-red-100 text-red-600 rounded-full h-fit">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 text-lg">{violation.title || violation.rule || 'Violation'}</h4>
                      <p className="text-gray-700 mt-1">{violation.explanation || violation.description}</p>
                      
                      <div className="mt-4 bg-white p-3 rounded border border-red-100 flex items-start gap-2">
                        <Info className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                        <span className="text-sm text-gray-600">{violation.recommendedAction || violation.remediation || 'Issue formal warning and require rectification of package declarations.'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <EmptyState 
                title="No Violations Found"
                description="This product met all required compliance checks."
                icon={<CheckCircle className="w-10 h-10 text-green-500" />}
              />
            )}
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Analyzed Images</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {inspection.images && inspection.images.length > 0 ? (
                    inspection.images.map((img, idx) => (
                      <div key={idx} className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-200 group flex items-center justify-center">
                        <ImageIcon className="w-12 h-12 text-gray-300" />
                        <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button variant="secondary" size="sm">View Panel {idx + 1}</Button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="col-span-full py-8 text-center bg-gray-50 rounded-lg border border-dashed border-gray-300">
                      <ImageIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">No images available</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Detected Fields (OCR & Vision Data)</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-t border-gray-200">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3 font-medium text-gray-500">Field Type</th>
                        <th className="px-4 py-3 font-medium text-gray-500">Extracted Text</th>
                        <th className="px-4 py-3 font-medium text-gray-500">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {(() => {
                        const fields = inspection.detectedFields && inspection.detectedFields.length > 0
                          ? inspection.detectedFields
                          : Object.entries(inspection.ocrConfidence || {}).map(([key, conf]) => ({
                              type: key.replace(/_/g, ' ').toUpperCase(),
                              text: inspection[key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())] || inspection[key] || 'Detected',
                              confidence: Math.round(conf <= 1 ? conf * 100 : conf)
                            }));
                        return fields.length > 0 ? (
                          fields.map((field, idx) => (
                            <tr key={idx}>
                              <td className="px-4 py-3 font-medium text-gray-900">{field.type}</td>
                              <td className="px-4 py-3 text-gray-700">{field.text}</td>
                              <td className="px-4 py-3">
                                <Badge variant={field.confidence >= 90 ? 'success' : field.confidence >= 70 ? 'warning' : 'danger'}>
                                  {field.confidence}%
                                </Badge>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="3" className="px-4 py-8 text-center text-gray-500">
                              Raw detection data not available for this record.
                            </td>
                          </tr>
                        );
                      })()}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 mt-8">
        <Link to="/history">
          <Button variant="outline">Back to History</Button>
        </Link>
        <Button>
          <Download className="w-4 h-4 mr-2" /> Download Report
        </Button>
      </div>
    </div>
  );
}
