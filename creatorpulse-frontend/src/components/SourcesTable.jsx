import { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

export default function SourcesTable() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [formData, setFormData] = useState({
    source_type: '',
    source_name: '',
    source_identifier: '',
    active: true
  });

  const fetchSources = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('sources')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching sources:', error);
    } else {
      setSources(data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleAddNew = () => {
    setEditingSource(null);
    setFormData({
      source_type: '',
      source_name: '',
      source_identifier: '',
      active: true
    });
    setShowModal(true);
  };

  const handleEdit = (source) => {
    setEditingSource(source);
    setFormData({
      source_type: source.source_type,
      source_name: source.source_name,
      source_identifier: source.source_identifier,
      active: source.active
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this source?')) {
      return;
    }

    const { error } = await supabase
      .from('sources')
      .delete()
      .eq('id', id);

    if (error) {
      console.error('Error deleting source:', error);
      alert('Failed to delete source');
    } else {
      fetchSources();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.source_type || !formData.source_identifier) {
      alert('Source type and identifier are required');
      return;
    }

    try {
      if (editingSource) {
        // Update existing source
        const { error } = await supabase
          .from('sources')
          .update(formData)
          .eq('id', editingSource.id);

        if (error) {
          console.error('Error updating source:', error);
          alert('Failed to update source');
        } else {
          setShowModal(false);
          fetchSources();
        }
      } else {
        const { data: { user } } = await supabase.auth.getUser();

        if (!user) {
          alert('You must be logged in to create a source');
          return;
        }

        // Create new source
        const sourceData = {
          ...formData,
          user_id: user.id
        };

        const { error } = await supabase
          .from('sources')
          .insert([sourceData]);

        if (error) {
          console.error('Error creating source:', error);
          alert('Failed to create source');
        } else {
          setShowModal(false);
          fetchSources();
        }
      }
    } catch (error) {
      console.error('Unexpected error:', error);
      alert('An unexpected error occurred');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleTemplatePopulate = async (templateType) => {
    if (!window.confirm(`This will populate your sources with ${templateType} templates. Continue?`)) {
      return;
    }

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      alert('You must be logged in to use templates');
      return;
    }

    // Template sources will be provided later
    const templateSources = getTemplateSources(templateType);
    
    try {
      const sourcesWithUserId = templateSources.map(source => ({
        ...source,
        user_id: user.id
      }));

      const { error } = await supabase
        .from('sources')
        .insert(sourcesWithUserId);

      if (error) {
        console.error('Error adding template sources:', error);
        alert('Failed to add template sources');
      } else {
        alert(`${templateType} template sources added successfully!`);
        fetchSources();
      }
    } catch (error) {
      console.error('Unexpected error:', error);
      alert('An unexpected error occurred');
    }
  };

  const getTemplateSources = (templateType) => {
    if (templateType === 'AI') {
      return [
        // RSS Sources
        { source_type: 'rss', source_name: 'AI News', source_identifier: 'https://www.artificialintelligence-news.com/feed/', active: true },
        { source_type: 'rss', source_name: 'Medium Generative AI', source_identifier: 'https://medium.com/feed/tag/generative-ai', active: true },
        { source_type: 'rss', source_name: 'MIT AI News', source_identifier: 'https://news.mit.edu/rss/topic/artificial-intelligence', active: true },
       
        // Reddit Sources
        { source_type: 'reddit', source_name: 'Artificial Intelligence', source_identifier: 'artificial', active: true },
        
        // Blog Sources (websites without RSS)
        { source_type: 'blog', source_name: 'Stability AI News', source_identifier: 'https://stability.ai/news', active: true },
      ];
    } else if (templateType === 'General') {
      return [
        // --- Tech & Business ---
        { source_type: 'rss', source_name: 'TechCrunch', source_identifier: 'https://techcrunch.com/feed/', active: true },
        // --- World & Politics ---
        { source_type: 'rss', source_name: 'BBC World', source_identifier: 'https://feeds.bbci.co.uk/news/world/rss.xml', active: true },
        { source_type: 'rss', source_name: 'Reuters World News', source_identifier: 'https://feeds.reuters.com/reuters/worldNews', active: true },
        { source_type: 'rss', source_name: 'The Guardian World', source_identifier: 'https://www.theguardian.com/world/rss', active: true },

        // --- Reddit Communities ---
        { source_type: 'reddit', source_name: 'World News', source_identifier: 'worldnews', active: true },

        // --- Blogs & Podcasts ---
        { source_type: 'blog', source_name: 'Wait But Why', source_identifier: 'https://waitbutwhy.com/', active: true },
        { source_type: 'podcast', source_name: 'TED Talks Daily', source_identifier: 'https://feeds.feedburner.com/TEDTalks_audio', active: true }
      ];
    }

    return [];
  };

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg leading-6 font-medium text-gray-900">Sources</h2>
          <div className="flex space-x-3">
            <button
              onClick={() => handleTemplatePopulate('AI')}
              className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Add AI News Sources
            </button>
            <button
              onClick={() => handleTemplatePopulate('General')}
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              Add General News Sources
            </button>
            <button
              onClick={handleAddNew}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Add Custom Source
            </button>
          </div>
        </div>


        {/* Sources Table */}
        {loading ? (
          <div className="text-center py-4">Loading...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Identifier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Active
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sources.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                      No sources found. Add your first source to get started.
                    </td>
                  </tr>
                ) : (
                  sources.map((source) => (
                    <tr key={source.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {source.source_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {source.source_name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {source.source_identifier}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          source.active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {source.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleEdit(source)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(source.id)}
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingSource ? 'Edit Source' : 'Add New Source'}
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Type *
                  </label>
                  <select
                    name="source_type"
                    value={formData.source_type}
                    onChange={handleInputChange}
                    required
                    className="input"
                  >
                    <option value="">Select a type</option>
                    <option value="rss">RSS Feed (e.g., https://example.com/feed.xml)</option>
                    <option value="youtube">YouTube Channel (e.g., @channelname or channel ID)</option>
                    <option value="reddit">Reddit Community (e.g., machinelearning)</option>
                    <option value="blog">Blog/Website (e.g., https://example.com)</option>
                    <option value="podcast">Podcast (e.g., RSS feed URL)</option>
                    <option value="other">Other (custom source)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Name
                  </label>
                  <input
                    type="text"
                    name="source_name"
                    value={formData.source_name}
                    onChange={handleInputChange}
                    placeholder="e.g., My Blog"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Identifier *
                  </label>
                  <input
                    type="text"
                    name="source_identifier"
                    value={formData.source_identifier}
                    onChange={handleInputChange}
                    placeholder={
                      formData.source_type === 'rss' ? 'https://example.com/feed.xml' :
                      formData.source_type === 'youtube' ? '@channelname or UCxxxxxxxxxxxxxxxx' :
                      formData.source_type === 'reddit' ? 'subredditname (without r/)' :
                      formData.source_type === 'blog' ? 'https://example.com' :
                      formData.source_type === 'podcast' ? 'https://example.com/podcast.rss' :
                      'Enter source identifier'
                    }
                    required
                    className="input"
                  />
                  {formData.source_type && (
                    <p className="mt-1 text-xs text-gray-500">
                      {formData.source_type === 'rss' && 'Enter the full RSS feed URL'}
                      {formData.source_type === 'youtube' && 'Enter channel handle (@name) or channel ID'}
                      {formData.source_type === 'reddit' && 'Enter subreddit name only (without r/)'}
                      {formData.source_type === 'blog' && 'Enter the main website URL'}
                      {formData.source_type === 'podcast' && 'Enter the podcast RSS feed URL'}
                      {formData.source_type === 'other' && 'Enter any relevant identifier'}
                    </p>
                  )}
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="active"
                    checked={formData.active}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Active
                  </label>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {editingSource ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
