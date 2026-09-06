import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  Check, 
  ArrowRight, 
  FileText, 
  Search, 
  Scan, 
  CheckCircle, 
  ClipboardList, 
  History, 
  Menu, 
  X
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import mountainBg from '../assets/mountain-bg.jpg';

export default function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isLoggingOut, setIsLoggingOut } = useAuth();

  useEffect(() => {
    if (isLoggingOut && setIsLoggingOut) {
      setIsLoggingOut(false);
    }
  }, [isLoggingOut, setIsLoggingOut]);

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };


  return (
    <div className="min-h-screen bg-[#212529] text-[#212529] flex flex-col font-sans antialiased selection:bg-[#8338EC] selection:text-white">
      {/* ==================================================
          HEADER
          Full viewport width:
          Logo near far left.
          Home → How It Works → Key Features → Login near far right.
          ================================================== */}
      <header className="sticky top-0 z-50 bg-[#212529] text-white h-16 w-full">
        <div className="w-full px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
          
          {/* FAR LEFT: PackCheck AI Logo + Name */}
          <Link to="/" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded bg-[#8338EC] flex items-center justify-center text-white shadow-xs">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-white leading-tight">
                PackCheck <span className="text-[#8338EC]">AI</span>
              </span>
              <span className="text-[10px] font-medium tracking-wider text-slate-400 uppercase">
                Legal Metrology Platform
              </span>
            </div>
          </Link>

          {/* FAR RIGHT: Home → How It Works → Key Features → Demonstration → Login */}
          <div className="hidden md:flex items-center gap-6 lg:gap-7">
            <button 
              onClick={() => scrollToSection('hero-section')} 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer py-1"
            >
              Home
            </button>
            <button 
              onClick={() => scrollToSection('how-it-works')} 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer py-1"
            >
              How It Works
            </button>
            <button 
              onClick={() => scrollToSection('key-features')} 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer py-1"
            >
              Key Features
            </button>
            <button 
              onClick={() => scrollToSection('example-compliance-check')} 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer py-1"
            >
              Demonstration
            </button>

            {/* Login CTA in Orange #FB5607 */}
            <Button 
              onClick={() => navigate('/login')} 
              className="bg-[#FB5607] hover:bg-[#e04b04] active:bg-[#c54002] text-white font-semibold text-sm px-5 py-2 rounded-md shadow-xs transition-colors cursor-pointer border-none ml-2"
            >
              Login
            </Button>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center gap-2">
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)} 
              className="p-1.5 rounded text-slate-300 hover:text-white hover:bg-slate-800 cursor-pointer"
              aria-label="Toggle Navigation"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-slate-800 bg-[#212529] px-4 py-3 space-y-2 text-white shadow-xl">
            <button 
              onClick={() => scrollToSection('hero-section')} 
              className="block w-full text-left py-2 text-sm font-medium text-slate-200 hover:text-[#8338EC] cursor-pointer"
            >
              Home
            </button>
            <button 
              onClick={() => scrollToSection('how-it-works')} 
              className="block w-full text-left py-2 text-sm font-medium text-slate-200 hover:text-[#8338EC] cursor-pointer"
            >
              How It Works
            </button>
            <button 
              onClick={() => scrollToSection('key-features')} 
              className="block w-full text-left py-2 text-sm font-medium text-slate-200 hover:text-[#8338EC] cursor-pointer"
            >
              Key Features
            </button>
            <button 
              onClick={() => scrollToSection('example-compliance-check')} 
              className="block w-full text-left py-2 text-sm font-medium text-slate-200 hover:text-[#8338EC] cursor-pointer"
            >
              Demonstration
            </button>
            <div className="pt-2 border-t border-slate-700">
              <Button 
                onClick={() => navigate('/login')} 
                className="w-full justify-center text-sm py-2 rounded-md cursor-pointer bg-[#FB5607] hover:bg-[#e04b04] text-white font-semibold"
              >
                Login
              </Button>
            </div>
          </div>
        )}
      </header>

      <main className="flex-1 flex flex-col">
        <section 
          id="hero-section"
          className="relative overflow-hidden bg-[#212529] text-white min-h-[calc(100vh-4rem)] flex flex-col justify-center py-16 lg:py-24 scroll-mt-16"
        >
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none"
            style={{ backgroundImage: `url(${mountainBg})` }}
          />

          <div className="absolute inset-0 bg-[#212529]/65 pointer-events-none" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#212529]/80 via-transparent to-[#212529] pointer-events-none" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_30%,_#212529_95%)] pointer-events-none" />
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-[#8338EC]/25 rounded-full blur-[120px] pointer-events-none" />
          <div className="absolute -bottom-20 right-1/4 w-[400px] h-[200px] bg-[#FB5607]/10 rounded-full blur-[90px] pointer-events-none" />

          <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center my-auto">
            <div className="space-y-6 flex flex-col items-center">
              <div>
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-[#E9ECEF] bg-[#212529]/85 border border-slate-700 px-3 py-1 rounded shadow-xs">
                  LEGAL METROLOGY COMPLIANCE PLATFORM
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-[1.2] max-w-3xl drop-shadow-md">
                Legal Metrology <br />
                Compliance, Made Simple.
              </h1>

              <p className="text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed font-normal drop-shadow-sm">
                Check packaged commodities, identify potential compliance issues and manage inspection records in one place.
              </p>

              <div className="pt-2">
                <Button 
                  onClick={() => navigate('/login')}
                  className="bg-[#FB5607] hover:bg-[#e04b04] active:bg-[#c54002] text-white font-semibold text-sm px-8 py-3.5 rounded-md shadow-lg shadow-[#FB5607]/25 transition-colors cursor-pointer border-none"
                >
                  START AN INSPECTION
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        </section>

        <section 
          id="how-it-works" 
          className="relative overflow-hidden bg-[#212529] min-h-[calc(100vh-4rem)] flex flex-col justify-center py-12 lg:py-16 text-[#212529] scroll-mt-16"
        >
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none opacity-20"
            style={{ backgroundImage: `url(${mountainBg})` }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#212529] via-[#212529]/95 to-[#212529] pointer-events-none" />
          <div className="absolute -top-20 left-1/3 w-[500px] h-[300px] bg-[#8338EC]/20 rounded-full blur-[100px] pointer-events-none" />

          <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div className="text-center max-w-2xl mx-auto mb-10">
              <h2 className="text-xs font-bold uppercase tracking-widest text-[#8338EC] mb-2">
                WORKFLOW
              </h2>
              <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                HOW IT WORKS
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
              
              <div className="bg-white border border-slate-300 p-5 rounded relative flex flex-col shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-mono font-bold text-[#8338EC]">01</span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Step 1</span>
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Add Product</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Upload clear images of the packaged commodity and provide basic inspection details.
                </p>
              </div>

              <div className="bg-white border border-slate-300 p-5 rounded relative flex flex-col shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-mono font-bold text-[#8338EC]">02</span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Step 2</span>
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Extract Information</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  AI reads the package and extracts key declarations such as MRP, net quantity, manufacturer and dates.
                </p>
              </div>

              <div className="bg-white border border-slate-300 p-5 rounded relative flex flex-col shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-mono font-bold text-[#8338EC]">03</span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Step 3</span>
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Check Compliance</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Screen against Legal Metrology Packaged Commodities rules to identify potential violations.
                </p>
              </div>

              <div className="bg-white border border-slate-300 p-5 rounded relative flex flex-col shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-mono font-bold text-[#8338EC]">04</span>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Step 4</span>
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Generate Report</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Review findings, export official inspection reports and maintain audit history.
                </p>
              </div>

            </div>
          </div>
        </section>

        <section 
          id="key-features" 
          className="relative overflow-hidden bg-[#212529] min-h-[calc(100vh-4rem)] flex flex-col justify-center py-12 lg:py-16 text-[#212529] scroll-mt-16"
        >
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none opacity-20"
            style={{ backgroundImage: `url(${mountainBg})` }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#212529] via-[#212529]/95 to-[#212529] pointer-events-none" />
          <div className="absolute top-1/4 right-1/4 w-[550px] h-[300px] bg-[#8338EC]/20 rounded-full blur-[110px] pointer-events-none" />

          <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div className="max-w-2xl mb-10">
              <h2 className="text-xs font-bold uppercase tracking-widest text-[#8338EC] mb-2">
                SYSTEM CAPABILITIES
              </h2>
              <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                KEY FEATURES
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              <div className="border border-slate-300 rounded p-6 bg-white shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#8338EC]">FEATURE 01</span>
                  <Scan className="w-5 h-5 text-[#FB5607]" />
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Package Inspection</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Capture and analyze packaged commodity information.
                </p>
              </div>

              <div className="border border-slate-300 rounded p-6 bg-white shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#8338EC]">FEATURE 02</span>
                  <CheckCircle className="w-5 h-5 text-[#8338EC]" />
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Rule-Based Compliance</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Evaluate packaging against Legal Metrology guidelines.
                </p>
              </div>

              <div className="border border-slate-300 rounded p-6 bg-white shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#8338EC]">FEATURE 03</span>
                  <ClipboardList className="w-5 h-5 text-[#FB5607]" />
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Inspection Summary</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Clear breakdown of compliant areas and potential issues.
                </p>
              </div>

              <div className="border border-slate-300 rounded p-6 bg-white shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#8338EC]">FEATURE 04</span>
                  <FileText className="w-5 h-5 text-[#8338EC]" />
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Digital Documentation</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Generate official inspection records and reports.
                </p>
              </div>

              <div className="border border-slate-300 rounded p-6 bg-white shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#8338EC]">FEATURE 05</span>
                  <History className="w-5 h-5 text-[#FB5607]" />
                </div>
                <h4 className="text-base font-bold text-[#212529] mb-2">Audit History</h4>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Keep structured history of conducted inspections.
                </p>
              </div>

            </div>
          </div>
        </section>

        <section 
          id="example-compliance-check" 
          className="relative overflow-hidden bg-[#212529] min-h-[calc(100vh-4rem)] flex flex-col justify-center py-12 lg:py-16 text-[#212529] scroll-mt-16"
        >
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none opacity-10"
            style={{ backgroundImage: `url(${mountainBg})` }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#212529] via-[#212529]/95 to-[#212529] pointer-events-none" />
          <div className="absolute top-1/3 -right-24 w-[450px] h-[300px] bg-[#8338EC]/15 rounded-full blur-[100px] pointer-events-none" />

          <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Heading row */}
            <div className="mb-10">
              <div className="max-w-2xl">
                <h2 className="text-xs font-bold uppercase tracking-widest text-[#8338EC] mb-2">
                  VERIFICATION PREVIEW
                </h2>
                <h3 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-2">
                  EXAMPLE COMPLIANCE CHECK
                </h3>
                <p className="text-sm sm:text-base text-slate-300">
                  See how PackCheck AI presents the result after an inspection has been completed.
                </p>
              </div>
            </div>

            {/* Exact 2-Card Split Layout Preserved - Equal Height via Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
              
              {/* Left Side: Compliance Check Breakdown */}
              <div className="bg-white border border-slate-300 rounded p-6 shadow-xs flex flex-col justify-between h-full">
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                    <div>
                      <span className="text-xs font-mono uppercase text-slate-500">Commodity</span>
                      <h4 className="text-lg font-bold text-[#212529]">Packaged Wheat Flour</h4>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500 block">Status</span>
                      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-300 px-2.5 py-0.5 rounded">
                        <Check className="w-3.5 h-3.5 text-emerald-600 stroke-[3]" />
                        COMPLIANT
                      </span>
                    </div>
                  </div>

                  <div>
                    <h5 className="text-xs font-semibold text-[#212529] uppercase tracking-wider mb-3">
                      Declaration Checks
                    </h5>
                    <div className="divide-y divide-slate-200 border border-slate-200 rounded">
                      {[
                        { label: 'Manufacturer Details', verified: true },
                        { label: 'Net Quantity', verified: true },
                        { label: 'MRP', verified: true },
                        { label: 'Date of Packaging', verified: true },
                        { label: 'Consumer Care Details', verified: true },
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 text-sm bg-white hover:bg-slate-50/50">
                          <span className="text-[#212529] font-medium">{item.label}</span>
                          <span className="w-5 h-5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pt-6 text-xs text-slate-500 flex items-center justify-between border-t border-slate-200 mt-6">
                  <span>Standard: Legal Metrology (PC) Rules, 2011</span>
                  <span className="font-mono text-slate-600">5 of 5 Passed</span>
                </div>
              </div>

              {/* Right Side: Inspection Report Preview */}
              <div className="bg-white border border-slate-300 rounded p-6 shadow-xs flex flex-col justify-between h-full">
                <div className="flex items-start justify-between border-b border-slate-200 pb-4">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500 block mb-0.5">
                      OFFICIAL DOCUMENT
                    </span>
                    <h4 className="text-lg font-bold text-[#212529] tracking-tight">
                      INSPECTION REPORT
                    </h4>
                  </div>
                  <span className="text-xs font-mono bg-emerald-50 text-emerald-700 px-2 py-1 rounded border border-emerald-300 font-semibold">
                    STATUS: COMPLIANT
                  </span>
                </div>

                <div className="text-xs space-y-1.5 bg-[#E9ECEF]/50 p-3 rounded border border-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Product:</span>
                    <span className="font-semibold text-[#212529]">Packaged Wheat Flour</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Inspection ID:</span>
                    <span className="font-mono text-slate-700">INS-2026-0842</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Date:</span>
                    <span className="text-slate-700">05 September 2026</span>
                  </div>
                </div>

                <div>
                  <h5 className="text-xs font-semibold text-[#212529] uppercase tracking-wider mb-2">
                    Declaration Verification
                  </h5>
                  <div className="border border-slate-200 rounded overflow-hidden text-xs">
                    <table className="w-full text-left">
                      <thead className="bg-[#E9ECEF] text-[#212529] font-semibold border-b border-slate-300">
                        <tr>
                          <th className="py-2 px-3">Declaration</th>
                          <th className="py-2 px-3 text-right">Result</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 bg-white">
                        <tr>
                          <td className="py-2 px-3 text-[#212529]">Manufacturer Details</td>
                          <td className="py-2 px-3 text-right font-medium text-emerald-700">Verified</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 text-[#212529]">Net Quantity</td>
                          <td className="py-2 px-3 text-right font-medium text-emerald-700">Verified</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 text-[#212529]">MRP</td>
                          <td className="py-2 px-3 text-right font-medium text-emerald-700">Verified</td>
                        </tr>
                        <tr>
                          <td className="py-2 px-3 text-[#212529]">Date</td>
                          <td className="py-2 px-3 text-right font-medium text-emerald-700">Verified</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => navigate('/login')}
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded border border-slate-300 bg-[#E9ECEF] hover:bg-slate-200 text-[#212529] text-xs font-semibold tracking-wide uppercase transition-colors cursor-pointer"
                  >
                    <FileText className="w-4 h-4 text-slate-600" />
                    [ PDF REPORT PREVIEW ]
                  </button>
                </div>
              </div>

            </div>
          </div>
        </section>
      </main>

      {/* ==================================================
          5. FOOTER
          Layout preserved EXACTLY:
          - Styled with cohesive dark mountain atmosphere
          - Always present at bottom of the continuous homepage
          ================================================== */}
      <footer className="relative overflow-hidden bg-[#212529] py-10 text-sm text-slate-400">
        <div 
          className="absolute inset-0 bg-cover bg-bottom bg-no-repeat pointer-events-none opacity-20"
          style={{ backgroundImage: `url(${mountainBg})` }}
        />
        <div className="absolute inset-0 bg-[#212529]/90 pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center md:text-left">
            <div className="font-bold text-white flex items-center justify-center md:justify-start gap-1.5">
              <Shield className="w-4 h-4 text-[#8338EC]" />
              PackCheck AI
            </div>
            <div className="text-xs text-slate-400">
              Legal Metrology Compliance Platform
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs sm:text-sm font-medium">
            <button 
              onClick={() => scrollToSection('hero-section')} 
              className="hover:text-white transition-colors cursor-pointer text-slate-300"
            >
              Home
            </button>
            <button 
              onClick={() => scrollToSection('how-it-works')} 
              className="hover:text-white transition-colors cursor-pointer text-slate-300"
            >
              How It Works
            </button>
            <button 
              onClick={() => scrollToSection('key-features')} 
              className="hover:text-white transition-colors cursor-pointer text-slate-300"
            >
              Key Features
            </button>
            <button 
              onClick={() => navigate('/login')} 
              className="hover:text-[#FB5607] text-[#FB5607] font-semibold transition-colors cursor-pointer"
            >
              Login
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}