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

export interface Device {
  id: string;
  type: string;
  name: string;
  hardware: string;
  status: string;
  createdAt: string;
  lastModifiedAt: string;
}
