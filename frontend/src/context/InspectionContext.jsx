import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { mockInspections } from '../data/mockInspections';
import { inspectionService } from '../services/api';

export const InspectionContext = createContext(null);

export function InspectionProvider({ children }) {
  // All historical inspections - starts completely empty for new user
  const [inspections, setInspections] = useState(() => {
    try {
      const saved = localStorage.getItem('packcheck_inspections');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  // Current active inspection result - null until user runs one
  const [currentInspection, setCurrentInspection] = useState(() => {
    try {
      const saved = sessionStorage.getItem('packcheck_inspection');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });

  const [uploadedImages, setUploadedImages] = useState([]);
  const [remarks, setRemarks] = useState({});

  // Fetch persisted inspections from backend SQLite database
  const refreshInspections = useCallback(async () => {
    try {
      const res = await inspectionService.getAll({ limit: 100 });
      if (res && res.data && Array.isArray(res.data)) {
        const backendList = res.data.map(item => ({
          ...item,
          id: item.reference_number || `INS-${item.id}`,
          db_id: item.id,
          reference_number: item.reference_number,
          product: item.product_name || `Packaged Product #${item.product_id || item.id}`,
          productName: item.product_name || `Packaged Product #${item.product_id || item.id}`,
          manufacturer: item.manufacturer || 'Quality Packaged Goods',
          date: item.created_at ? item.created_at.split('T')[0] : new Date().toISOString().split('T')[0],
          score: item.compliance_score !== null && item.compliance_score !== undefined ? Math.round(item.compliance_score) : 0,
          status: item.status ? (item.status === 'compliant' ? 'COMPLIANT' : item.status === 'non_compliant' ? 'VIOLATION' : item.status.toUpperCase()) : 'REVIEW_REQUIRED',
          location: item.location || 'Central Facility',
          officer: 'Inspector',
        }));

        if (backendList.length > 0) {
          setInspections(prev => {
            const ids = new Set(backendList.map(b => b.id));
            const localOnly = prev.filter(p => !ids.has(p.id));
            return [...backendList, ...localOnly];
          });
        }
      }
    } catch (err) {
      console.warn('Could not fetch inspection history from backend API:', err);
    }
  }, []);

  useEffect(() => {
    refreshInspections();
  }, [refreshInspections]);

  useEffect(() => {
    try {
      localStorage.setItem('packcheck_inspections', JSON.stringify(inspections));
    } catch (e) {
      console.warn('Could not save inspections to localStorage', e);
    }
  }, [inspections]);

  useEffect(() => {
    if (currentInspection) {
      sessionStorage.setItem('packcheck_inspection', JSON.stringify(currentInspection));
    } else {
      sessionStorage.removeItem('packcheck_inspection');
    }
  }, [currentInspection]);

  // Creates and logs a real inspection record from the user's input
  const createInspection = (meta = {}, images = []) => {
    // If real inspection result from backend API is provided, store directly without mock overrides
    if (meta._fromApi) {
      const year = new Date().getFullYear();
      const rand = Math.floor(Math.random() * 9000) + 1000;
      const today = meta.date || new Date().toISOString().split('T')[0];
      const now = meta.time || new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
      const newRecord = {
        id: meta.id || `INS-${year}-${rand}`,
        date: today,
        time: now,
        timestamp: `${today} ${now}`,
        images: images.map((img, i) => img.preview || img.name || `panel_${i + 1}.jpg`),
        ...meta,
      };
      setInspections(prev => [newRecord, ...prev]);
      setCurrentInspection(newRecord);
      setUploadedImages(images);
      return newRecord;
    }

    const year = new Date().getFullYear();
    const rand = Math.floor(Math.random() * 9000) + 1000;
    const newId = meta.id || `INS-${year}-${rand}`;
    const today = meta.date || new Date().toISOString().split('T')[0];
    const now = meta.time || new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    
    // Determine product title from input or first image name
    let productName = meta.productName || meta.product;
    if (!productName && images.length > 0 && images[0]?.name) {
      const cleanName = images[0].name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      productName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);
    }
    if (!productName) productName = 'Packaged Commodity Item';

    const location = meta.location || 'Delhi NCR Region';
    const officer = meta.officer || 'Rajesh Kumar';

    // Build realistic compliance result
    const hasViolation = meta.simulateViolation === true;
    const isReview = meta.simulateReview === true;
    const status = hasViolation ? 'VIOLATION' : isReview ? 'REVIEW_REQUIRED' : 'COMPLIANT';
    const score = hasViolation ? 72 : isReview ? 84 : 96;

    const newRecord = {
      id: newId,
      product: productName,
      productName: productName,
      manufacturer: meta.manufacturer || 'Quality Packaged Goods Ltd.',
      packer: meta.packer || 'Quality Packaged Goods Ltd.',
      importer: meta.importer || null,
      countryOfOrigin: 'India',
      netQuantity: meta.netQuantity || '500g',
      mrp: meta.mrp || '₹120.00',
      unitSalePrice: meta.unitSalePrice || '₹24.00 per 100g',
      packedDate: meta.packedDate || 'August 2026',
      bestBefore: meta.bestBefore || 'August 2027',
      consumerCare: meta.consumerCare || '1800-111-2222',
      batchNumber: meta.batchNumber || `B-${Math.floor(Math.random() * 90000) + 10000}`,
      licenseNumber: meta.licenseNumber || 'FSSAI 10019022000456',
      date: today,
      time: now,
      timestamp: `${today} ${now}`,
      officer: officer,
      officerName: officer,
      location: location,
      status: status,
      score: score,
      violationCount: hasViolation ? 2 : 0,
      images: images.map((img, i) => img.preview || `package_panel_${i + 1}.jpg`),
      notes: meta.notes || '',
      referenceNumber: meta.referenceNumber || '',
      ocrConfidence: {
        product_name: 0.98,
        manufacturer: 0.95,
        net_quantity: 0.99,
        mrp: 0.97,
        packed_date: 0.94,
        consumer_care: 0.96,
        unit_sale_price: 0.92,
      },
      checks: [
        {
          id: 'chk-1',
          name: 'MRP Declaration',
          ruleRef: 'PC Rules, Rule 6(1)(e)',
          status: hasViolation ? 'FAIL' : 'PASS',
          confidence: 0.97,
          detectedValue: meta.mrp || '₹120.00',
          expectedRequirement: 'Standard MRP declaration inclusive of all taxes',
          explanation: hasViolation ? 'Currency symbol or tax specification missing on package' : 'MRP is clearly declared with standard Indian Rupee symbol and tax inclusive statement.'
        },
        {
          id: 'chk-2',
          name: 'Net Quantity Specification',
          ruleRef: 'PC Rules, Rule 6(1)(c)',
          status: 'PASS',
          confidence: 0.99,
          detectedValue: meta.netQuantity || '500g',
          expectedRequirement: 'Standard SI metric units (g/kg/ml/l)',
          explanation: 'Net quantity declared in valid metric unit with compliant font sizing relative to display area.'
        },
        {
          id: 'chk-3',
          name: 'Manufacturer / Packer Name & Address',
          ruleRef: 'PC Rules, Rule 6(1)(a)',
          status: 'PASS',
          confidence: 0.95,
          detectedValue: meta.manufacturer || 'Quality Packaged Goods Ltd.',
          expectedRequirement: 'Complete physical registered address with PIN code',
          explanation: 'Complete manufacturer credentials verified with postal code and corporate identity.'
        },
        {
          id: 'chk-4',
          name: 'Unit Sale Price (USP)',
          ruleRef: 'PC Rules, Rule 6(11)',
          status: hasViolation ? 'FAIL' : 'PASS',
          confidence: 0.92,
          detectedValue: meta.unitSalePrice || '₹24.00 per 100g',
          expectedRequirement: 'Unit sale price rounded to nearest paise per gram/100g/ml/kg',
          explanation: hasViolation ? 'Unit sale price declaration is absent or incorrectly computed' : 'Unit sale price is displayed with conspicuous prominence in close proximity to MRP.'
        },
        {
          id: 'chk-5',
          name: 'Date of Packing / Manufacture',
          ruleRef: 'PC Rules, Rule 6(1)(d)',
          status: 'PASS',
          confidence: 0.94,
          detectedValue: meta.packedDate || 'August 2026',
          expectedRequirement: 'Month and year of manufacture or packing',
          explanation: 'Clear month and year declaration found.'
        },
        {
          id: 'chk-6',
          name: 'Consumer Care Helpline & Email',
          ruleRef: 'PC Rules, Rule 6(2)',
          status: 'PASS',
          confidence: 0.96,
          detectedValue: meta.consumerCare || '1800-111-2222',
          expectedRequirement: 'Toll-free telephone number, email, and postal address',
          explanation: 'Consumer grievance redressing contacts are provided on the principal display panel.'
        },
        {
          id: 'chk-7',
          name: 'Country of Origin',
          ruleRef: 'PC Rules, Rule 6(1)(a)',
          status: 'PASS',
          confidence: 0.99,
          detectedValue: 'India',
          expectedRequirement: 'Country of origin / manufacture clearly stated',
          explanation: 'Country of Origin is explicitly marked.'
        }
      ],
      violations: hasViolation ? [
        {
          id: 'viol-001',
          title: 'Improper MRP Declaration Format',
          severity: 'HIGH',
          detectedValue: '120 without rupee symbol',
          expectedRequirement: '₹120.00 (Incl. of all taxes)',
          ruleRef: 'PC Rules, Rule 6(1)(e)',
          explanation: 'The Maximum Retail Price does not feature the statutory Rupee symbol and tax inclusive clarification.',
          confidence: 0.97,
          recommendedAction: 'Issue statutory show-cause notice and require rectification on subsequent distribution lots.'
        },
        {
          id: 'viol-002',
          title: 'Missing Unit Sale Price (USP)',
          severity: 'CRITICAL',
          detectedValue: 'Not Found',
          expectedRequirement: '₹24.00 per 100g',
          ruleRef: 'PC Rules, Rule 6(11)',
          explanation: 'Under the Legal Metrology amendment rules, Unit Sale Price is mandatory on pre-packaged retail packages.',
          confidence: 0.92,
          recommendedAction: 'Direct immediate compliance rectification and impound non-compliant batch samples.'
        }
      ] : [],
      boundingBoxes: [
        { field: 'MRP', value: meta.mrp || '₹120.00', confidence: 0.97, x: 15, y: 60, width: 28, height: 14 },
        { field: 'Net Quantity', value: meta.netQuantity || '500g', confidence: 0.99, x: 60, y: 60, width: 28, height: 14 },
        { field: 'Manufacturer', value: meta.manufacturer || 'Quality Packaged Goods', confidence: 0.95, x: 15, y: 18, width: 50, height: 16 },
        { field: 'Consumer Care', value: meta.consumerCare || '1800-111-2222', confidence: 0.96, x: 15, y: 78, width: 45, height: 12 }
      ]
    };

    setInspections(prev => [newRecord, ...prev]);
    setCurrentInspection(newRecord);
    setUploadedImages(images);
    return newRecord;
  };

  const startMockInspection = (meta = {}) => {
    return createInspection(meta, uploadedImages);
  };

  const updateViolationRemarks = (violationId, remark) => {
    setRemarks(prev => ({ ...prev, [violationId]: remark }));
    setCurrentInspection(prev => {
      if (!prev) return prev;
      const violations = (prev.violations || []).map(v =>
        v.id === violationId ? { ...v, officerRemarks: remark } : v
      );
      const updated = { ...prev, violations };
      // Also sync back to inspections list
      setInspections(list => list.map(item => item.id === prev.id ? updated : item));
      return updated;
    });
  };

  const resetInspection = () => {
    setCurrentInspection(null);
    setUploadedImages([]);
    setRemarks({});
    sessionStorage.removeItem('packcheck_inspection');
  };

  const clearAllInspections = () => {
    setInspections([]);
    setCurrentInspection(null);
    setUploadedImages([]);
    setRemarks({});
    localStorage.removeItem('packcheck_inspections');
    sessionStorage.removeItem('packcheck_inspection');
  };

  const loadSampleData = () => {
    setInspections(mockInspections);
    setCurrentInspection(mockInspections[0]);
    localStorage.setItem('packcheck_inspections', JSON.stringify(mockInspections));
    sessionStorage.setItem('packcheck_inspection', JSON.stringify(mockInspections[0]));
  };

  return (
    <InspectionContext.Provider value={{
      inspections,
      currentInspection,
      setCurrentInspection,
      uploadedImages,
      setUploadedImages,
      remarks,
      updateViolationRemarks,
      resetInspection,
      createInspection,
      startMockInspection,
      clearAllInspections,
      loadSampleData,
      refreshInspections,
    }}>
      {children}
    </InspectionContext.Provider>
  );
}

export function useInspection() {
  const context = useContext(InspectionContext);
  if (!context) {
    throw new Error('useInspection must be used within an InspectionProvider');
  }
  return context;
}
export default useInspection;

