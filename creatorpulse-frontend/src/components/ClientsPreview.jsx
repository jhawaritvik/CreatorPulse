import { useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

export default function ClientsPreview() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchClients = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('clients')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(5);
    
    if (error) {
      console.error('Error fetching clients:', error);
    } else {
      setClients(data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchClients();
  }, []);

  if (loading) {
    return <div className="text-center py-2">Loading...</div>;
  }

  if (clients.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No clients found. Add your first client to get started.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {clients.map((client) => (
        <div key={client.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
          <div>
            <div className="font-medium text-sm text-gray-900">{client.name}</div>
            <div className="text-xs text-gray-500">{client.email}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
