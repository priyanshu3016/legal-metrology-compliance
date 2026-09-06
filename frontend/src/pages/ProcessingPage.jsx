import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';
import { InspectionContext } from '../context/InspectionContext';
import Card from '../components/ui/Card';

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
  const { currentInspection, uploadedImages } = useContext(InspectionContext) || { currentInspection: null, uploadedImages: [] };
  
  const [currentStepIndex, setCurrentStepIndex] = useState(3); // Start with step 4 in progress (index 3)
  const [progress, setProgress] = useState(50);
  const [statusText, setStatusText] = useState('AI Analysis in Progress...');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!currentInspection) {
      navigate('/inspection/new');
      return;
    }

    const timer1 = setTimeout(() => {
      setCurrentStepIndex(4); // Step 5 in progress
      setProgress(66);
    }, 2000);

    const timer2 = setTimeout(() => {
      setCurrentStepIndex(5); // Step 6 in progress
      setProgress(83);
      setStatusText('Finalizing Report...');
    }, 3500);

    const timer3 = setTimeout(() => {
      setCurrentStepIndex(6); // All done
      setProgress(100);
      setStatusText('Complete!');
      setIsComplete(true);
    }, 5000);

    const timer4 = setTimeout(() => {
      navigate('/inspection/result');
    }, 5500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [currentInspection, navigate]);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{statusText}</h1>
        <p className="text-gray-500">This may take a few seconds. Please do not close this window.</p>
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
            const isPending = index > currentStepIndex;

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
      </Card>
    </div>
  );
}

