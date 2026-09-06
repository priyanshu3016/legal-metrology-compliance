import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale, Shield, Eye, EyeOff, Loader2, Lock, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import mountainBg from '../assets/mountain-bg.jpg';

export default function LoginPage() {
  const [officerName, setOfficerName] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setError('');

    const trimmedName = officerName.trim();
    if (!trimmedName) {
      setError('Please enter your Officer Name or Username.');
      return;
    }

    setIsLoading(true);

    // Format display name nicely (e.g. 'raman yadav' -> 'Raman Yadav')
    const formattedName = trimmedName.includes('@')
      ? trimmedName.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      : trimmedName.replace(/[._-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    const cleanUsername = trimmedName.toLowerCase().replace(/\s+/g, '.');

    setTimeout(() => {
      setIsLoading(false);
      login({
        id: `OFF-2026-${Math.floor(Math.random() * 900) + 100}`,
        name: formattedName,
        username: cleanUsername,
        email: trimmedName.includes('@') ? trimmedName : `${cleanUsername}@lm.gov.in`,
        role: 'Senior Enforcement Officer',
        badgeNumber: `LMO-DL-${Math.floor(Math.random() * 9000) + 1000}`,
        location: 'Delhi NCR Region'
      });
      navigate('/dashboard');
    }, 400);
  };

  const handleQuickDemo = () => {
    setOfficerName('Rajesh Kumar');
    setPassword('packcheck2026');
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#212529] text-[#212529] flex flex-col justify-between p-4 sm:p-6 lg:p-8 selection:bg-[#8338EC] selection:text-white">
      {/* Background Mountain Layer & Atmosphere */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat pointer-events-none opacity-30"
        style={{ backgroundImage: `url(${mountainBg})` }}
      />
      <div className="absolute inset-0 bg-[#212529]/75 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#212529]/90 via-[#212529]/70 to-[#212529] pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#8338EC]/20 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute -bottom-24 right-1/4 w-[450px] h-[250px] bg-[#FB5607]/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Top Left Brand */}
      <header className="relative z-10 w-full max-w-7xl mx-auto">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2.5 text-white hover:opacity-90 transition-opacity group"
        >
          <div className="w-9 h-9 rounded-lg bg-[#8338EC] text-white flex items-center justify-center shadow-xs">
            <Scale className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-sm sm:text-base tracking-wider uppercase text-white font-sans">
              Legal Metrology
            </span>
            <span className="text-[10px] text-slate-300 font-medium tracking-tight -mt-0.5">
              PackCheck AI &bull; Enforcement Portal
            </span>
          </div>
        </Link>
      </header>

      {/* Centered Login Content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center my-6 sm:my-10">
        <div className="w-full max-w-md space-y-6">
          {/* Heading and Subheading */}
          <div className="text-center space-y-1.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white font-sans uppercase drop-shadow-sm">
              Officer Login
            </h1>
            <p className="text-sm text-slate-300 font-normal">
              Sign in to access your inspection dashboard
            </p>
          </div>

          {/* Quick Demo Assist Banner */}
          <div className="bg-white/95 backdrop-blur-xs border border-slate-300 rounded-lg p-2.5 text-xs text-[#212529] flex items-center justify-between gap-2 shadow-xs">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#8338EC] shrink-0" />
              <span>Enter any officer name or load sample credentials:</span>
            </div>
            <button 
              type="button" 
              onClick={handleQuickDemo}
              className="font-semibold text-[#8338EC] hover:text-[#7126dc] underline shrink-0 cursor-pointer text-xs"
            >
              Demo Fill
            </button>
          </div>

          {/* Login Form Container - Clean light/off-white foreground surface */}
          <div className="bg-white rounded-xl border border-slate-300 shadow-xl p-6 sm:p-8">
            <form onSubmit={handleLogin} className="space-y-5">
              {error && (
                <div className="bg-red-50 text-red-700 p-3 rounded-lg text-xs sm:text-sm font-medium border border-red-200 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Officer ID / Username */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#212529] uppercase tracking-wider">
                  Officer ID / Username
                </label>
                <div className="relative">
                  <Input
                    type="text"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-sm rounded-lg border-slate-300 focus:border-[#8338EC] focus:ring-1 focus:ring-[#8338EC]"
                    placeholder="e.g. Officer Raman Yadav / OFF-2026"
                    autoFocus
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#212529] uppercase tracking-wider">
                  Password
                </label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 pr-10 text-sm rounded-lg border-slate-300 focus:border-[#8338EC] focus:ring-1 focus:ring-[#8338EC]"
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Remember me & Forgot password */}
              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 text-slate-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    id="remember-me"
                    name="remember-me"
                    className="h-4 w-4 text-[#8338EC] focus:ring-[#8338EC] border-slate-300 rounded cursor-pointer"
                  />
                  <span>Remember me</span>
                </label>

                <a 
                  href="#forgot" 
                  onClick={(e) => { e.preventDefault(); alert("For demo/prototype evaluation, simply enter any username and password to log in."); }}
                  className="font-medium text-[#8338EC] hover:text-[#7126dc] hover:underline"
                >
                  Forgot Password?
                </a>
              </div>

              {/* Prominent Login Button with Orange Brand Accent (#FB5607) */}
              <Button 
                type="submit" 
                className="w-full py-2.5 px-4 text-sm font-semibold uppercase tracking-wider bg-[#FB5607] hover:bg-[#e04b04] active:bg-[#c54002] text-white rounded-lg shadow-md shadow-[#FB5607]/25 transition-colors cursor-pointer border-none"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Authenticating...
                  </span>
                ) : (
                  'Login'
                )}
              </Button>
            </form>
          </div>

          {/* Security / Authorization Message */}
          <div className="text-center">
            <p className="text-xs text-slate-300 font-medium leading-relaxed drop-shadow-xs">
              Authorized access for Legal Metrology <br className="hidden sm:inline" />
              Inspecting Officers
            </p>
          </div>
        </div>
      </main>

      {/* Bottom Left Back to Home */}
      <footer className="relative z-10 w-full max-w-7xl mx-auto pt-2">
        <Link 
          to="/" 
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Home</span>
        </Link>
      </footer>
    </div>
  );
}
