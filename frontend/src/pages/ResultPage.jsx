import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  ShieldAlert, 
  Image as ImageIcon, 
  BarChart2, 
  ArrowRight,
  Info
} from 'lucide-react';
import { useInspection } from '../context/InspectionContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { EmptyState } from '../components/ui/States';
import { 
  getStatusColor, 
  getStatusLabel, 
  getConfidenceColor, 
  formatConfidence,
  getScoreColor
} from '../utils';

import { mockInspections } from '../data/mockInspections';

export default function ResultPage() {
  const navigate = useNavigate();
  const { currentInspection, inspections } = useInspection();
  const [activeTab, setActiveTab] = useState('extracted');
  const [expandedCheck, setExpandedCheck] = useState(null);

  // If no active inspection in context, check if there's any recent inspection or show empty state
  const inspection = currentInspection || (inspections && inspections.length > 0 ? inspections[0] : null);

  if (!inspection) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <EmptyState 
          title="No Active Inspection Found"
          description="You have not run an inspection yet. Upload packaging photos and begin a new AI inspection to review compliance findings here."
          action={
            <Button onClick={() => navigate('/inspection/new')}>
              Start New Inspection
            </Button>
          }
        />
      </div>
    );
  }

  const id = inspection.id || 'INS-2026-0001';
  const status = inspection.status || 'COMPLIANT';
  const productName = inspection.product || inspection.productName || 'Basmati Rice Premium';
  const timestamp = inspection.timestamp || `${inspection.date || '2026-08-15'} ${inspection.time || '10:30'}`;
  const score = inspection.score ?? 95;
  const confidence = inspection.confidence ?? 0.96;
  const officerName = inspection.officer || inspection.officerName || 'Rajesh Kumar';

  const extractedData = inspection.extractedData || {
    productName: { value: inspection.product, confidence: Math.round((inspection.ocrConfidence?.product_name || 0.98) * 100) },
    manufacturer: { value: inspection.manufacturer, confidence: Math.round((inspection.ocrConfidence?.manufacturer || 0.95) * 100) },
    packer: { value: inspection.packer || inspection.manufacturer, confidence: 95 },
    netQuantity: { value: inspection.netQuantity, confidence: Math.round((inspection.ocrConfidence?.net_quantity || 0.99) * 100) },
    mrp: { value: inspection.mrp, confidence: Math.round((inspection.ocrConfidence?.mrp || 0.98) * 100) },
    unitSalePrice: { value: inspection.unitSalePrice || 'Not Declared', confidence: Math.round((inspection.ocrConfidence?.unit_sale_price || 0.85) * 100) },
    packedDate: { value: inspection.packedDate, confidence: Math.round((inspection.ocrConfidence?.packed_date || 0.97) * 100) },
    bestBefore: { value: inspection.bestBefore || 'N/A', confidence: 94 },
    consumerCare: { value: inspection.consumerCare, confidence: Math.round((inspection.ocrConfidence?.consumer_care || 0.96) * 100) },
    countryOfOrigin: { value: inspection.countryOfOrigin || 'India', confidence: 99 },
    batchNumber: { value: inspection.batchNumber || 'N/A', confidence: 97 },
    licenseNumber: { value: inspection.licenseNumber || 'N/A', confidence: 96 },
  };

  const complianceChecks = inspection.complianceChecks || (inspection.checks || []).map(c => ({
    ruleName: c.name,
    reference: c.ruleRef,
    result: c.status,
    confidence: typeof c.confidence === 'number' && c.confidence <= 1 ? Math.round(c.confidence * 100) : (c.confidence || 95),
    detectedValue: c.detectedValue,
    expectedValue: c.expectedRequirement,
    explanation: c.explanation
  }));

  const boundingBoxes = inspection.boundingBoxes && inspection.boundingBoxes.length > 0
    ? inspection.boundingBoxes.map(b => ({
        ...b,
        x: typeof b.x === 'number' && b.x > 100 ? Math.round(b.x / 10) : b.x,
        y: typeof b.y === 'number' && b.y > 100 ? Math.round(b.y / 10) : b.y,
        width: typeof b.width === 'number' && b.width > 100 ? Math.round(b.width / 10) : b.width,
        height: typeof b.height === 'number' && b.height > 100 ? Math.round(b.height / 10) : b.height,
      }))
    : [
        { field: 'MRP', value: '₹850', confidence: 98, x: 12, y: 55, width: 28, height: 14 },
        { field: 'Net Quantity', value: '5kg', confidence: 99, x: 60, y: 55, width: 28, height: 14 },
        { field: 'Manufacturer', value: 'Agro Farms', confidence: 95, x: 12, y: 15, width: 50, height: 18 },
        { field: 'Consumer Care', value: '1800-123-4567', confidence: 96, x: 12, y: 75, width: 45, height: 12 }
      ];

  const StatusIcon = status === 'COMPLIANT' ? CheckCircle : status === 'VIOLATION' ? XCircle : AlertTriangle;
  
  const getBannerColor = (status) => {
    switch (status) {
      case 'COMPLIANT': return 'bg-green-50 border-green-200';
      case 'VIOLATION': return 'bg-red-50 border-red-200';
      case 'REVIEW_REQUIRED': return 'bg-amber-50 border-amber-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const tabs = [
    { id: 'extracted', label: 'Extracted Information', icon: FileText },
    { id: 'checks', label: 'Compliance Checks', icon: ShieldAlert },
    { id: 'ocr', label: 'OCR Confidence', icon: BarChart2 },
    { id: 'evidence', label: 'Evidence', icon: ImageIcon },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Summary Banner */}
      <div className={`w-full p-6 border rounded-xl shadow-sm flex flex-col md:flex-row items-center justify-between gap-6 ${getBannerColor(status)}`}>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-gray-900">{productName || 'Unknown Product'}</h1>
            <Badge variant={status === 'COMPLIANT' ? 'success' : status === 'VIOLATION' ? 'danger' : 'warning'}>
              <div className="flex items-center gap-1">
                <StatusIcon className="w-4 h-4" />
                <span>{getStatusLabel(status)}</span>
              </div>
            </Badge>
          </div>
          <div className="text-sm text-gray-600 flex flex-wrap gap-4">
            <span><strong>ID:</strong> {id}</span>
            <span><strong>Time:</strong> {new Date(timestamp).toLocaleString()}</span>
            <span><strong>Officer:</strong> {officerName}</span>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center shrink-0">
          <div className="relative w-24 h-24 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-gray-200"
                strokeWidth="3"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={getScoreColor(score).replace('text-', 'stroke-')}
                strokeWidth="3"
                strokeDasharray={`${score}, 100`}
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className="text-2xl font-bold text-gray-900">{score}</span>
              <span className="text-xs text-gray-500">/100</span>
            </div>
          </div>
          <div className="mt-2 text-sm font-medium text-gray-700">
            Overall Confidence: {formatConfidence(confidence)}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0">
          <Button variant="outline" onClick={() => navigate('/inspection/report')}>
            View Report
          </Button>
          {status === 'VIOLATION' && (
            <Button variant="danger" onClick={() => navigate('/inspection/violations')}>
              View Violations
            </Button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${isActive 
                    ? 'border-[#8338EC] text-[#8338EC]' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'extracted' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(extractedData || {}).map(([key, data]) => (
              <Card key={key} className="p-4 flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-500 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</h3>
                  <p className={`mt-1 text-base font-semibold ${!data?.value ? 'text-gray-400 italic' : data.value === 'N/A' ? 'text-slate-500' : 'text-gray-900'}`}>
                    {data?.value || 'Not Detected'}
                  </p>
                </div>
                <div title={`Confidence: ${formatConfidence(data?.confidence)}`}>
                  <div className={`w-3 h-3 rounded-full ${
                    !data?.value ? 'bg-red-500' : 
                    data.confidence < 75 ? 'bg-amber-500' : 'bg-green-500'
                  }`} />
                </div>
              </Card>
            ))}
          </div>
        )}

        {activeTab === 'checks' && (
          <div className="space-y-4">
            {complianceChecks?.map((check, idx) => {
              const isExpanded = expandedCheck === idx;
              const CheckIcon = check.result === 'PASS' ? CheckCircle : check.result === 'FAIL' ? XCircle : AlertTriangle;
              return (
                <Card key={idx} className="overflow-hidden">
                  <div className="p-4 flex items-center justify-between bg-gray-50">
                    <div className="flex items-center gap-4 flex-1">
                      <CheckIcon className={`w-6 h-6 ${
                        check.result === 'PASS' ? 'text-green-500' : 
                        check.result === 'FAIL' ? 'text-red-500' : 'text-amber-500'
                      }`} />
                      <div>
                        <h3 className="font-semibold text-gray-900">{check.ruleName}</h3>
                        <p className="text-sm text-gray-500">{check.reference}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge className={getConfidenceColor(check.confidence)}>
                        {formatConfidence(check.confidence)}
                      </Badge>
                      <button onClick={() => setExpandedCheck(isExpanded ? null : idx)} className="text-gray-400 hover:text-gray-600">
                        {isExpanded ? <ChevronUp /> : <ChevronDown />}
                      </button>
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="p-4 border-t border-gray-200 bg-white">
                      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                        <div>
                          <span className="text-gray-500 block mb-1">Detected Value:</span>
                          <span className="font-medium">{check.detectedValue || 'None'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block mb-1">Expected:</span>
                          <span className="font-medium">{check.expectedValue || 'Any valid format'}</span>
                        </div>
                      </div>
                      <div className="bg-blue-50 text-blue-800 p-3 rounded-md text-sm flex items-start gap-2">
                        <Info className="w-5 h-5 shrink-0 mt-0.5" />
                        <p>{check.explanation}</p>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}

        {activeTab === 'ocr' && (
          <div className="space-y-6">
            <Card className="p-6">
              <h2 className="text-lg font-semibold mb-6">Field Extraction Confidence</h2>
              <div className="space-y-6">
                {Object.entries(extractedData || {}).map(([key, data]) => (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                      <span className="text-sm font-semibold">{formatConfidence(data?.confidence)}</span>
                    </div>
                    <ProgressBar 
                      value={data?.confidence || 0} 
                      color={data?.confidence < 75 ? 'amber' : 'green'}
                    />
                    {data?.confidence < 75 && (
                      <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Low confidence extraction. Please verify manually.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'evidence' && (
          <Card className="p-6">
            <div className="flex flex-col md:flex-row gap-8">
              <div className="flex-1">
                <div className="relative w-full aspect-video bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden">
                  <span className="text-gray-400 font-medium">Package Image</span>
                  {boundingBoxes?.map((box, idx) => (
                    <div 
                      key={idx}
                      className="absolute border-2 border-blue-500 bg-blue-500/20 cursor-pointer hover:bg-blue-500/40 transition-colors flex items-start"
                      style={{ 
                        left: `${box.x}%`, 
                        top: `${box.y}%`, 
                        width: `${box.width}%`, 
                        height: `${box.height}%` 
                      }}
                      title={box.field}
                    >
                      <span className="bg-blue-500 text-white text-[10px] px-1 whitespace-nowrap absolute -top-4 left-0">
                        {box.field}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-4 text-center">
                  Click on a region to see extracted text
                </p>
              </div>
              <div className="w-full md:w-64 space-y-4">
                <h3 className="font-semibold text-gray-900">Detected Regions</h3>
                <ul className="space-y-2">
                  {boundingBoxes?.map((box, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                      <div className="w-3 h-3 bg-blue-500 rounded-sm"></div>
                      <span className="capitalize">{box.field.replace(/([A-Z])/g, ' $1').trim()}</span>
                    </li>
                  ))}
                </ul>
                <Button className="w-full mt-4" onClick={() => navigate('/inspection/evidence')}>
                  View Full Evidence Manager
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="mt-8 flex flex-wrap gap-4 pt-6 border-t border-gray-200">
        <Button variant="outline" onClick={() => navigate('/inspection/evidence')} className="flex items-center gap-2">
          View Full Evidence <ArrowRight className="w-4 h-4" />
        </Button>
        <Button variant="outline" onClick={() => navigate('/inspection/report')} className="flex items-center gap-2">
          Generate Report <FileText className="w-4 h-4" />
        </Button>
        {status === 'VIOLATION' && (
          <Button variant="danger" onClick={() => navigate('/inspection/violations')} className="flex items-center gap-2">
            View Violations <ShieldAlert className="w-4 h-4" />
          </Button>
        )}
      </div>

      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3 text-sm text-amber-800">
        <AlertTriangle className="w-5 h-5 shrink-0" />
        <p>
          <strong>AI Disclaimer:</strong> This is an AI-assisted compliance screening. Results are based on automated analysis of uploaded images and may contain inaccuracies. Final compliance determination requires review by a certified Legal Metrology officer.
        </p>
      </div>
    </div>
  );
}

