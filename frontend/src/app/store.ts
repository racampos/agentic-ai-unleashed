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
