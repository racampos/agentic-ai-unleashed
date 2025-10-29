import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { labsAPI } from '../../api/LabsAPI';
import type { LabMetadata, Lab } from '../../types';
import { LabCard } from './LabCard';

export function LabBrowser() {
  const navigate = useNavigate();
  const [labs, setLabs] = useState<LabMetadata[]>([]);
  const [selectedLab, setSelectedLab] = useState<Lab | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startingLab, setStartingLab] = useState(false);

  // Fetch labs on mount
  useEffect(() => {
    async function fetchLabs() {
      try {
        setLoading(true);
        const response = await labsAPI.listLabs();
        setLabs(response.labs);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load labs');
      } finally {
        setLoading(false);
      }
    }

    fetchLabs();
  }, []);

  // Handle lab selection
  const handleSelectLab = async (labId: string) => {
    try {
      const lab = await labsAPI.getLab(labId);
      setSelectedLab(lab);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lab details');
    }
  };

  // Handle start lab
  const handleStartLab = async () => {
    if (!selectedLab) return;

    try {
      setStartingLab(true);
      setError(null);

      // Deploy the topology
      const result = await labsAPI.startLab(selectedLab.metadata.id);

      console.log('Lab started successfully:', result);

      // Navigate to the workspace with the lab ID
      navigate(`/lab/${selectedLab.metadata.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start lab');
    } finally {
      setStartingLab(false);
    }
  };

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading labs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex-shrink-0">
        <h1 className="text-2xl font-bold text-white">
          AI Networking Lab Tutor
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Choose a lab to begin your hands-on learning experience
        </p>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {/* Lab List - Left Side */}
        <div className="w-1/2 border-r border-gray-700 overflow-y-auto p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Available Labs</h2>

          {error && !selectedLab && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="grid gap-4">
            {labs.map((lab) => (
              <LabCard
                key={lab.id}
                lab={lab}
                onSelect={handleSelectLab}
              />
            ))}
          </div>

          {labs.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              No labs available
            </p>
          )}
        </div>

        {/* Lab Details - Right Side */}
        <div className="w-1/2 overflow-y-auto p-6">
          {selectedLab ? (
            <div className="max-w-3xl">
              {/* Header with Title and Start Button */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  {/* Lab Title */}
                  <h2 className="text-2xl font-bold text-white mb-2">
                    {selectedLab.metadata.title}
                  </h2>

                  {/* Lab Metadata */}
                  <div className="flex gap-4">
                    <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">
                      {selectedLab.metadata.difficulty}
                    </span>
                    <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">
                      {selectedLab.metadata.estimated_time} minutes
                    </span>
                    {selectedLab.metadata.prerequisites.length > 0 && (
                      <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">
                        {selectedLab.metadata.prerequisites.length} prerequisite(s)
                      </span>
                    )}
                  </div>
                </div>

                {/* Start Lab Button */}
                <button
                  onClick={handleStartLab}
                  disabled={startingLab}
                  className="ml-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors whitespace-nowrap"
                >
                  {startingLab ? 'Starting Lab...' : 'Start Lab'}
                </button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded mb-6">
                  {error}
                </div>
              )}

              {/* Network Diagram */}
              {selectedLab.metadata.diagram_file && (
                <div className="mb-6 bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Network Topology</h3>
                  <img
                    src={labsAPI.getDiagramUrl(selectedLab.metadata.id)}
                    alt="Network Topology Diagram"
                    className="w-full rounded"
                  />
                </div>
              )}

              {/* Lab Content (Markdown) */}
              <div className="prose prose-invert prose-sm max-w-none mb-6">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ ...props }) => <h1 className="text-2xl font-bold text-white mt-6 mb-4" {...props} />,
                    h2: ({ ...props }) => <h2 className="text-xl font-bold text-white mt-5 mb-3" {...props} />,
                    h3: ({ ...props }) => <h3 className="text-lg font-semibold text-white mt-4 mb-2" {...props} />,
                    p: ({ ...props }) => <p className="text-gray-300 mb-3 leading-relaxed" {...props} />,
                    ul: ({ ...props }) => <ul className="list-disc list-inside text-gray-300 mb-3 space-y-1" {...props} />,
                    ol: ({ ...props }) => <ol className="list-decimal list-inside text-gray-300 mb-3 space-y-1" {...props} />,
                    li: ({ ...props }) => <li className="text-gray-300" {...props} />,
                    code: ({ className, children, ...props }: any) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className="bg-gray-700 text-blue-300 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className="block bg-gray-800 text-green-300 p-3 rounded text-sm font-mono overflow-x-auto whitespace-pre" {...props}>
                          {children}
                        </code>
                      );
                    },
                    pre: ({ ...props }) => <pre className="mb-3" {...props} />,
                    table: ({ ...props }) => (
                      <div className="overflow-x-auto mb-4">
                        <table className="min-w-full border border-gray-700" {...props} />
                      </div>
                    ),
                    thead: ({ ...props }) => <thead className="bg-gray-800" {...props} />,
                    th: ({ ...props }) => <th className="border border-gray-700 px-4 py-2 text-left text-white font-semibold" {...props} />,
                    td: ({ ...props }) => <td className="border border-gray-700 px-4 py-2 text-gray-300" {...props} />,
                    blockquote: ({ ...props }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-400 my-3" {...props} />,
                    a: ({ ...props }) => <a className="text-blue-400 hover:text-blue-300 underline" {...props} />,
                    strong: ({ ...props }) => <strong className="font-bold text-white" {...props} />,
                  }}
                >
                  {selectedLab.content}
                </ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Select a lab to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
