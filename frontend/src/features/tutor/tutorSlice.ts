import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { Message, LabSession } from '../../types';

interface TutorState {
  session: LabSession | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

const initialState: TutorState = {
  session: null,
  messages: [],
  isLoading: false,
  error: null,
};

export const tutorSlice = createSlice({
  name: 'tutor',
  initialState,
  reducers: {
    setSession: (state, action: PayloadAction<LabSession>) => {
      state.session = action.payload;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
  },
});

export const {
  setSession,
  addMessage,
  setLoading,
  setError,
  clearMessages,
} = tutorSlice.actions;

export default tutorSlice.reducer;
