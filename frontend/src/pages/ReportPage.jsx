import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Printer, ArrowLeft, Shield } from 'lucide-react';
import { useInspection } from '../context/InspectionContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/States';
import { formatConfidence, getStatusLabel } from '../utils';

import { mockInspections } from '../data/mockInspections';

export default function ReportPage() {
  const navigate = useNavigate();
  const { currentInspection, inspections } = useInspection();

  const raw = currentInspection || (inspections && inspections.length > 0 ? inspections[0] : null);

  if (!raw) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <EmptyState 
          title="No Inspection Report Available"
          description="Complete an AI inspection to generate and print official Legal Metrology compliance reports."
          action={
            <Button onClick={() => navigate('/inspection/new')}>
              Start New Inspection
            </Button>
          }
        />
      </div>
    );
  }

  const id = raw.id || 'INS-2026-0001';
  const status = raw.status || 'COMPLIANT';
  const productName = raw.product || raw.productName || 'Basmati Rice Premium';
  const timestamp = raw.timestamp || `${raw.date || '2026-08-15'} ${raw.time || '10:30'}`;
  const score = raw.score ?? 95;
  const officerName = raw.officer || raw.officerName || 'Rajesh Kumar';

  const extractedData = raw.extractedData || {
    manufacturer: { value: raw.manufacturer || 'Agro Farms India Pvt. Ltd.' },
    netQuantity: { value: raw.netQuantity || '5kg' },
    mrp: { value: raw.mrp || '₹850' },
    packedDate: { value: raw.packedDate || 'July 2026' },
    batchNumber: { value: raw.batchNumber || 'BR-2607-452' },
  };

  const complianceChecks = raw.complianceChecks || (raw.checks || []).map(c => ({
    ruleName: c.name,
    reference: c.ruleRef,
    result: c.status,
    explanation: c.explanation
  }));

  const violations = (raw.violations || []).map(v => ({
    title: v.title || 'Legal Metrology Violation',
    reference: v.ruleRef || v.reference || 'PC Rules, Rule 6',
    description: v.explanation || v.description || 'Non-compliance detected.',
    recommendedAction: v.recommendedAction || 'Direct corrective action under Legal Metrology Rules.'
  }));

  const officerRemarks = raw.officerRemarks || (raw.notes || '');

  const handlePrint = () => {
    window.print();
  };

  const statusColors = {
    COMPLIANT: 'text-green-700 bg-green-50 border-green-200',
    VIOLATION: 'text-red-700 bg-red-50 border-red-200',
    REVIEW_REQUIRED: 'text-amber-700 bg-amber-50 border-amber-200'
  };

  return (
    <div className="max-w-4xl mx-auto pb-12 print:pb-0">
      {/* Action Buttons (Hidden on Print) */}
      <div className="flex justify-between items-center mb-6 print:hidden">
        <Button variant="outline" onClick={() => navigate('/inspection/result')} className="flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Results
        </Button>
        <Button variant="primary" onClick={handlePrint} className="flex items-center gap-2">
          <Printer className="w-4 h-4" /> Print Report
        </Button>
      </div>

      {/* Paper Report Container */}
      <div className="bg-white p-8 md:p-12 border border-gray-200 shadow-sm print:shadow-none print:border-none print:p-0">
        
        {/* Report Header */}
        <div className="text-center mb-8 border-b-2 border-gray-800 pb-6">
          <div className="flex justify-center mb-2">
            <Shield className="w-12 h-12 text-blue-800" />
          </div>
          <h1 className="text-xl font-bold uppercase tracking-wider text-gray-900">Government of India</h1>
          <h2 className="text-md font-semibold text-gray-700">Ministry of Consumer Affairs, Food and Public Distribution</h2>
          <h3 className="text-sm font-medium text-gray-600 mb-4">Department of Consumer Affairs - Legal Metrology Division</h3>
          
          <div className="bg-gray-100 py-2 px-4 inline-block rounded-sm mt-2">
            <h4 className="text-lg font-bold text-gray-900">COMPLIANCE INSPECTION REPORT</h4>
          </div>
          
          <div className="mt-6 flex justify-between text-sm text-gray-700 text-left">
            <div>
              <p><strong>Inspection ID:</strong> {id}</p>
              <p><strong>Date & Time:</strong> {new Date(timestamp).toLocaleString()}</p>
            </div>
            <div className="text-right">
              <p><strong>Inspecting Officer:</strong> {officerName}</p>
              <p><strong>System:</strong> PackCheck AI Screening</p>
            </div>
          </div>
        </div>

        {/* Status Banner */}
        <div className={`p-4 mb-8 border rounded-md text-center ${statusColors[status]}`}>
          <p className="text-lg font-bold uppercase">
            OVERALL STATUS: {getStatusLabel(status)}
          </p>
          <p className="text-sm mt-1">Compliance Score: <strong>{score}/100</strong></p>
        </div>

        {/* Product Details Section */}
        <div className="mb-8">
          <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">1. Product Information</h3>
          <table className="w-full text-sm border-collapse border border-gray-300">
            <tbody>
              <tr>
                <th className="border border-gray-300 p-2 text-left bg-gray-50 w-1/3">Product Name</th>
                <td className="border border-gray-300 p-2 font-medium">{productName || 'N/A'}</td>
              </tr>
              <tr>
                <th className="border border-gray-300 p-2 text-left bg-gray-50">Manufacturer/Packer</th>
                <td className="border border-gray-300 p-2">{extractedData?.manufacturer?.value || 'N/A'}</td>
              </tr>
              <tr>
                <th className="border border-gray-300 p-2 text-left bg-gray-50">Net Quantity</th>
                <td className="border border-gray-300 p-2">{extractedData?.netQuantity?.value || 'N/A'}</td>
              </tr>
              <tr>
                <th className="border border-gray-300 p-2 text-left bg-gray-50">MRP</th>
                <td className="border border-gray-300 p-2">{extractedData?.mrp?.value || 'N/A'}</td>
              </tr>
              <tr>
                <th className="border border-gray-300 p-2 text-left bg-gray-50">Packed Date / Batch</th>
                <td className="border border-gray-300 p-2">{extractedData?.packedDate?.value || 'N/A'} / {extractedData?.batchNumber?.value || 'N/A'}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Compliance Checks Section */}
        <div className="mb-8">
          <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">2. Legal Metrology Checks</h3>
          <table className="w-full text-sm border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2 text-left">Rule / Requirement</th>
                <th className="border border-gray-300 p-2 text-center w-24">Result</th>
                <th className="border border-gray-300 p-2 text-left">Remarks</th>
              </tr>
            </thead>
            <tbody>
              {complianceChecks?.map((check, idx) => (
                <tr key={idx}>
                  <td className="border border-gray-300 p-2">
                    <strong>{check.ruleName}</strong>
                    <div className="text-xs text-gray-500">{check.reference}</div>
                  </td>
                  <td className={`border border-gray-300 p-2 text-center font-bold ${
                    check.result === 'PASS' ? 'text-green-600' : 
                    check.result === 'FAIL' ? 'text-red-600' : 'text-amber-600'
                  }`}>
                    {check.result}
                  </td>
                  <td className="border border-gray-300 p-2 text-xs">
                    {check.explanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Violations Section */}
        {violations && violations.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-bold text-red-700 mb-3 border-b border-gray-300 pb-1">3. Detected Violations</h3>
            <div className="space-y-4">
              {violations.map((v, idx) => (
                <div key={idx} className="border border-red-200 bg-red-50 p-4 rounded-sm">
                  <h4 className="font-bold text-red-800 text-sm">{idx + 1}. {v.title}</h4>
                  <p className="text-xs text-gray-700 mt-1"><strong>Reference:</strong> {v.reference}</p>
                  <p className="text-xs text-gray-700 mt-1"><strong>Description:</strong> {v.description}</p>
                  <p className="text-xs text-red-700 mt-2 font-medium"><strong>Action:</strong> {v.recommendedAction}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Evidence Section */}
        <div className="mb-8 print:break-inside-avoid">
          <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">4. Image Evidence</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-40 bg-gray-100 border border-gray-300 flex items-center justify-center text-gray-400 text-sm">
              [Image 1: Front Package]
            </div>
            <div className="h-40 bg-gray-100 border border-gray-300 flex items-center justify-center text-gray-400 text-sm">
              [Image 2: Back Package]
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">Images attached to digital record. Bounding box overlays available in system.</p>
        </div>

        {/* Officer Remarks */}
        <div className="mb-12 print:break-inside-avoid">
          <h3 className="text-lg font-bold text-gray-900 mb-3 border-b border-gray-300 pb-1">5. Officer Remarks</h3>
          <div className="min-h-[80px] p-3 border border-gray-300 text-sm whitespace-pre-wrap">
            {officerRemarks || 'No additional remarks provided.'}
          </div>
        </div>

        {/* Signatures */}
        <div className="flex justify-between items-end mt-16 print:break-inside-avoid">
          <div className="text-center">
            <div className="w-48 border-b border-gray-800 mb-2"></div>
            <p className="text-sm font-medium">System Generated Signature</p>
            <p className="text-xs text-gray-500">PackCheck AI</p>
          </div>
          <div className="text-center">
            <div className="w-48 border-b border-gray-800 mb-2"></div>
            <p className="text-sm font-medium">{officerName}</p>
            <p className="text-xs text-gray-500">Inspecting Officer</p>
          </div>
        </div>

        {/* Footer Disclaimer */}
        <div className="mt-12 pt-4 border-t border-gray-300 text-xs text-center text-gray-500">
          <p>This is an AI-assisted screening report generated by PackCheck AI. Final legal determination and issuance of notices requires verification by an authorized Legal Metrology officer.</p>
          <p className="mt-1 text-gray-400">Report Generated: {new Date().toLocaleString()} | DocRef: {id}</p>
        </div>

      </div>
    </div>
  );
}

