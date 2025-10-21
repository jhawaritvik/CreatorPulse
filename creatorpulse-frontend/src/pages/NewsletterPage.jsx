import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import NewsletterList from '../components/NewsletterList';
import NewsletterEditor from '../components/NewsletterEditor';

const NewsletterPage = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('list'); // 'list' or 'editor'
  const [selectedNewsletter, setSelectedNewsletter] = useState(null);

  const handleSelectNewsletter = (newsletter) => {
    setSelectedNewsletter(newsletter);
    setCurrentView('editor');
  };

  const handleCreateNew = () => {
    setSelectedNewsletter(null);
    setCurrentView('editor');
  };

  const handleBackToList = () => {
    setSelectedNewsletter(null);
    setCurrentView('list');
  };

  const handleNewsletterSave = () => {
    // Refresh the list or handle save completion
    setCurrentView('list');
    setSelectedNewsletter(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Newsletter Management</h1>
            <p className="mt-1 text-sm text-gray-600">
              Create, edit, and send newsletters to your subscribers
            </p>
          </div>

          {currentView === 'list' ? (
            <NewsletterList 
              onSelectNewsletter={handleSelectNewsletter}
              onCreateNew={handleCreateNew}
            />
          ) : (
            <NewsletterEditor 
              newsletter={selectedNewsletter}
              onSave={handleNewsletterSave}
              onBack={handleBackToList}
            />
          )}
        </div>
      </main>
    </div>
  );
};

export default NewsletterPage;
