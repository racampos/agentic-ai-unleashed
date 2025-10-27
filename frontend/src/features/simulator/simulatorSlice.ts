import { createSlice, PayloadAction } from '@reduxjs/toolkit';

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
  },
  lastError: null,
};

export const simulatorSlice = createSlice({
  name: 'simulator',
  initialState,
  reducers: {
    setDevice: (state, action: PayloadAction<string>) => {
      state.currentDevice = action.payload;
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
    error: (state, action: PayloadAction<string>) => {
      state.lastError = action.payload;
    },
  },
});

export const {
  setDevice,
  connectionStatusChanged,
  cliResponseReceived,
  error,
} = simulatorSlice.actions;

export default simulatorSlice.reducer;
