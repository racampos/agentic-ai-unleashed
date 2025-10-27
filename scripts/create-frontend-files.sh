#!/bin/bash

# This script creates all the frontend files for the AI Tutor application
# Run from the project root directory

cd "$(dirname "$0")/.." || exit 1

echo "Creating frontend files..."

# Create Redux store
cat > frontend/src/app/store.ts << 'EOF'
import { configureStore } from '@reduxjs/toolkit';
import simulatorReducer from '../features/simulator/simulatorSlice';
import tutorReducer from '../features/tutor/tutorSlice';

export const store = configureStore({
  reducer: {
    simulator: simulatorReducer,
    tutor: tutorReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
EOF

# Create types
cat > frontend/src/types/index.ts << 'EOF'
export interface CLIHistoryEntry {
  command: string;
  output: string;
  timestamp: string;
  device_id: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface LabSession {
  session_id: string;
  lab_id: string;
  mastery_level: 'novice' | 'intermediate' | 'advanced';
}
EOF

echo "✓ Created store and types"

# Create Simulator Slice (adapted from user's code)
cat > frontend/src/features/simulator/simulatorSlice.ts << 'EOF'
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
EOF

echo "✓ Created simulator slice"

echo "All frontend base files created successfully!"
echo "Next steps:"
echo "1. Review the generated files"
echo "2. Run additional creation scripts for components"
echo "3. npm run dev to start the development server"
