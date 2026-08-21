import { fetchApi } from './api';
import type { User } from '../types';

export const authService = {
  login: async (email: string, password: string) => {
    // Form data is required by OAuth2PasswordRequestForm in FastAPI
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    return fetchApi('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
  },

  register: async (userData: any) => {
    return fetchApi('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  getMe: async (): Promise<User> => {
    return fetchApi('/auth/me');
  }
};
