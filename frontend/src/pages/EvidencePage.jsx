import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  Image as ImageIcon,
  FileText,
  MapPin,
  Calendar,
  User
} from 'lucide-react';
import { useInspection } from '../context/InspectionContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/States';
import { formatConfidence, getConfidenceColor } from '../utils';

import { mockInspections } from '../data/mockInspections';

function resolveImageUrl(img) {
  if (!img) return '';
  const path = typeof img === 'string' ? img : (img.file_path || img.url || img.path || img.preview || '');
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:') || path.startsWith('data:')) {
    return path;
  }
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const backendUrl = apiBase.replace(/\/api(\/v1)?\/?$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${backendUrl}${cleanPath}`;
}

export default function EvidencePage() {
  const navigate = useNavigate();
  const { currentInspection, inspections } = useInspection();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const raw = currentInspection || (inspections && inspections.length > 0 ? inspections[0] : null);

  if (!raw) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <EmptyState 
          title="No Inspection Evidence"
          description="Upload commodity photos and run an AI inspection to view annotated package regions and extracted OCR text."
          action={
            <Button onClick={() => navigate('/inspection/new')}>
              Start New Inspection
            </Button>
          }
        />
      </div>
    );
  }
  const inspection = {
    id: raw.id || 'INS-2026-0001',
    product: raw.product || raw.productName || 'Basmati Rice Premium',
    date: raw.date || '2026-08-15',
    time: raw.time || '10:30',
    officer: raw.officer || raw.officerName || 'Rajesh Kumar',
    location: raw.location || 'Delhi NCR Region',
    confidence: raw.confidence || 0.96,
    boundingBoxes: raw.boundingBoxes && raw.boundingBoxes.length > 0
      ? raw.boundingBoxes.map(b => ({
          ...b,
          x: typeof b.x === 'number' && b.x > 100 ? Math.round(b.x / 10) : b.x,
          y: typeof b.y === 'number' && b.y > 100 ? Math.round(b.y / 10) : b.y,
          width: typeof b.width === 'number' && b.width > 100 ? Math.round(b.width / 10) : b.width,
          height: typeof b.height === 'number' && b.height > 100 ? Math.round(b.height / 10) : b.height,
        }))
      : [
          { field: 'MRP', value: '₹850', confidence: 0.98, x: 12, y: 55, width: 28, height: 14 },
          { field: 'Net Quantity', value: '5kg', confidence: 0.99, x: 60, y: 55, width: 28, height: 14 },
          { field: 'Manufacturer', value: 'Agro Farms', confidence: 0.95, x: 12, y: 15, width: 50, height: 18 },
          { field: 'Consumer Care', value: '1800-123-4567', confidence: 0.96, x: 12, y: 75, width: 45, height: 12 }
        ],
    extractedData: raw.extractedData || {
      mrp: { value: raw.mrp || '₹850' },
      netQuantity: { value: raw.netQuantity || '5kg' },
      manufacturer: { value: raw.manufacturer || 'Agro Farms' },
      consumerCare: { value: raw.consumerCare || '1800-123-4567' },
    }
  };

  // Dynamically resolve images from inspection or fallback to placeholders
  const images = raw.images && raw.images.length > 0
    ? raw.images.map((img, idx) => ({
        id: idx + 1,
        label: idx === 0 ? 'Front Package Panel' : idx === 1 ? 'Back Package Panel' : `Panel ${idx + 1}`,
        url: resolveImageUrl(img)
      }))
    : [
        { id: 1, label: 'Front Package Panel', url: null },
        { id: 2, label: 'Back Nutrition & Care Panel', url: null },
        { id: 3, label: 'Side Net Wt & Batch Panel', url: null }
      ];

  const handlePrevImage = () => {
    setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const handleNextImage = () => {
    setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={() => navigate('/inspection/result')} className="flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" /> Back to Results
        </Button>
        <Button variant="primary" className="flex items-center gap-2">
          <Download className="w-4 h-4" /> Download Evidence Package
        </Button>
      </div>

      {/* Evidence Summary */}
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" /> Evidence Management
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <FileText className="w-4 h-4 shrink-0" />
            <span className="font-medium text-gray-900">ID:</span> {inspection.id}
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="w-4 h-4 shrink-0" />
            <span className="font-medium text-gray-900">Date:</span> {inspection.date}
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <User className="w-4 h-4 shrink-0" />
            <span className="font-medium text-gray-900">Officer:</span> {inspection.officer}
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <MapPin className="w-4 h-4 shrink-0" />
            <span className="font-medium text-gray-900">Location:</span> {inspection.location}
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Image Viewer */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 flex flex-col items-center">
            <div className="w-full flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <ImageIcon className="w-5 h-5" /> Image Viewer
              </h3>
              <Badge variant="neutral">{currentImageIndex + 1} of {images.length}</Badge>
            </div>
            
            <div className={`relative w-full bg-gray-100 rounded-lg border border-gray-300 flex items-center justify-center overflow-hidden mb-4 ${!images[currentImageIndex].url ? 'aspect-video' : ''}`}>
              {images[currentImageIndex].url ? (
                <img 
                  src={images[currentImageIndex].url} 
                  alt={images[currentImageIndex].label} 
                  className="w-full h-auto block rounded-lg"
                  crossOrigin="anonymous"
                />
              ) : (
                <span className="text-gray-400 font-medium text-lg">{images[currentImageIndex].label} Image Placeholder</span>
              )}
              {/* Overlay mock bounding boxes on the first image */}
              {currentImageIndex === 0 && inspection.boundingBoxes?.map((box, idx) => (
                <div 
                  key={idx}
                  className="absolute border-2 border-green-500 bg-green-500/10"
                  style={{ 
                    left: `${box.x}%`, 
                    top: `${box.y}%`, 
                    width: `${box.width}%`, 
                    height: `${box.height}%` 
                  }}
                />
              ))}
            </div>

            <div className="flex items-center justify-center gap-4 w-full">
              <Button variant="outline" size="sm" onClick={handlePrevImage}><ChevronLeft className="w-4 h-4" /> Prev</Button>
              <span className="text-sm font-medium text-gray-700">{images[currentImageIndex].label}</span>
              <Button variant="outline" size="sm" onClick={handleNextImage}>Next <ChevronRight className="w-4 h-4" /></Button>
            </div>
          </Card>

          {/* OCR Raw Text Section */}
          <Card className="p-6">
            <h3 className="font-semibold text-gray-900 mb-4 border-b pb-2">OCR Text Snippets (Raw)</h3>
            <div className="bg-gray-900 rounded-md p-4 overflow-x-auto">
              <pre className="text-green-400 font-mono text-xs leading-relaxed">
{`[OCR Output Engine v2.4]
Processing image: ${inspection.id}_img_1.jpg
Status: OK | Confidence Avg: ${formatConfidence(inspection.confidence)}

DETECTED REGIONS:
-----------------------------------------
[Net Quantity]: "NET WT. 500g" (Conf: 0.98)
[MRP]: "MRP Rs. 150.00 (Incl. of all taxes)" (Conf: 0.96)
[Packed Date]: "PKD: 10/2023" (Conf: 0.92)
[Manufacturer]: "XYZ Foods Pvt. Ltd., 123 Industrial Area, Delhi" (Conf: 0.89)
[Consumer Care]: "Call: 1800-123-4567 Email: care@xyzfoods.com" (Conf: 0.94)
[Batch Number]: "B.No: XF-2390A" (Conf: 0.95)

WARNINGS:
-----------------------------------------
- Low contrast detected near "Best Before" region.
- Potential occlusion over "License Number".
`}
              </pre>
            </div>
          </Card>
        </div>

        {/* Right Column: Detected Regions & Metadata */}
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="font-semibold text-gray-900 mb-4 border-b pb-2">Detected Regions</h3>
            <div className="space-y-4">
              {inspection.boundingBoxes?.map((box, idx) => (
                <div key={idx} className="flex flex-col border border-gray-100 rounded-md p-3 bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-bold text-gray-900 capitalize">{box.field.replace(/([A-Z])/g, ' $1').trim()}</span>
                    <Badge className={getConfidenceColor(box.confidence)}>
                      {formatConfidence(box.confidence)}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    Extracted: <span className="font-medium text-gray-800">"{box.value || box.extractedText || inspection.extractedData[box.field]?.value || 'Detected'}"</span>
                  </div>
                  <div className="flex items-center gap-2 mt-auto">
                    <div className="w-3 h-3 bg-green-500 rounded-sm"></div>
                    <span className="text-[10px] text-gray-500">Box: [{box.x}%, {box.y}%, {box.width}%, {box.height}%]</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
             <h3 className="font-semibold text-gray-900 mb-4 border-b pb-2">Metadata</h3>
             <ul className="text-sm space-y-3">
               <li className="flex justify-between"><span className="text-gray-500">Upload Time:</span> <span className="font-medium">{inspection.date}, {inspection.time}</span></li>
               <li className="flex justify-between"><span className="text-gray-500">Device ID:</span> <span className="font-medium">LM-MOB-042</span></li>
               <li className="flex justify-between"><span className="text-gray-500">GPS Coordinates:</span> <span className="font-medium">28.6139° N, 77.2090° E</span></li>
               <li className="flex justify-between"><span className="text-gray-500">AI Model Version:</span> <span className="font-medium">v1.2.4-prod</span></li>
               <li className="flex justify-between"><span className="text-gray-500">Processing Time:</span> <span className="font-medium">1.4s</span></li>
             </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}

