import { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

export default function SourcesPreview() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchSources = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('sources')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(5);
    
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

  if (loading) {
    return <div className="text-center py-2">Loading...</div>;
  }

  if (sources.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No sources found. Add your first source to get started.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sources.map((source) => (
        <div key={source.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
          <div>
            <div className="font-medium text-sm text-gray-900">{source.source_type}</div>
            <div className="text-xs text-gray-500">{source.source_name || source.source_identifier}</div>
          </div>
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            source.active 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {source.active ? 'Active' : 'Inactive'}
          </span>
        </div>
      ))}
    </div>
  );
}
