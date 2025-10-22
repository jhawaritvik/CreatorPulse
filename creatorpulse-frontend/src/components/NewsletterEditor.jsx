import { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import { apiService } from '../services/api';

export default function NewsletterEditor({ newsletter, onSave, onBack }) {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    status: 'draft'
  });
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [selectedClients, setSelectedClients] = useState([]);
  const [showSendModal, setShowSendModal] = useState(false);
  const [scheduledTime, setScheduledTime] = useState('');
  const [sendImmediately, setSendImmediately] = useState(true);
  const [sources, setSources] = useState([]);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (newsletter) {
      setFormData({
        title: newsletter.title || '',
        content: newsletter.content || '',
        status: newsletter.status || 'draft'
      });
    }
    fetchClients();
    fetchSources();
  }, [newsletter]);

  const fetchClients = async () => {
    const { data, error } = await supabase
      .from('clients')
      .select('*')
      .order('name');
    
    if (error) {
      console.error('Error fetching clients:', error);
    } else {
      setClients(data || []);
    }
  };

  const fetchSources = async () => {
    const { data, error } = await supabase
      .from('sources')
      .select('*')
      .eq('active', true)
      .order('source_name');
    
    if (error) {
      console.error('Error fetching sources:', error);
    } else {
      setSources(data || []);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleGenerateFromSources = async () => {
    if (sources.length === 0) {
      alert('No active sources found. Please add and activate sources first.');
      return;
    }

    setGenerating(true);
    try {
      // Convert sources to the format expected by the API
      const sourcesData = sources.map(source => ({
        id: source.id,
        source_type: source.source_type,
        source_name: source.source_name,
        source_identifier: source.source_identifier,
        active: source.active
      }));

      const response = await apiService.generateDraft({
        newsletterId: newsletter?.id || 'new',
        sources: sourcesData
      });

      if (response.draft) {
        setFormData(prev => ({
          ...prev,
          content: response.draft
        }));
        alert(`Newsletter generated successfully using ${response.sources_used?.length || sources.length} sources!`);
      } else {
        throw new Error('No draft content received from API');
      }
    } catch (error) {
      console.error('Error generating newsletter from sources:', error);
      alert(`Failed to generate newsletter: ${error.message}`);
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const newsletterData = {
        ...formData,
        updated_at: new Date().toISOString()
      };

      let result;
      if (newsletter) {
        // Update existing newsletter
        result = await supabase
          .from('newsletters')
          .update(newsletterData)
          .eq('id', newsletter.id);
      } else {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) {
          alert('You must be logged in to save a newsletter');
          setLoading(false);
          return;
        }

        // Create new newsletter
        const newsletterData = {
          ...formData,
          user_id: user.id,
          updated_at: new Date().toISOString()
        };
        result = await supabase
          .from('newsletters')
          .insert([newsletterData])
          .select()
          .single();
      }

      if (result.error) {
        console.error('Error saving newsletter:', result.error);
        alert('Failed to save newsletter');
      } else {
        alert('Newsletter saved successfully!');
        if (onSave) onSave(result.data);
      }
    } catch (error) {
      console.error('Unexpected error:', error);
      alert('An unexpected error occurred');
    }
    setLoading(false);
  };

  const handleSend = async () => {
    if (selectedClients.length === 0) {
      alert('Please select at least one client to send the newsletter to.');
      return;
    }

    setLoading(true);
    try {
      // First save the newsletter
      await handleSave();

      // Prepare send data
      const sendData = {
        newsletterId: newsletter?.id,
        clientIds: selectedClients,
        scheduledTime: sendImmediately ? null : new Date(scheduledTime).toISOString(),
        sendImmediately
      };

      // Call send function using apiService for proper authentication
      const response = await apiService.sendNewsletter(sendData);
      
      if (response && response.success) {
        let message = `Newsletter sent successfully to ${response.recipients} recipients!`;
        if (response.scheduledFor) {
          const localTime = new Date(response.scheduledFor).toLocaleString();
          message = `Newsletter scheduled successfully for ${localTime}. It will be sent to ${response.recipients} recipients.`;
        }
        alert(message);
        setShowSendModal(false);
        if (onSave) onSave();
      } else {
        alert(`Failed to send newsletter: ${response?.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error sending newsletter:', error);
      alert(`Failed to send newsletter: ${error.detail || error.message}`);
    }
    setLoading(false);
  };

  const handleClientToggle = (clientId) => {
    setSelectedClients(prev => 
      prev.includes(clientId)
        ? prev.filter(id => id !== clientId)
        : [...prev, clientId]
    );
  };

  const handleSelectAllClients = () => {
    setSelectedClients(clients.map(client => client.id));
  };

  const handleDeselectAllClients = () => {
    setSelectedClients([]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            {newsletter ? 'Edit Newsletter' : 'Create New Newsletter'}
          </h2>
          <p className="text-sm text-gray-600">
            {newsletter ? 'Modify your newsletter content' : 'Write and send newsletters to your clients'}
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Back to List
          </button>
        )}
      </div>

      {/* Newsletter Form */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <form className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Newsletter Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="Enter newsletter title"
                required
                className="input"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Newsletter Content *
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                placeholder="Write your newsletter content here..."
                required
                rows={15}
                className="input"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleGenerateFromSources}
                disabled={loading || generating || sources.length === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {generating ? 'Generating...' : `Generate from Sources (${sources.length})`}
              </button>
              
              <button
                type="button"
                onClick={handleSave}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                Save Draft
              </button>
              
              <button
                type="button"
                onClick={() => setShowSendModal(true)}
                disabled={loading || !formData.title || !formData.content}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                Send Newsletter
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Send Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Send Newsletter
              </h3>
              
              <div className="space-y-6">
                {/* Client Selection */}
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <label className="block text-sm font-medium text-gray-700">
                      Select Recipients *
                    </label>
                    <div className="space-x-2">
                      <button
                        type="button"
                        onClick={handleSelectAllClients}
                        className="text-xs text-indigo-600 hover:text-indigo-900"
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={handleDeselectAllClients}
                        className="text-xs text-gray-600 hover:text-gray-900"
                      >
                        Deselect All
                      </button>
                    </div>
                  </div>
                  
                  <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-3">
                    {clients.length === 0 ? (
                      <p className="text-sm text-gray-500">No clients found. Add clients first.</p>
                    ) : (
                      <div className="space-y-2">
                        {clients.map((client) => (
                          <label key={client.id} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={selectedClients.includes(client.id)}
                              onChange={() => handleClientToggle(client.id)}
                              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <span className="ml-2 text-sm text-gray-900">
                              {client.name} ({client.email})
                            </span>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Send Options */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Send Options
                  </label>
                  
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={sendImmediately}
                        onChange={() => setSendImmediately(true)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-900">Send immediately</span>
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={!sendImmediately}
                        onChange={() => setSendImmediately(false)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-900">Schedule for later</span>
                    </label>
                  </div>

                  {!sendImmediately && (
                    <div className="mt-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Scheduled Time
                      </label>
                      <input
                        type="datetime-local"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        min={new Date().toISOString().slice(0, 16)}
                        className="input"
                      />
                    </div>
                  )}
                </div>

                {/* Modal Actions */}
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowSendModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={loading || selectedClients.length === 0}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {loading ? 'Sending...' : 'Send Newsletter'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
