import axios from 'axios';
import type { UnifiedEvent } from './types';

// Connects to your Uvicorn backend
const API_URL = 'http://127.0.0.1:8000'; 

const api = axios.create({
  baseURL: API_URL,
});

export const fetchEvents = async (days: number = 7): Promise<UnifiedEvent[]> => {
  const response = await api.get(`/events?days=${days}`);
  return response.data;
};

export const fetchAccounts = async () => {
  const response = await api.get('/auth/accounts');
  return response.data;
};

export const disconnectAccount = async (accountKey: string, userId: string = 'test_user') => {
  const response = await api.delete(`/auth/accounts/${accountKey}`, {
    params: { user_id: userId }
  });
  return response.data;
};

// --- NEW CRUD OPERATIONS ---

export const createEvent = async (event: Partial<UnifiedEvent>, targetAccount: string[] = ['all']): Promise<UnifiedEvent> => {
  const response = await api.post(`/events`, event, {
    params: { target_account: targetAccount },
    paramsSerializer: { indexes: null } // Prevents bracket notation like target_account[]=...
  });
  return response.data;
};

export const updateEvent = async (unifiedId: string, eventData: UnifiedEvent): Promise<UnifiedEvent> => {
  const response = await api.put(`/events/${unifiedId}`, eventData);
  return response.data;
};

export const deleteEvent = async (id: string, originalIds: Record<string, string>) => {
  const response = await api.delete(`/events/${id}`, {
    params: { original_ids: JSON.stringify(originalIds) }
  });
  return response.data;
};

// --- AUTH URLs ---

export const getGoogleLoginUrl = () => `${API_URL}/auth/google/login`;
export const getMicrosoftLoginUrl = () => `${API_URL}/auth/microsoft/login`;