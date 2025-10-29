import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { CLIPanel } from '../simulator/CLIPanel';
import { TutorPanel } from '../tutor/TutorPanel';
import { labsAPI } from '../../api/LabsAPI';
import type { Lab } from '../../types';

export function LabWorkspace() {
  const { labId } = useParams<{ labId: string }>();
  const navigate = useNavigate();
  const [lab, setLab] = useState<Lab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'tutor' | 'labinfo'>('tutor');

  // Fetch lab data on mount
  useEffect(() => {
    async function fetchLab() {
      if (!labId) {
        setError('No lab ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const labData = await labsAPI.getLab(labId);
        setLab(labData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lab');
      } finally {
        setLoading(false);
      }
    }

    fetchLab();
  }, [labId]);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading lab...</p>
        </div>
      </div>
    );
  }

  if (error || !lab) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Lab not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Back to Labs
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {lab.metadata.title}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            {lab.metadata.difficulty} • {lab.metadata.estimated_time} minutes
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Back to Labs
          </button>
        </div>
      </header>

      {/* Main Content - Two Panel Layout */}
      <div className="flex-1 flex min-h-0">
        {/* CLI Simulator Panel - Left */}
        <div className="w-1/2 border-r border-gray-700">
          <CLIPanel />
        </div>

        {/* Right Panel with Tabs */}
        <div className="w-1/2 flex flex-col">
          {/* Tab Headers */}
          <div className="flex border-b border-gray-700 bg-gray-800 flex-shrink-0">
            <button
              onClick={() => setActiveTab('tutor')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'tutor'
                  ? 'text-white border-b-2 border-blue-500 bg-gray-750'
                  : 'text-gray-400 hover:text-gray-300 hover:bg-gray-750'
              }`}
            >
              AI Tutor
            </button>
            <button
              onClick={() => setActiveTab('labinfo')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'labinfo'
                  ? 'text-white border-b-2 border-blue-500 bg-gray-750'
                  : 'text-gray-400 hover:text-gray-300 hover:bg-gray-750'
              }`}
            >
              Lab Info
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 min-h-0 overflow-hidden">
            {/* AI Tutor Tab */}
            {activeTab === 'tutor' && (
              <TutorPanel labId={labId} />
            )}

            {/* Lab Info Tab */}
            {activeTab === 'labinfo' && (
              <div className="h-full overflow-y-auto bg-gray-850">
                <div className="p-6">
                  {/* Network Diagram */}
                  {lab.metadata.diagram_file && (
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-white mb-3">Network Topology</h3>
                      <img
                        src={labsAPI.getDiagramUrl(lab.metadata.id)}
                        alt="Network Topology"
                        className="w-full rounded border border-gray-700"
                      />
                    </div>
                  )}

                  {/* Lab Description */}
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-white mb-2">Description</h3>
                    <p className="text-sm text-gray-400">{lab.metadata.description}</p>
                  </div>

                  {/* Prerequisites */}
                  {lab.metadata.prerequisites.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-white mb-2">Prerequisites</h3>
                      <ul className="text-sm text-gray-400 list-disc list-inside">
                        {lab.metadata.prerequisites.map((prereq, idx) => (
                          <li key={idx}>{prereq}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Lab Instructions */}
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-2">Instructions</h3>
                    <div className="text-sm text-gray-400 whitespace-pre-wrap">
                      {lab.content}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
