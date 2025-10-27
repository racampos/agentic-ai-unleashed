import type { Message, LabSession, CLIHistoryEntry } from '../types';

interface StartSessionRequest {
  lab_id: string;
  mastery_level: 'novice' | 'intermediate' | 'advanced';
}

interface SendMessageRequest {
  session_id: string;
  user_message: string;
  cli_history?: CLIHistoryEntry[];
}

interface TutorResponse {
  response: string;
  session_id: string;
}

export class TutorAPI {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
  }

  /**
   * Start a new tutoring session
   */
  async startSession(request: StartSessionRequest): Promise<LabSession> {
    try {
      const response = await fetch(`${this.baseUrl}/tutor/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start session');
      }

      const data = await response.json();
      return {
        session_id: data.session_id,
        lab_id: request.lab_id,
        mastery_level: request.mastery_level,
      };
    } catch (error) {
      console.error('Failed to start session:', error);
      throw error;
    }
  }

  /**
   * Send a message to the tutor and get a response
   */
  async sendMessage(request: SendMessageRequest): Promise<TutorResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/tutor/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
      }

      const data = await response.json();
      return {
        response: data.response,
        session_id: data.session_id,
      };
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }

  /**
   * Get chat history for a session
   */
  async getChatHistory(sessionId: string): Promise<Message[]> {
    try {
      const response = await fetch(`${this.baseUrl}/tutor/history/${sessionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get chat history');
      }

      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error('Failed to get chat history:', error);
      throw error;
    }
  }
}

// Singleton instance
export const tutorAPI = new TutorAPI();
