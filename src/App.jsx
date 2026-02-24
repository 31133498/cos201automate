import { useState, useEffect } from 'react';
import { CheckCircle } from 'lucide-react';

function App() {
  const [state, setState] = useState('form');
  const [formData, setFormData] = useState({ name: '', matric_no: '', email: '', token: '' });
  const [terminalText, setTerminalText] = useState('');

  const terminalSequence = [
    '> Authenticating Token...',
    '> Synthesizing Dataset (>500 rows)...',
    '> Training Multiple Linear Regression Model...',
    '> Plotting Visualizations...',
    '> Packaging files and emailing...'
  ];

  useEffect(() => {
    if (state === 'loading') {
      let step = 0;
      setTerminalText(terminalSequence[0]);

      const interval = setInterval(() => {
        step++;
        if (step < terminalSequence.length) {
          setTerminalText(terminalSequence[step]);
        } else {
          clearInterval(interval);
          setState('success');
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [state]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setState('loading');
    
    // Start API call immediately
    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Request failed'}`);
        setState('form');
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
      setState('form');
    }
  };

  const handleReset = () => {
    setState('form');
    setFormData({ name: '', matric_no: '', email: '', token: '' });
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      {state === 'form' && (
        <div className="w-full max-w-md bg-slate-800 border border-slate-700 rounded-lg shadow-2xl p-8">
          <h1 className="text-3xl font-bold text-white mb-8 text-center">
            COS201 ML Assignment Generator
          </h1>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Full Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-md text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your full name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Matric Number</label>
              <input
                type="text"
                required
                value={formData.matric_no}
                onChange={(e) => setFormData({ ...formData, matric_no: e.target.value })}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-md text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your matric number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-md text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="your.email@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Access Token</label>
              <input
                type="password"
                required
                value={formData.token}
                onChange={(e) => setFormData({ ...formData, token: e.target.value })}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-md text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your access token"
              />
            </div>
            <button
              type="submit"
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-md transition-all transform hover:scale-105 shadow-lg"
            >
              Run My Analysis
            </button>
          </form>
        </div>
      )}

      {state === 'loading' && (
        <div className="w-full max-w-2xl bg-black border border-green-900 rounded-lg shadow-2xl p-8">
          <div className="font-mono text-green-400 text-lg">
            {terminalText}
            <span className="animate-pulse">_</span>
          </div>
        </div>
      )}

      {state === 'success' && (
        <div className="w-full max-w-md bg-slate-800 border border-slate-700 rounded-lg shadow-2xl p-8 text-center">
          <CheckCircle className="w-24 h-24 text-green-500 mx-auto mb-6" strokeWidth={2} />
          <p className="text-white text-lg leading-relaxed mb-8">
            Done! Your personalized dataset, Python script, and graphs have been zipped and sent to your email. (Check your spam folder just in case!)
          </p>
          <button
            onClick={handleReset}
            className="px-8 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-md transition-all"
          >
            Return Home
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
