import { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

export default function NewsletterList({ onSelectNewsletter, onCreateNew }) {
  const [newsletters, setNewsletters] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchNewsletters = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('newsletters')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching newsletters:', error);
    } else {
      setNewsletters(data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchNewsletters();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this newsletter?')) {
      return;
    }

    const { error } = await supabase
      .from('newsletters')
      .delete()
      .eq('id', id);

    if (error) {
      console.error('Error deleting newsletter:', error);
      alert('Failed to delete newsletter');
    } else {
      fetchNewsletters();
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', text: 'Draft' },
      scheduled: { color: 'bg-yellow-100 text-yellow-800', text: 'Scheduled' },
      sent: { color: 'bg-green-100 text-green-800', text: 'Sent' },
      failed: { color: 'bg-red-100 text-red-800', text: 'Failed' }
    };
    
    const config = statusConfig[status] || statusConfig.draft;
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.color}`}>
        {config.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Newsletters</h2>
          <button
            onClick={onCreateNew}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create New Newsletter
          </button>
        </div>

        {loading ? (
          <div className="text-center py-4">Loading...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scheduled
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {newsletters.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                      No newsletters found. Create your first newsletter to get started.
                    </td>
                  </tr>
                ) : (
                  newsletters.map((newsletter) => (
                    <tr key={newsletter.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {newsletter.title || 'Untitled Newsletter'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {newsletter.content ? `${newsletter.content.substring(0, 100)}...` : 'No content'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(newsletter.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(newsletter.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {newsletter.scheduled_time ? formatDate(newsletter.scheduled_time) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => onSelectNewsletter(newsletter)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(newsletter.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
