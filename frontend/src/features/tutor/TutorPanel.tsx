import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import type { RootState, AppDispatch } from '../../app/store';
import {
  setSession,
  addMessage,
  setLoading,
  setError,
} from './tutorSlice';
import { tutorAPI } from '../../api/TutorAPI';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import type { Message } from '../../types';

interface TutorPanelProps {
  labId?: string;
}

export const TutorPanel: React.FC<TutorPanelProps> = ({ labId: propLabId }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { session, messages, isLoading, error } = useSelector(
    (state: RootState) => state.tutor
  );
  const currentDevice = useSelector((state: RootState) => state.simulator.currentDevice);
  const cliHistory = useSelector((state: RootState) => {
    if (!currentDevice || !state.simulator.deviceStates[currentDevice]) {
      return [];
    }
    return state.simulator.deviceStates[currentDevice].history;
  });

  const [labId, setLabId] = useState(propLabId || '');
  const [masteryLevel, setMasteryLevel] = useState<'novice' | 'intermediate' | 'advanced'>('novice');
  const [showSessionSetup, setShowSessionSetup] = useState(true);

  // Initialize session
  const handleStartSession = async () => {
    if (!labId.trim()) {
      dispatch(setError('Please enter a Lab ID'));
      return;
    }

    try {
      dispatch(setLoading(true));
      dispatch(setError(null));

      const newSession = await tutorAPI.startSession({
        lab_id: labId.trim(),
        mastery_level: masteryLevel,
      });

      dispatch(setSession(newSession));
      setShowSessionSetup(false);

      // Add welcome message
      const welcomeMessage: Message = {
        role: 'system',
        content: `Session started for Lab: ${labId} (${masteryLevel} level)`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(welcomeMessage));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start session';
      dispatch(setError(errorMessage));
    } finally {
      dispatch(setLoading(false));
    }
  };

  // Auto-start session if labId is provided as prop
  useEffect(() => {
    if (propLabId && !session) {
      handleStartSession();
    }
  }, [propLabId, session]);

  // Send message to tutor
  const handleSendMessage = async (messageText: string) => {
    if (!session) {
      dispatch(setError('No active session'));
      return;
    }

    try {
      dispatch(setLoading(true));
      dispatch(setError(null));

      // Add user message to UI
      const userMessage: Message = {
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(userMessage));

      // Send to API with CLI history
      console.log('[TutorPanel] Sending message with CLI history:', {
        historyCount: cliHistory.length,
        history: cliHistory,
      });
      const response = await tutorAPI.sendMessage({
        session_id: session.session_id,
        user_message: messageText,
        cli_history: cliHistory,
      });

      // Add assistant response to UI
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(assistantMessage));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      dispatch(setError(errorMessage));

      // Add error message to chat
      const errorMsg: Message = {
        role: 'system',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(errorMsg));
    } finally {
      dispatch(setLoading(false));
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <h2 className="text-lg font-semibold text-white">AI Tutor</h2>
        {session && (
          <div className="text-sm text-gray-400 mt-1">
            Lab: {session.lab_id} | Level: {session.mastery_level}
          </div>
        )}
      </div>

      {/* Session Setup */}
      {showSessionSetup && !session && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-semibold text-white mb-4">
              Start a New Session
            </h3>

            <div className="space-y-4">
              {!propLabId && (
                <div>
                  <label
                    htmlFor="labId"
                    className="block text-sm font-medium text-gray-300 mb-2"
                  >
                    Lab ID
                  </label>
                  <input
                    id="labId"
                    type="text"
                    value={labId}
                    onChange={(e) => setLabId(e.target.value)}
                    placeholder="e.g., BGP-101"
                    className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Mastery Level
                </label>
                <div className="space-y-2">
                  {(['novice', 'intermediate', 'advanced'] as const).map(
                    (level) => (
                      <label
                        key={level}
                        className="flex items-center text-gray-300 cursor-pointer"
                      >
                        <input
                          type="radio"
                          name="masteryLevel"
                          value={level}
                          checked={masteryLevel === level}
                          onChange={(e) =>
                            setMasteryLevel(
                              e.target.value as 'novice' | 'intermediate' | 'advanced'
                            )
                          }
                          className="mr-2"
                        />
                        <span className="capitalize">{level}</span>
                      </label>
                    )
                  )}
                </div>
              </div>

              {error && (
                <div className="text-red-400 text-sm">{error}</div>
              )}

              <button
                onClick={handleStartSession}
                disabled={isLoading || !labId.trim()}
                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Starting...' : 'Start Session'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      {session && !showSessionSetup && (
        <>
          <MessageList messages={messages} />
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            placeholder={
              isLoading ? 'AI is thinking...' : 'Ask a question or describe what you need help with...'
            }
          />
        </>
      )}

      {/* Error Display (if any) */}
      {error && session && (
        <div className="px-4 py-2 bg-red-900 text-red-200 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};
