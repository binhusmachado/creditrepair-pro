import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../services/api';

function ClientDetail() {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchClient();
  }, [id]);

  const fetchClient = async () => {
    try {
      const response = await api.get(`/api/clients/${id}`);
      setClient(response.data);
    } catch (error) {
      console.error('Error fetching client:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-2xl font-bold">{client?.client?.full_name}</h1>
            <p className="text-gray-600">{client?.client?.email}</p>
          </div>

          <div className="flex space-x-8 border-b">
            {['overview', 'reports', 'disputes', 'letters'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-4 font-medium capitalize ${
                  activeTab === tab
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-500'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Credit Reports</p>
                  <p className="text-2xl font-bold">{client?.credit_reports?.length || 0}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Active Disputes</p>
                  <p className="text-2xl font-bold">{client?.disputes?.length || 0}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="text-2xl font-bold text-green-600">Active</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow p-6 md:col-span-3">
              <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
              <div className="flex space-x-4">
                <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Report
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="bg-white rounded-xl shadow">
            {client?.credit_reports?.map((report) => (
              <div key={report.id} className="p-4 border-b">
                <div className="flex justify-between">
                  <div>
                    <p className="font-medium">{report.bureau || 'Unknown Bureau'}</p>
                    <p className="text-sm text-gray-500">{report.upload_date}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{report.equifax_score || '---'}</p>
                    <p className="text-sm text-gray-500">Errors: {report.total_errors}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'disputes' && (
          <div className="bg-white rounded-xl shadow">
            {client?.disputes?.map((dispute) => (
              <div key={dispute.id} className="p-4 border-b">
                <div className="flex justify-between">
                  <div>
                    <p className="font-medium">{dispute.creditor_name}</p>
                    <p className="text-sm text-gray-500">{dispute.bureau} • Round {dispute.round_number}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    dispute.status === 'resolved' 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {dispute.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default ClientDetail;