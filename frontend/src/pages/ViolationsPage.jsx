import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  AlertOctagon, 
  Info, 
  FileText,
  ImageIcon,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useInspection } from '../context/InspectionContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/States';
import { getSeverityColor, getConfidenceColor, formatConfidence } from '../utils';

import { mockInspections } from '../data/mockInspections';

export default function ViolationsPage() {
  const navigate = useNavigate();
  const { currentInspection, inspections, updateViolationRemarks } = useInspection();
  
  const inspection = currentInspection || (inspections && inspections.length > 0 ? inspections[0] : null);
  const [remarks, setRemarks] = useState(inspection?.officerRemarks || '');
  const [expandedRule, setExpandedRule] = useState(null);

  if (!inspection) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <EmptyState 
          title="No Inspection Selected"
          description="Conduct an inspection to analyze and view legal metrology violations and compliance discrepancies."
          action={
            <Button onClick={() => navigate('/inspection/new')}>
              Start New Inspection
            </Button>
          }
        />
      </div>
    );
  }

  const rawViolations = inspection.violations || [];
  const violations = rawViolations.map(v => ({
    ...v,
    title: v.title || 'Legal Metrology Violation',
    severity: v.severity || 'HIGH',
    detectedValue: v.detectedValue || 'Non-compliant value',
    expectedValue: v.expectedRequirement || v.expectedValue || 'Mandatory standard format under PC Rules',
    reference: v.ruleRef || v.reference || 'PC Rules, Rule 6',
    description: v.explanation || v.description || 'Violation of legal metrology packaged commodities requirements.',
    confidence: v.confidence || 0.95,
    recommendedAction: v.recommendedAction || 'Issue show-cause notice and request corrective declaration before sale.'
  }));
  const hasViolations = violations.length > 0;

  const handleSaveRemarks = (e) => {
    setRemarks(e.target.value);
    if (updateViolationRemarks && violations[0]?.id) {
      updateViolationRemarks(violations[0].id, e.target.value);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Summary Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" onClick={() => navigate('/inspection/result')} className="flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to Results
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              Violation Analysis
              <Badge variant={hasViolations ? 'danger' : 'success'}>
                {hasViolations ? `${violations.length} Violation(s) Found` : 'No Violations'}
              </Badge>
            </h1>
            <p className="text-sm text-gray-500 mt-1">Inspection ID: {inspection.id} &middot; Product: {inspection.product || inspection.productName}</p>
          </div>
        </div>
      </div>

      {!hasViolations ? (
        <EmptyState 
          icon={<AlertOctagon className="w-12 h-12 text-green-500" />}
          title="No Violations Found"
          description="All compliance checks passed for this product."
          action={<Button onClick={() => navigate('/inspection/result')}>Return to Results</Button>}
        />
      ) : (
        <div className="space-y-6">
          {violations.map((violation, idx) => {
            const isExpanded = expandedRule === idx;
            return (
              <Card key={idx} className="border-red-200 overflow-hidden">
                <div className="bg-red-50 p-4 border-b border-red-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <AlertOctagon className="w-5 h-5 text-red-600" />
                    <h2 className="text-lg font-bold text-red-900">{violation.title}</h2>
                    <Badge className={getSeverityColor(violation.severity)}>
                      {violation.severity}
                    </Badge>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-500">Detected Value</h4>
                        <p className="text-base font-semibold text-gray-900 mt-1">{violation.detectedValue || 'Not Found'}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500">Expected Requirement</h4>
                        <p className="text-base text-gray-800 mt-1">{violation.expectedValue}</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 flex justify-between items-center">
                          Rule Reference
                          <button onClick={() => setExpandedRule(isExpanded ? null : idx)} className="text-blue-600 hover:text-blue-800 flex items-center gap-1 text-xs">
                            {isExpanded ? 'Hide Details' : 'Show Details'} {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        </h4>
                        <p className="text-base font-medium text-gray-900 mt-1">{violation.reference}</p>
                        {isExpanded && (
                          <div className="mt-2 p-3 bg-gray-50 rounded-md text-sm text-gray-600 border border-gray-200">
                            {violation.ruleDescription || 'Detailed legal text for this rule reference...'}
                          </div>
                        )}
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500">Detection Confidence</h4>
                        <div className="mt-1">
                          <Badge className={getConfidenceColor(violation.confidence)}>
                            {formatConfidence(violation.confidence)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-500 mb-2">Explanation</h4>
                    <p className="text-gray-700">{violation.description}</p>
                  </div>

                  <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3">
                    <Info className="w-5 h-5 text-blue-600 shrink-0" />
                    <div>
                      <h4 className="text-sm font-semibold text-blue-900">Recommended Action</h4>
                      <p className="text-sm text-blue-800 mt-1">{violation.recommendedAction || 'Issue show-cause notice to the manufacturer and direct withdrawal of non-compliant batches.'}</p>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Officer Remarks</h3>
            <textarea
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-3 border h-32"
              placeholder="Enter official remarks, observations, or next steps here..."
              value={remarks}
              onChange={handleSaveRemarks}
            />
            <p className="text-xs text-gray-500 mt-2">These remarks will be included in the final generated report.</p>
          </Card>

          <div className="flex flex-wrap gap-4 pt-4 border-t border-gray-200">
            <Button variant="outline" onClick={() => navigate('/inspection/result')}>
              Back to Results
            </Button>
            <Button variant="outline" onClick={() => navigate('/inspection/evidence')} className="flex items-center gap-2">
              <ImageIcon className="w-4 h-4" /> View Evidence
            </Button>
            <Button variant="primary" onClick={() => navigate('/inspection/report')} className="flex items-center gap-2">
              <FileText className="w-4 h-4" /> Generate Report
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

