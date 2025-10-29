import { useEffect, useState, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { Terminal } from './Terminal';
import type { CLITrigger } from '../../api/SimulatorAPI';
import { SimulatorAPI } from '../../api/SimulatorAPI';
import { setDevice } from './simulatorSlice';
import type { AppDispatch } from '../../app/store';
import type { Device } from '../../types';

export const CLIPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [devices, setDevices] = useState<Device[]>([]);
  const [activeDeviceId, setActiveDeviceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const simulatorRefs = useRef<Map<string, SimulatorAPI>>(new Map());

  const baseUrl = import.meta.env.VITE_SIMULATOR_WS_URL || 'http://localhost:8000';

  // Fetch devices on mount
  useEffect(() => {
    const loadDevices = async () => {
      try {
        setLoading(true);
        setError(null);
        const fetchedDevices = await SimulatorAPI.fetchDevices(baseUrl);
        console.log('[CLIPanel] Fetched devices:', fetchedDevices);
        setDevices(fetchedDevices);

        // Select the first device by default
        if (fetchedDevices.length > 0) {
          setActiveDeviceId(fetchedDevices[0].id);
        }
      } catch (err) {
        console.error('[CLIPanel] Failed to fetch devices:', err);
        setError('Failed to load devices from simulator');
      } finally {
        setLoading(false);
      }
    };

    loadDevices();
  }, [baseUrl]);

  // Initialize simulator for active device
  useEffect(() => {
    if (!activeDeviceId) return;

    // Check if we already have a connection for this device
    if (simulatorRefs.current.has(activeDeviceId)) {
      console.log(`[CLIPanel] Using existing connection for ${activeDeviceId}`);
      return;
    }

    // Create new simulator instance
    const newSimulator = SimulatorAPI.create({
      baseUrl,
      deviceId: activeDeviceId,
      dispatch,
    });

    // Initialize connection
    newSimulator
      .initialize()
      .then(() => {
        console.log(`[CLIPanel] Connected to device: ${activeDeviceId}`);
        dispatch(setDevice(activeDeviceId));
        simulatorRefs.current.set(activeDeviceId, newSimulator);
      })
      .catch((error) => {
        console.error(`[CLIPanel] Failed to connect to device ${activeDeviceId}:`, error);
      });

    // Cleanup on unmount
    return () => {
      // Note: We don't disconnect here because we want to keep connections alive
      // when switching tabs. Connections will be cleaned up on component unmount.
    };
  }, [activeDeviceId, baseUrl, dispatch]);

  // Cleanup all connections on unmount
  useEffect(() => {
    return () => {
      simulatorRefs.current.forEach((simulator) => {
        simulator.disconnect();
      });
      simulatorRefs.current.clear();
    };
  }, []);

  const createCommandHandler = (deviceId: string) => {
    return (text: string, trigger: CLITrigger) => {
      const simulator = simulatorRefs.current.get(deviceId);
      if (!simulator) {
        console.log(`[CLIPanel:handleCommand] No simulator for device ${deviceId}`);
        return;
      }

      console.log('[CLIPanel:handleCommand] Sending command:', { text, trigger, deviceId });
      simulator.sendCommand(text, trigger);
    };
  };

  const handleTabClick = (deviceId: string) => {
    setActiveDeviceId(deviceId);
    dispatch(setDevice(deviceId));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-gray-400">
        <div className="text-center">
          <div className="mb-2">Loading devices...</div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-red-400">
        <div className="text-center">
          <div className="mb-2">Error: {error}</div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (devices.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-gray-400">
        <div className="text-center">
          <div className="mb-2">No devices found in topology</div>
          <div className="text-sm text-gray-500">Please create devices in the simulator first</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Device tabs */}
      <div className="flex border-b border-gray-700 bg-gray-800">
        {devices.map((device) => (
          <button
            key={device.id}
            onClick={() => handleTabClick(device.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeDeviceId === device.id
                ? 'bg-gray-900 text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
            }`}
          >
            {device.name}
          </button>
        ))}
      </div>

      {/* Terminals - Keep all mounted and render off-screen when not active */}
      <div className="flex-1 min-h-0 relative">
        {devices.map((device) => (
          <div
            key={device.id}
            className="absolute inset-0"
            style={{
              visibility: activeDeviceId === device.id ? 'visible' : 'hidden',
              zIndex: activeDeviceId === device.id ? 1 : 0,
            }}
          >
            <Terminal
              deviceId={device.id}
              onCommand={createCommandHandler(device.id)}
              isActive={activeDeviceId === device.id}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
