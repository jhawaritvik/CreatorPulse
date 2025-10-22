import { useState } from 'react';
import { apiService } from '../services/api';
import { supabase } from '../supabaseClient';

export default function ApiTest() {
  const [testResult, setTestResult] = useState('');
  const [loading, setLoading] = useState(false);

  const testApiConnection = async () => {
    setLoading(true);
    try {
      const result = await apiService.testConnection();
      setTestResult(`✅ API Connection Successful: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestResult(`❌ API Connection Failed: ${error.message}`);
    }
    setLoading(false);
  };

  const testAuthentication = async () => {
    setLoading(true);
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) {
        setTestResult(`❌ Authentication Error: ${error.message}`);
      } else if (!session) {
        setTestResult(`❌ No active session - please log in`);
      } else {
        setTestResult(`✅ Authentication OK - User: ${session.user.email}`);
      }
    } catch (error) {
      setTestResult(`❌ Auth Test Failed: ${error.message}`);
    }
    setLoading(false);
  };

  const testGenerateDraft = async () => {
    setLoading(true);
    try {
      // Test with minimal valid data
      // Use 'new' to indicate a draft for a new newsletter (backend skips UUID validation)
      const result = await apiService.generateDraft({
        newsletterId: 'new',
        // Provide at least one fake active source identifier structure to pass validation
        sources: [
          {
            id: 'debug-source',
            source_type: 'rss',
            source_name: 'Debug Source',
            source_identifier: 'https://example.com/rss.xml',
            active: true
          }
        ]
      });
      setTestResult(`✅ Generate Draft Successful: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestResult(`❌ Generate Draft Failed: ${error.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="p-4 border rounded bg-white">
      <h3 className="text-lg font-semibold mb-4">API Debug Tests</h3>
      
      <div className="space-y-3">
        <button
          onClick={testApiConnection}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 mr-2"
        >
          {loading ? 'Testing...' : 'Test API Connection'}
        </button>
        
        <button
          onClick={testAuthentication}
          disabled={loading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 mr-2"
        >
          {loading ? 'Testing...' : 'Test Authentication'}
        </button>
        
        <button
          onClick={testGenerateDraft}
          disabled={loading}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Generate Draft'}
        </button>
      </div>
      
      {testResult && (
        <div className="mt-4 p-3 bg-gray-100 rounded">
          <pre className="text-sm whitespace-pre-wrap">{testResult}</pre>
        </div>
      )}
    </div>
  );
}
