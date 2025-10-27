import { useEffect, useState, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { Terminal } from './Terminal';
import type { CLITrigger } from '../../api/SimulatorAPI';
import { SimulatorAPI } from '../../api/SimulatorAPI';
import { setDevice } from './simulatorSlice';
import type { AppDispatch } from '../../app/store';

export const CLIPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [deviceId, setDeviceIdLocal] = useState('');
  const simulatorRef = useRef<SimulatorAPI | null>(null);

  // Initialize simulator when device ID changes
  useEffect(() => {
    if (!deviceId) {
      // Cleanup existing connection
      if (simulatorRef.current) {
        simulatorRef.current.disconnect();
        simulatorRef.current = null;
      }
      return;
    }

    // Create new simulator instance
    const baseUrl = import.meta.env.VITE_SIMULATOR_WS_URL || 'http://localhost:8000';
    const newSimulator = SimulatorAPI.create({
      baseUrl,
      deviceId,
      dispatch,
    });

    // Initialize connection
    newSimulator
      .initialize()
      .then(() => {
        console.log(`Connected to device: ${deviceId}`);
        dispatch(setDevice(deviceId));
        simulatorRef.current = newSimulator;
      })
      .catch((error) => {
        console.error('Failed to connect to simulator:', error);
      });

    // Cleanup on unmount or device change
    return () => {
      newSimulator.disconnect();
    };
  }, [deviceId, dispatch]);

  const handleCommand = (text: string, trigger: CLITrigger) => {
    console.log('[CLIPanel:handleCommand] Called with:', { text, trigger, hasSimulator: !!simulatorRef.current, deviceId });
    if (!simulatorRef.current || !deviceId) {
      console.log('[CLIPanel:handleCommand] Blocked - no simulator or deviceId');
      return;
    }
    simulatorRef.current.sendCommand(text, trigger);
  };

  const handleDeviceIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDeviceIdLocal(e.target.value);
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Device selector */}
      <div className="p-3 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center gap-2">
          <label htmlFor="deviceId" className="text-sm text-gray-300">
            Device ID:
          </label>
          <input
            id="deviceId"
            type="text"
            value={deviceId}
            onChange={handleDeviceIdChange}
            placeholder="Enter Device ID (e.g., R1, SW1)"
            className="border border-gray-600 bg-gray-700 text-white p-2 rounded flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Terminal */}
      <div className="flex-1 min-h-0">
        <Terminal deviceId={deviceId} onCommand={handleCommand} />
      </div>
    </div>
  );
};
