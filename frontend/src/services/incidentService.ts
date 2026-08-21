import { fetchApi } from './api';
import type { Incident } from '../types';

export const incidentService = {
  createIncident: async (incidentData: any): Promise<Incident> => {
    return fetchApi('/incidents', {
      method: 'POST',
      body: JSON.stringify(incidentData),
    });
  },

  getMyIncidents: async (): Promise<Incident[]> => {
    return fetchApi('/incidents/my');
  },

  getDepartmentIncidents: async (): Promise<Incident[]> => {
    return fetchApi('/department/incidents');
  },

  getIncident: async (incidentId: string): Promise<Incident> => {
    return fetchApi(`/incidents/${incidentId}`);
  },

  acceptIncident: async (incidentId: string) => {
    return fetchApi(`/incidents/${incidentId}/accept`, { method: 'POST' });
  },

  startIncident: async (incidentId: string) => {
    return fetchApi(`/incidents/${incidentId}/start`, { method: 'POST' });
  },

  resolveIncident: async (incidentId: string) => {
    return fetchApi(`/incidents/${incidentId}/resolve`, { method: 'POST' });
  }
};
