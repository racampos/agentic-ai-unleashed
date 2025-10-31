import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { CLIHistoryEntry } from '../../types';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting';

interface CLIResponse {
  content: string;
  prompt: string;
  current_input: string;
  deviceId: string;
}

interface DeviceCLIState {
  output: string;
  prompt: string;
  current_input: string;
  sequence: number;
  history: CLIHistoryEntry[];
}

interface SimulatorState {
  connectionStatus: ConnectionStatus;
  currentDevice: string | null;
  deviceStates: Record<string, DeviceCLIState>;
  lastError: string | null;
}

const initialState: SimulatorState = {
  connectionStatus: 'disconnected',
  currentDevice: null,
  deviceStates: {},
  lastError: null,
};

const getOrCreateDeviceState = (state: SimulatorState, deviceId: string): DeviceCLIState => {
  if (!state.deviceStates[deviceId]) {
    state.deviceStates[deviceId] = {
      output: '',
      prompt: '',
      current_input: '',
      sequence: 0,
      history: [],
    };
  }
  return state.deviceStates[deviceId];
};

export const simulatorSlice = createSlice({
  name: 'simulator',
  initialState,
  reducers: {
    setDevice: (state, action: PayloadAction<string>) => {
      state.currentDevice = action.payload;
      // Initialize device state if it doesn't exist
      getOrCreateDeviceState(state, action.payload);
    },
    connectionStatusChanged: (state, action: PayloadAction<ConnectionStatus>) => {
      state.connectionStatus = action.payload;
    },
    cliResponseReceived: (state, action: PayloadAction<CLIResponse>) => {
      const deviceState = getOrCreateDeviceState(state, action.payload.deviceId);
      deviceState.output = action.payload.content;
      deviceState.prompt = action.payload.prompt;
      deviceState.current_input = action.payload.current_input;
      deviceState.sequence += 1;
      state.lastError = null;
    },
    addCLIHistoryEntry: (state, action: PayloadAction<CLIHistoryEntry>) => {
      const deviceState = getOrCreateDeviceState(state, action.payload.device_id);
      deviceState.history.push(action.payload);
      // Keep only last 50 entries to avoid memory issues
      if (deviceState.history.length > 50) {
        deviceState.history = deviceState.history.slice(-50);
      }
    },
    clearCLIHistory: (state, action: PayloadAction<string>) => {
      const deviceState = getOrCreateDeviceState(state, action.payload);
      deviceState.history = [];
    },
    error: (state, action: PayloadAction<string>) => {
      state.lastError = action.payload;
    },
    clearAllDeviceStates: (state) => {
      state.deviceStates = {};
      state.currentDevice = null;
    },
  },
});

export const {
  setDevice,
  connectionStatusChanged,
  cliResponseReceived,
  addCLIHistoryEntry,
  clearCLIHistory,
  error,
  clearAllDeviceStates,
} = simulatorSlice.actions;

export default simulatorSlice.reducer;
