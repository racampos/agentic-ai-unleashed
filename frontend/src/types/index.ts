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

// Lab types
export interface LabMetadata {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimated_time: number; // minutes
  topology_file: string | null;
  diagram_file: string | null;
  lesson_file: string | null;
  prerequisites: string[];
}

export interface Lab {
  metadata: LabMetadata;
  content: string; // Markdown content
}

export interface LabListResponse {
  labs: LabMetadata[];
  count: number;
}

export interface DeploymentDevice {
  id: string;
  name: string;
  type: string;
  status: 'created' | 'already_exists' | 'error';
  error?: string;
}

export interface DeploymentConnection {
  name: string;
  endpoints?: string[];
  status: 'created' | 'error';
  error?: string;
}

export interface DeploymentResult {
  lab_id: string;
  lab_title: string;
  cleanup: {
    devices_deleted: number;
    connections_deleted: number;
    errors: string[];
  };
  devices: DeploymentDevice[];
  connections: DeploymentConnection[];
  interfaces_ready: boolean;
  summary: {
    devices_created: number;
    devices_failed: number;
    connections_created: number;
    connections_failed: number;
  };
  message: string;
}
