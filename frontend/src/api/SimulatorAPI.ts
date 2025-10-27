import type { AppDispatch } from '../app/store';
import {
  connectionStatusChanged,
  cliResponseReceived,
  error as dispatchError,
} from '../features/simulator/simulatorSlice';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting';

export type CLITrigger = 'enter' | 'tab' | 'question' | 'up_arrow' | 'down_arrow';

interface CLICommand {
  deviceId: string;
  text: string;
  trigger: CLITrigger;
}

interface SimulatorAPIConfig {
  baseUrl: string;
  deviceId: string;
  dispatch: AppDispatch;
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  maxReconnectDelay?: number;
  connectionTimeout?: number;
  heartbeatInterval?: number;
}

export class SimulatorAPI {
  // Static connection tracking
  private static activeConnections: Map<string, { api: SimulatorAPI; refCount: number }> = new Map();
  private static getInstance(config: SimulatorAPIConfig): SimulatorAPI {
    const existingInstance = Array.from(SimulatorAPI.activeConnections.values()).find(
      ({ api }) => api.baseUrl === config.baseUrl && api.deviceId === config.deviceId
    );

    if (existingInstance) {
      existingInstance.refCount++;
      return existingInstance.api;
    }

    const newInstance = new SimulatorAPI(config);
    return newInstance;
  }

  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectDelay: number;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private connectionTimer: number | null = null;
  private commandQueue: CLICommand[] = [];
  private dispatch: AppDispatch;
  private lastPongTime: number = 0;
  private isInitializing: boolean = false;

  private readonly baseUrl: string;
  private readonly deviceId: string;
  private readonly maxReconnectAttempts: number;
  private readonly initialReconnectDelay: number;
  private readonly maxReconnectDelay: number;
  private readonly connectionTimeout: number;
  private readonly heartbeatInterval: number;

  constructor(config: SimulatorAPIConfig) {
    this.baseUrl = config.baseUrl;
    this.deviceId = config.deviceId;
    this.dispatch = config.dispatch;
    this.maxReconnectAttempts = config.maxReconnectAttempts ?? 5;
    this.initialReconnectDelay = config.initialReconnectDelay ?? 1000;
    this.maxReconnectDelay = config.maxReconnectDelay ?? 30000;
    this.connectionTimeout = config.connectionTimeout ?? 10000;
    this.heartbeatInterval = config.heartbeatInterval ?? 30000;
    this.reconnectDelay = this.initialReconnectDelay;
  }

  public static create(config: SimulatorAPIConfig): SimulatorAPI {
    return SimulatorAPI.getInstance(config);
  }

  /**
   * Initializes the connection to the simulator for a specific device
   */
  public async initialize(): Promise<void> {
    // If we already have a connection for this device, just return
    const connectionKey = this.deviceId;
    if (SimulatorAPI.activeConnections.has(connectionKey)) {
      console.log(`Simulator connection for device ${this.deviceId} already initialized`);
      return;
    }

    // Prevent multiple simultaneous initializations
    if (this.isInitializing) {
      console.log('Simulator connection initialization in progress');
      return;
    }

    this.isInitializing = true;

    try {
      // Add to active connections
      SimulatorAPI.activeConnections.set(connectionKey, { api: this, refCount: 1 });

      // Establish WebSocket connection directly with the device
      await this.connect();
    } catch (error) {
      this.handleError('Connection initialization failed', error as Error);
      throw error;
    } finally {
      this.isInitializing = false;
    }
  }

