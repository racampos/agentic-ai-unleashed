import type { LabListResponse, Lab, StartDeploymentResponse, DeploymentStatus } from '../types';

export class LabsAPI {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888';
  }

  /**
   * Get list of all available labs
   */
  async listLabs(): Promise<LabListResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/labs`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch labs');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list labs:', error);
      throw error;
    }
  }

  /**
   * Get details for a specific lab
   */
  async getLab(labId: string): Promise<Lab> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/labs/${labId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lab details');
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get lab ${labId}:`, error);
      throw error;
    }
  }

  /**
   * Get the URL for a lab's topology diagram
   */
  getDiagramUrl(labId: string): string {
    return `${this.baseUrl}/api/v1/labs/${labId}/diagram`;
  }

  /**
   * Start (deploy) a lab topology to the simulator
   * Returns immediately with a deployment_id to track progress
   */
  async startLab(labId: string): Promise<StartDeploymentResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/labs/${labId}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start lab');
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to start lab ${labId}:`, error);
      throw error;
    }
  }

  /**
   * Get the current status of a deployment
   */
  async getDeploymentStatus(labId: string, deploymentId: string): Promise<DeploymentStatus> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/labs/${labId}/deployment-status/${deploymentId}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get deployment status');
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get deployment status ${deploymentId}:`, error);
      throw error;
    }
  }
}

// Singleton instance
export const labsAPI = new LabsAPI();
