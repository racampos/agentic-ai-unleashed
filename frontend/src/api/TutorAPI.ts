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
      const response = await fetch(`${this.baseUrl}/api/lab/start`, {
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
   * Send a message to the tutor and get a response (non-streaming)
   */
  async sendMessage(request: SendMessageRequest): Promise<TutorResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: request.session_id,
          message: request.user_message,
          cli_history: request.cli_history || [],
        }),
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
   * Send a message to the tutor with streaming response
   * @param request - The message request
   * @param onChunk - Callback for each text chunk
   * @param onMetadata - Callback for final metadata
   * @param onError - Callback for errors
   */
  async sendMessageStream(
    request: SendMessageRequest,
    onChunk: (text: string) => void,
    onMetadata?: (metadata: any) => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: request.session_id,
          message: request.user_message,
          cli_history: request.cli_history || [],
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
      }

      // Process Server-Sent Events stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));

              if (data.type === 'content') {
                console.log('[TutorAPI] Content chunk received:', data.text);
                onChunk(data.text);
              } else if (data.type === 'metadata') {
                console.log('[TutorAPI] Metadata received:', data);
                onMetadata?.(data);
              } else if (data.type === 'error') {
                onError?.(new Error(data.message));
              } else if (data.type === 'done') {
                // Stream complete
                return;
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send streaming message:', error);
      onError?.(error as Error);
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
