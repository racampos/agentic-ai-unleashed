import { useParams, useNavigate } from 'react-router-dom';
import { CLIPanel } from '../simulator/CLIPanel';
import { TutorPanel } from '../tutor/TutorPanel';

export function LabWorkspace() {
  const { labId } = useParams<{ labId: string }>();
  const navigate = useNavigate();

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            AI Networking Lab Tutor
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Lab: {labId || 'Unknown'}
          </p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Back to Labs
        </button>
      </header>

      {/* Main Content - Split View */}
      <div className="flex-1 flex min-h-0">
        {/* CLI Simulator Panel - Left */}
        <div className="w-1/2 border-r border-gray-700">
          <CLIPanel />
        </div>

        {/* AI Tutor Panel - Right */}
        <div className="w-1/2">
          <TutorPanel />
        </div>
      </div>
    </div>
  );
}
