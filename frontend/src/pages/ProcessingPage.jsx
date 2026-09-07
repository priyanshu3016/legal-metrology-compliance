import React, { useEffect, useState, useContext, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react';
import { InspectionContext } from '../context/InspectionContext';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { inspectService } from '../services/api';

const STEPS = [
  { id: 1, label: 'Image Received' },
  { id: 2, label: 'Image Quality Analysis' },
  { id: 3, label: 'OCR Text Extraction' },
  { id: 4, label: 'Declaration Detection' },
  { id: 5, label: 'Legal Metrology Validation' },
  { id: 6, label: 'Compliance Report Generation' }
];

export default function ProcessingPage() {
  const navigate = useNavigate();
  const { uploadedImages, createInspection } = useContext(InspectionContext) || { uploadedImages: [], createInspection: () => {} };
  
  const [currentStepIndex, setCurrentStepIndex] = useState(1);
  const [progress, setProgress] = useState(20);
  const [statusText, setStatusText] = useState('AI Analysis in Progress...');
  const [isComplete, setIsComplete] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const hasExecutedRef = useRef(false);

  useEffect(() => {
    if (!uploadedImages || uploadedImages.length === 0) {
      navigate('/inspection/new');
      return;
    }

    if (hasExecutedRef.current) return;
    hasExecutedRef.current = true;

    // Progression timer while waiting for backend
    const timerStep2 = setTimeout(() => {
      setCurrentStepIndex(2);
      setProgress(40);
      setStatusText('Extracting Text via PaddleOCR...');
    }, 1200);

    const timerStep3 = setTimeout(() => {
      setCurrentStepIndex(3);
      setProgress(60);
      setStatusText('Detecting Mandatory Declarations...');
    }, 2800);

    const timerStep4 = setTimeout(() => {
      setCurrentStepIndex(4);
      setProgress(75);
      setStatusText('Validating Legal Metrology Rules...');
    }, 4500);

    // Build FormData from uploadedImages
    const formData = new FormData();
    let frontFile = null;
    let backFile = null;
    let sideFile = null;

    for (const img of uploadedImages) {
      if (img.viewKey === 'front') frontFile = img.file;
      else if (img.viewKey === 'back') backFile = img.file;
      else if (img.viewKey === 'side') sideFile = img.file;
    }

    // Fallbacks if viewKey not set
    if (!frontFile && uploadedImages[0]?.file) frontFile = uploadedImages[0].file;
    if (!backFile && uploadedImages[1]?.file) backFile = uploadedImages[1].file;
    if (!sideFile && uploadedImages[2]?.file) sideFile = uploadedImages[2].file;

    // Ensure backFile is populated
    if (!backFile && frontFile) backFile = frontFile;

    formData.append('front_image', frontFile);
    formData.append('back_image', backFile);
    if (sideFile) {
      formData.append('side_image', sideFile);
    }

    // Call backend single-shot endpoint
    inspectService.run(formData)
      .then((response) => {
        const data = response.data;
        clearTimeout(timerStep2);
        clearTimeout(timerStep3);
        clearTimeout(timerStep4);

        setCurrentStepIndex(5);
        setProgress(90);
        setStatusText('Finalizing Report...');

        const metaStr = sessionStorage.getItem('packcheck_inspect_meta');
        const meta = metaStr ? JSON.parse(metaStr) : {};

        setTimeout(() => {
          setCurrentStepIndex(6);
          setProgress(100);
          setStatusText('Complete!');
          setIsComplete(true);

          createInspection(
            {
              _fromApi: true,
              id: data.id,
              status: data.status,
              score: data.score,
              confidence: data.confidence || 0.95,
              product: data.product || meta.productName,
              productName: data.productName || data.product || meta.productName,
              manufacturer: data.manufacturer || '',
              packer: data.manufacturer || '',
              netQuantity: data.netQuantity || '',
              mrp: data.mrp || '',
              unitSalePrice: data.unitSalePrice || '',
              packedDate: data.packedDate || '',
              bestBefore: data.bestBefore || '',
              consumerCare: data.consumerCare || '',
              countryOfOrigin: data.countryOfOrigin || 'India',
              extractedData: data.extractedData,
              ocrConfidence: data.ocrConfidence,
              checks: data.checks,
              complianceChecks: data.complianceChecks || data.checks,
              violations: data.violations || [],
              boundingBoxes: data.boundingBoxes || [],
              disclaimers: data.disclaimers || [],
              processingTimeMs: data.processingTimeMs,
              ...meta,
            },
            uploadedImages
          );

          setTimeout(() => {
            navigate('/inspection/result');
          }, 800);
        }, 600);
      })
      .catch((err) => {
        clearTimeout(timerStep2);
        clearTimeout(timerStep3);
        clearTimeout(timerStep4);
        console.error('Inspection API failed:', err);
        const errMsg = err.response?.data?.detail?.message
          || (typeof err.response?.data?.detail === 'string' ? err.response?.data?.detail : null)
          || err.message
          || 'Failed to connect to backend inspection engine.';
        setErrorMessage(errMsg);
      });

    return () => {
      clearTimeout(timerStep2);
      clearTimeout(timerStep3);
      clearTimeout(timerStep4);
    };
  }, [uploadedImages, navigate, createInspection]);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{errorMessage ? 'Inspection Error' : statusText}</h1>
        <p className="text-gray-500">
          {errorMessage
            ? 'An error occurred during AI OCR or legal compliance processing.'
            : 'This may take a few seconds. Please do not close this window.'}
        </p>
      </div>

      <Card className="w-full max-w-2xl p-8 shadow-xl">
        {/* Images Thumbnail Row */}
        {uploadedImages && uploadedImages.length > 0 && (
          <div className="flex justify-center gap-2 mb-10 overflow-x-auto py-2">
            {uploadedImages.map((img, idx) => (
              <div key={img.id || idx} className="w-16 h-16 rounded-md overflow-hidden border border-gray-200 shadow-sm flex-shrink-0">
                <img src={img.preview} alt={`Upload ${idx}`} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        )}

        {errorMessage ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
            <p className="text-red-800 font-semibold">{errorMessage}</p>
            <div className="flex justify-center gap-3 pt-2">
              <Button variant="outline" onClick={() => navigate('/inspection/new')}>
                Back to Upload
              </Button>
              <Button onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </div>
        ) : (
          <>
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-10 overflow-hidden">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            {/* Steps List */}
            <div className="space-y-4 max-w-md mx-auto">
              {STEPS.map((step, index) => {
                const isDone = index < currentStepIndex;
                const isInProgress = index === currentStepIndex && !isComplete;

                return (
                  <div 
                    key={step.id} 
                    className={`flex items-center p-3 rounded-lg transition-colors ${
                      isInProgress ? 'bg-blue-50 border border-blue-100' : 'bg-transparent'
                    }`}
                  >
                    <div className="mr-4">
                      {isDone ? (
                        <CheckCircle className="w-6 h-6 text-green-500" />
                      ) : isInProgress ? (
                        <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                      ) : (
                        <Circle className="w-6 h-6 text-gray-300" />
                      )}
                    </div>
                    
                    <div className="flex-1 text-left">
                      <span className={`font-medium ${
                        isDone ? 'text-gray-900' : 
                        isInProgress ? 'text-blue-700' : 
                        'text-gray-400'
                      }`}>
                        Step {step.id}: {step.label}
                      </span>
                    </div>
                    
                    <div className="text-sm font-semibold">
                      {isDone ? (
                        <span className="text-green-600">DONE</span>
                      ) : isInProgress ? (
                        <span className="text-blue-600">IN PROGRESS</span>
                      ) : (
                        <span className="text-gray-400">PENDING</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}


