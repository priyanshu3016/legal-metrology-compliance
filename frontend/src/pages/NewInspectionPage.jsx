import React, { useState, useRef, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, X, Zap, Image as ImageIcon, FileText, Calendar, Clock, MapPin, User, Package, AlertCircle } from 'lucide-react';
import { useInspection } from '../context/InspectionContext';
import { useAuth } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import { generateId } from '../utils';

export default function NewInspectionPage() {
  const navigate = useNavigate();
  const { createInspection, setCurrentInspection, setUploadedImages } = useInspection();
  const { user } = useAuth();
  const frontInputRef = useRef(null);
  const backInputRef = useRef(null);
  const sideInputRef = useRef(null);

  const [productName, setProductName] = useState('');
  const [location, setLocation] = useState(user?.location || 'Delhi NCR Region');
  const officerName = user?.name || "Authorized Officer"; 
  
  const today = new Date().toISOString().split('T')[0];
  const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
  
  const [date, setDate] = useState(today);
  const [time, setTime] = useState(now);
  const [referenceNumber, setReferenceNumber] = useState('');
  const [notes, setNotes] = useState('');

  // Independent state for 3 views: Front View, Back View, Side View
  const [viewImages, setViewImages] = useState({
    front: null,
    back: null,
    side: null
  });

  const [dragOverState, setDragOverState] = useState({
    front: false,
    back: false,
    side: false
  });

  const [error, setError] = useState('');

  const handleViewFileChange = (viewKey, fileList) => {
    if (fileList && fileList.length > 0) {
      const selected = fileList[0];
      if (!selected.type.startsWith('image/')) {
        setError('Please upload a valid image file (JPG, PNG, WEBP).');
        return;
      }

      const labelMap = { front: 'Front', back: 'Back', side: 'Side' };
      const fileObj = {
        id: generateId ? generateId() : Math.random().toString(36).substr(2, 9),
        file: selected,
        preview: URL.createObjectURL(selected),
        label: labelMap[viewKey] || 'Package View',
        viewKey: viewKey,
        size: (selected.size / 1024 / 1024).toFixed(2) + ' MB',
        name: selected.name
      };

      setViewImages(prev => ({ ...prev, [viewKey]: fileObj }));
      setError('');
    }
  };

  const handleRemoveView = (viewKey) => {
    setViewImages(prev => ({ ...prev, [viewKey]: null }));
    if (viewKey === 'front' && frontInputRef.current) frontInputRef.current.value = '';
    if (viewKey === 'back' && backInputRef.current) backInputRef.current.value = '';
    if (viewKey === 'side' && sideInputRef.current) sideInputRef.current.value = '';
  };

  const handleDragOver = (e, viewKey) => {
    e.preventDefault();
    setDragOverState(prev => ({ ...prev, [viewKey]: true }));
  };

  const handleDragLeave = (viewKey) => {
    setDragOverState(prev => ({ ...prev, [viewKey]: false }));
  };

  const handleDrop = (e, viewKey) => {
    e.preventDefault();
    setDragOverState(prev => ({ ...prev, [viewKey]: false }));
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleViewFileChange(viewKey, e.dataTransfer.files);
    }
  };

  const files = Object.values(viewImages).filter(Boolean);

  const handleStartInspection = () => {
    if (files.length === 0) {
      setError('Please upload at least one image (Front, Back, or Side view) to proceed.');
      return;
    }

    if (setUploadedImages) {
      setUploadedImages(files);
    }

    // Store metadata for ProcessingPage to use when finalizing the inspection
    sessionStorage.setItem('packcheck_inspect_meta', JSON.stringify({
      productName: productName.trim() || undefined,
      location,
      officer: officerName,
      date,
      time,
      referenceNumber,
      notes
    }));

    navigate('/inspection/processing');
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">New Inspection</h1>

      <div className="space-y-8">
        {/* Section 1: Inspection Details */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <FileText className="w-5 h-5 mr-2 text-blue-600" />
            1. Inspection Details
          </h2>
          <Card className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                  <Package className="w-4 h-4 mr-1 text-blue-600" />
                  Product Name / Commodity Description (Optional)
                </label>
                <Input 
                  type="text"
                  placeholder="e.g. Fortune Sunlite Refined Sunflower Oil 1L (or leave blank to auto-detect)"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Optional: AI will auto-detect commodity title from package text if left blank.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                  <MapPin className="w-4 h-4 mr-1 text-gray-500" />
                  Location
                </label>
                <select 
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                >
                  {['Delhi NCR Region', 'Mumbai West', 'Chennai Central', 'Bangalore Urban', 'Kolkata North', 'Hyderabad', 'Pune Zone', 'Ahmedabad'].map(loc => (
                    <option key={loc} value={loc}>{loc}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                  <User className="w-4 h-4 mr-1 text-gray-500" />
                  Officer Name
                </label>
                <Input 
                  type="text" 
                  value={officerName} 
                  readOnly 
                  className="bg-gray-50 text-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                  <Calendar className="w-4 h-4 mr-1 text-gray-500" />
                  Date
                </label>
                <Input 
                  type="date" 
                  value={date} 
                  onChange={(e) => setDate(e.target.value)} 
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center">
                  <Clock className="w-4 h-4 mr-1 text-gray-500" />
                  Time
                </label>
                <Input 
                  type="time" 
                  value={time} 
                  onChange={(e) => setTime(e.target.value)} 
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference Number (Optional)
                </label>
                <Input 
                  type="text" 
                  value={referenceNumber} 
                  onChange={(e) => setReferenceNumber(e.target.value)} 
                  placeholder="e.g. REF-2023-001"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (Optional)
                </label>
                <textarea 
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                  placeholder="Any additional context about this inspection..."
                />
              </div>
            </div>
          </Card>
        </section>

        {/* Section 2: Upload Product Images */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
            <ImageIcon className="w-5 h-5 mr-2 text-blue-600" />
            2. Upload Product Images
          </h2>
          <Card className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {[
                { key: 'front', label: 'Front View', ref: frontInputRef },
                { key: 'back', label: 'Back View', ref: backInputRef },
                { key: 'side', label: 'Side View', ref: sideInputRef },
              ].map(({ key, label, ref }) => {
                const item = viewImages[key];
                return (
                  <div
                    key={key}
                    className="flex flex-col h-full bg-slate-50/70 rounded-xl border border-slate-200 overflow-hidden"
                  >
                    <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center justify-between">
                      <span className="text-sm font-semibold text-[#212529] uppercase tracking-wider">
                        {label}
                      </span>
                      {item && (
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                          Selected
                        </span>
                      )}
                    </div>

                    <div className="p-4 flex-1 flex flex-col justify-center">
                      {item ? (
                        <div className="relative group w-full flex flex-col items-center">
                          <div className="w-full aspect-[4/3] bg-white rounded-lg border border-slate-200 overflow-hidden relative shadow-xs flex items-center justify-center">
                            <img
                              src={item.preview}
                              alt={label}
                              className="w-full h-full object-contain"
                            />
                            <button
                              type="button"
                              onClick={() => handleRemoveView(key)}
                              className="absolute top-2 right-2 bg-white/90 hover:bg-white text-slate-700 hover:text-red-600 p-1.5 rounded-full shadow-md transition-colors cursor-pointer"
                              title="Remove image"
                              aria-label={`Remove ${label}`}
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          <div className="w-full mt-3 flex items-center justify-between text-xs text-slate-500">
                            <span className="truncate max-w-[140px]" title={item.name}>
                              {item.name}
                            </span>
                            <span className="text-slate-400 shrink-0">{item.size}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => ref.current?.click()}
                            className="mt-2 text-xs font-semibold text-[#8338EC] hover:text-[#7126dc] hover:underline cursor-pointer"
                          >
                            Replace Image
                          </button>
                        </div>
                      ) : (
                        <div
                          onDragOver={(e) => handleDragOver(e, key)}
                          onDragLeave={() => handleDragLeave(key)}
                          onDrop={(e) => handleDrop(e, key)}
                          onClick={() => ref.current?.click()}
                          className={`flex-1 min-h-[190px] border-2 border-dashed rounded-lg p-5 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
                            dragOverState[key]
                              ? 'border-[#8338EC] bg-purple-50/50'
                              : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50/50'
                          }`}
                        >
                          <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-3">
                            <UploadCloud className="w-5 h-5 text-slate-500" />
                          </div>
                          <p className="text-xs font-medium text-slate-700 leading-snug">
                            Drag and drop {label.toLowerCase()} image here,
                            <br />
                            <span className="text-[#8338EC] font-semibold hover:underline">
                              or click to browse
                            </span>
                          </p>
                          <p className="text-[11px] text-slate-400 mt-2 font-medium">
                            JPG, PNG, WEBP
                          </p>
                        </div>
                      )}
                    </div>

                    <input
                      type="file"
                      ref={ref}
                      onChange={(e) => handleViewFileChange(key, e.target.files)}
                      className="hidden"
                      accept="image/jpeg,image/png,image/webp,image/*"
                    />
                  </div>
                );
              })}
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md text-sm border border-red-200">
                {error}
              </div>
            )}
          </Card>
        </section>

        {/* Section 3: Start Inspection */}
        <section className="flex justify-end pt-4">
          <Button 
            onClick={handleStartInspection}
            disabled={files.length === 0}
            className="w-full md:w-auto text-lg py-4 px-8 flex items-center justify-center bg-[#FB5607] hover:bg-[#e04b04] active:bg-[#c54002] text-white rounded-lg shadow-md disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors border-none cursor-pointer"
          >
            <Zap className="w-6 h-6 mr-2" />
            Start AI Inspection
          </Button>
        </section>
      </div>
    </div>
  );
}

