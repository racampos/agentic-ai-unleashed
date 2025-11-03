import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false);

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

  // Handle panel resizing with stable callbacks
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDraggingRef.current) return;
    e.preventDefault();

    const newWidth = (e.clientX / window.innerWidth) * 100;
    // Constrain between 20% and 80%
    if (newWidth >= 20 && newWidth <= 80) {
      setLeftPanelWidth(newWidth);
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    if (!isDraggingRef.current) return;

    isDraggingRef.current = false;
    setIsDragging(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';

    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.removeEventListener('selectstart', preventSelection);
  }, [handleMouseMove]);

  const preventSelection = useCallback((e: Event) => {
    e.preventDefault();
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();

    isDraggingRef.current = true;
    setIsDragging(true);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('selectstart', preventSelection);
  }, [handleMouseMove, handleMouseUp, preventSelection]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('selectstart', preventSelection);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [handleMouseMove, handleMouseUp, preventSelection]);

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading lab...</p>
        </div>
      </div>
    );
  }

  if (error || !lab) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-gray-900">
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
    <div className="h-full w-full flex flex-col bg-gray-900">
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
      <div className="flex-1 flex min-h-0 relative">
        {/* Drag Overlay - prevents interference from underlying elements */}
        {isDragging && (
          <div className="absolute inset-0 z-50 cursor-col-resize" />
        )}

        {/* CLI Simulator Panel - Left */}
        <div
          className="border-r border-gray-700"
          style={{ width: `${leftPanelWidth}%` }}
        >
          <CLIPanel />
        </div>

        {/* Resizable Divider */}
        <div
          className="w-1 bg-gray-700 hover:bg-blue-500 cursor-col-resize transition-colors flex-shrink-0 relative z-10"
          onMouseDown={handleMouseDown}
        />

        {/* Right Panel with Tabs */}
        <div
          className="flex flex-col"
          style={{ width: `${100 - leftPanelWidth}%` }}
        >
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
          <div className="flex-1 min-h-0 overflow-hidden relative">
            {/* AI Tutor Tab */}
            <div className={`h-full ${activeTab === 'tutor' ? 'block' : 'hidden'}`}>
              <TutorPanel labId={labId} />
            </div>

            {/* Lab Info Tab */}
            <div className={`h-full overflow-y-auto bg-gray-850 ${activeTab === 'labinfo' ? 'block' : 'hidden'}`}>
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
                  <div className="prose prose-invert prose-sm max-w-none">
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
                      {lab.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
