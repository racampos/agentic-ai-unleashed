import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { CLIHistoryEntry } from '../../types';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting';

interface CLIResponse {
  content: string;
  prompt: string;
  current_input: string;
}

interface SimulatorState {
  connectionStatus: ConnectionStatus;
  currentDevice: string | null;
  cli: {
    output: string;
    prompt: string;
    current_input: string;
    sequence: number;
    history: CLIHistoryEntry[];
  };
  lastError: string | null;
}

const initialState: SimulatorState = {
  connectionStatus: 'disconnected',
  currentDevice: null,
  cli: {
    output: '',
    prompt: '',
    current_input: '',
    sequence: 0,
    history: [],
  },
  lastError: null,
};

export const simulatorSlice = createSlice({
  name: 'simulator',
  initialState,
  reducers: {
    setDevice: (state, action: PayloadAction<string>) => {
      state.currentDevice = action.payload;
      // Clear history when switching devices
      state.cli.history = [];
    },
    connectionStatusChanged: (state, action: PayloadAction<ConnectionStatus>) => {
      state.connectionStatus = action.payload;
    },
    cliResponseReceived: (state, action: PayloadAction<CLIResponse>) => {
      state.cli.output = action.payload.content;
      state.cli.prompt = action.payload.prompt;
      state.cli.current_input = action.payload.current_input;
      state.cli.sequence += 1;
      state.lastError = null;
    },
    addCLIHistoryEntry: (state, action: PayloadAction<CLIHistoryEntry>) => {
      state.cli.history.push(action.payload);
      // Keep only last 50 entries to avoid memory issues
      if (state.cli.history.length > 50) {
        state.cli.history = state.cli.history.slice(-50);
      }
    },
    clearCLIHistory: (state) => {
      state.cli.history = [];
    },
    error: (state, action: PayloadAction<string>) => {
      state.lastError = action.payload;
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
} = simulatorSlice.actions;

export default simulatorSlice.reducer;
