import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import SourcesTable from '../components/SourcesTable';
import ClientsTable from '../components/ClientsTable';
import SourcesPreview from '../components/SourcesPreview';
import ClientsPreview from '../components/ClientsPreview';
import { supabase } from '../supabaseClient';

const DashboardPage = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    totalSources: 0,
    activeClients: 0,
    newslettersSent: 0
  });

  const fetchStats = async () => {
    try {
      // Fetch sources count
      const { count: sourcesCount } = await supabase
        .from('sources')
        .select('*', { count: 'exact', head: true });

      // Fetch clients count
      const { count: clientsCount } = await supabase
        .from('clients')
        .select('*', { count: 'exact', head: true });

      // Fetch newsletters count
      const { count: newslettersCount } = await supabase
        .from('newsletters')
        .select('*', { count: 'exact', head: true });

      setStats({
        totalSources: sourcesCount || 0,
        activeClients: clientsCount || 0,
        newslettersSent: newslettersCount || 0
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage your content sources and clients
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="mb-6">
            <nav className="flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('sources')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'sources'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sources
              </button>
              <button
                onClick={() => setActiveTab('clients')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'clients'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Clients
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Quick Stats */}
              <div className="bg-white shadow sm:rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                    Quick Stats
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{stats.totalSources}</div>
                      <div className="text-sm text-gray-600">Total Sources</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{stats.activeClients}</div>
                      <div className="text-sm text-gray-600">Active Clients</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{stats.newslettersSent}</div>
                      <div className="text-sm text-gray-600">Newsletters Sent</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white shadow sm:rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Recent Sources
                    </h3>
                    <SourcesPreview />
                  </div>
                </div>
                <div className="bg-white shadow sm:rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Recent Clients
                    </h3>
                    <ClientsPreview />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sources' && (
            <div className="space-y-6">
              <SourcesTable />
            </div>
          )}

          {activeTab === 'clients' && (
            <div className="space-y-6">
              <ClientsTable />
            </div>
          )}


        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