  /**
   * Establishes WebSocket connection
   */
  private async connect(): Promise<void> {
    if (!this.deviceId) {
      throw new Error('No device ID available');
    }

    this.dispatch(connectionStatusChanged('connecting'));

    try {
      // Connect to the WebSocket endpoint
      const token = import.meta.env.VITE_SIMULATOR_TOKEN || 'TEST_TOKEN';

      // Browser WebSocket API doesn't support custom headers
      // We'll try passing the token as a query parameter
      // If that doesn't work, we may need to send auth in first message
      const wsUrl = `${this.baseUrl.replace('http', 'ws')}/ws?token=${token}`;

      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();

      // Set connection timeout
      this.connectionTimer = window.setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          this.ws?.close();
          this.attemptReconnect();  // Try to reconnect instead of throwing
        }
      }, this.connectionTimeout);

    } catch (error) {
      this.handleError('WebSocket connection failed', error as Error);
      this.attemptReconnect();
    }
  }

  /**
   * Sets up WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      // Clear connection timeout
      if (this.connectionTimer) {
        clearTimeout(this.connectionTimer);
        this.connectionTimer = null;
      }

      this.dispatch(connectionStatusChanged('connected'));
      this.reconnectAttempts = 0;
      this.reconnectDelay = this.initialReconnectDelay;

      // Start heartbeat
      this.startHeartbeat();

      // Process any queued commands
      this.processCommandQueue();
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      this.dispatch(connectionStatusChanged('disconnected'));

      // Always attempt to reconnect unless we explicitly called disconnect
      // Check if this was triggered by our own disconnect call
      const connection = this.deviceId ? SimulatorAPI.activeConnections.get(this.deviceId) : null;
      const isIntentionalDisconnect = connection && connection.refCount <= 0;

      if (!isIntentionalDisconnect) {
        console.log('WebSocket closed unexpectedly, attempting reconnect...');
        this.attemptReconnect();
      }
    };

    this.ws.onerror = () => {
      const error = new Error('WebSocket error event');
      this.handleError('WebSocket error occurred', error);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        // Handle heartbeat response
        if (message.type === 'pong') {
          this.lastPongTime = Date.now();
          return;
        }

        console.log('Received WebSocket message:', message);

        // Handle different message types
        switch (message.type) {
          case 'cli_response':
            this.dispatch(cliResponseReceived({
              content: message.content,
              prompt: message.prompt,
              current_input: message.current_input,
            }));
            break;

          case 'error':
            this.dispatch(dispatchError(message.content));
            break;
        }
      } catch (error) {
        this.handleError('Failed to parse message', error as Error);
      }
    };
  }

  /**
   * Handles error scenarios and dispatches error actions
   */
  private handleError(message: string, error: Error): void {
    console.error(`${message}:`, error);
    this.dispatch(dispatchError(`${message}: ${error.message}`));
  }

  /**
   * Attempts to reconnect to the WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`Maximum reconnect attempts (${this.maxReconnectAttempts}) reached`);
      this.dispatch(connectionStatusChanged('disconnected'));
      return;
    }

    this.reconnectAttempts++;
    this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
    this.dispatch(connectionStatusChanged('reconnecting'));

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`);
    this.reconnectTimer = window.setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnect attempt failed:', error);
        this.attemptReconnect();
      });
    }, this.reconnectDelay);
  }

  /**
   * Starts the heartbeat mechanism
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.lastPongTime = Date.now();
    this.heartbeatTimer = window.setInterval(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.stopHeartbeat();
        return;
      }

      // Check if we've missed too many pongs
      const now = Date.now();
      if (now - this.lastPongTime > this.heartbeatInterval * 3) {
        console.warn('No heartbeat response received for too long');
        this.ws.close();
        this.attemptReconnect();
        return;
      }

      // Send ping message with device ID
      const pingMessage = {
        type: 'ping',
        device_id: this.deviceId,
        metadata: {
          timestamp: now
        }
      };
      this.ws.send(JSON.stringify(pingMessage));
    }, this.heartbeatInterval);
  }

  /**
   * Stops the heartbeat mechanism
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Disconnects from the WebSocket
   */
  public disconnect(): void {
    const currentDeviceId = this.deviceId;
    if (currentDeviceId) {
      const connection = SimulatorAPI.activeConnections.get(currentDeviceId);
      if (connection) {
        connection.refCount--;

        if (connection.refCount <= 0) {
          // Close WebSocket if this is the last reference
          if (this.ws) {
            this.ws.close();
            this.ws = null;
          }

          SimulatorAPI.activeConnections.delete(currentDeviceId);
          this.commandQueue = []; // Clear command queue on intentional disconnect
          this.dispatch(connectionStatusChanged('disconnected'));
        }
      }
    }

    this.stopHeartbeat();
  }

  /**
   * Sends a CLI command to the device
   */
  public sendCommand(text: string, trigger: CLITrigger = 'enter'): void {
    const command: CLICommand = {
      deviceId: this.deviceId,
      text,
      trigger
    };

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not connected, queueing command');
      this.commandQueue.push(command);
      return;
    }

    this.sendCommandToServer(command);
  }

  /**
   * Processes any queued commands
   */
  private processCommandQueue(): void {
    if (!this.commandQueue.length) return;

    console.log(`Processing ${this.commandQueue.length} queued commands`);

    while (this.commandQueue.length > 0) {
      const command = this.commandQueue.shift();
      if (command) {
        this.sendCommandToServer(command);
      }
    }
  }

  /**
   * Sends a command to the server
   */
  private sendCommandToServer(command: CLICommand): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('Cannot send command: WebSocket not connected');
      return;
    }

    const message = {
      type: 'cli',
      device_id: command.deviceId,
      trigger: command.trigger,
      text: command.text,
      metadata: {
        timestamp: Date.now()
      }
    };

    try {
      this.ws.send(JSON.stringify(message));
      console.log('Sent command:', message);
    } catch (error) {
      this.handleError('Failed to send command', error as Error);
    }
  }
}
