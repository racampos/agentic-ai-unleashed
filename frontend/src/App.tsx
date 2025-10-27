import { CLIPanel } from './features/simulator/CLIPanel';
import { TutorPanel } from './features/tutor/TutorPanel';

function App() {
  return (
    <div className="h-screen w-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <h1 className="text-2xl font-bold text-white">
          AI Networking Lab Tutor
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Interactive CLI simulator with AI-powered guidance
        </p>
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

export default App;
