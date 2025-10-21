import { supabase } from '../supabaseClient';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      throw new Error('No authentication token available');
    }
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`
    };
  }

  async request(endpoint, options = {}) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          ...options.headers
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Test endpoint
  async testConnection() {
    try {
      const response = await fetch(`${this.baseURL}/api/test`);
      return await response.json();
    } catch (error) {
      console.error('API connection test failed:', error);
      throw error;
    }
  }

  // Sources endpoints
  async getSources() {
    return this.request('/api/sources');
  }

  async createSource(sourceData) {
    return this.request('/api/sources', {
      method: 'POST',
      body: JSON.stringify(sourceData)
    });
  }

  async updateSource(sourceId, sourceData) {
    return this.request(`/api/sources/${sourceId}`, {
      method: 'PUT',
      body: JSON.stringify(sourceData)
    });
  }

  async deleteSource(sourceId) {
    return this.request(`/api/sources/${sourceId}`, {
      method: 'DELETE'
    });
  }

  // Clients endpoints
  async getClients() {
    return this.request('/api/clients');
  }

  async createClient(clientData) {
    return this.request('/api/clients', {
      method: 'POST',
      body: JSON.stringify(clientData)
    });
  }

  async updateClient(clientId, clientData) {
    return this.request(`/api/clients/${clientId}`, {
      method: 'PUT',
      body: JSON.stringify(clientData)
    });
  }

  async deleteClient(clientId) {
    return this.request(`/api/clients/${clientId}`, {
      method: 'DELETE'
    });
  }

  // Newsletter endpoints
  async getNewsletters() {
    return this.request('/api/newsletters');
  }

  async generateDraft(newsletterData) {
    return this.request('/api/generate-draft', {
      method: 'POST',
      body: JSON.stringify(newsletterData)
    });
  }

  async sendNewsletter(newsletterData) {
    return this.request('/api/send-newsletter', {
      method: 'POST',
      body: JSON.stringify(newsletterData)
    });
  }

  // Source content endpoints
  async getSourceContent(sourceId) {
    return this.request(`/api/sources/${sourceId}/content`);
  }

  async scrapeSource(sourceId) {
    return this.request(`/api/sources/${sourceId}/scrape`, {
      method: 'POST'
    });
  }
}

export const apiService = new ApiService();
export default apiService;
