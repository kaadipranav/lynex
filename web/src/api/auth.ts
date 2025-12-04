import { apiClient } from './client';

export interface User {
  id: string;
  email: string;
  name: string | null;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  expires_at: string;
}

const TOKEN_KEY = 'lynex_token';
const USER_KEY = 'lynex_user';

export const authApi = {
  signup: async (email: string, password: string, name?: string) => {
    const response = await apiClient.post<AuthResponse>('/auth/signup', {
      email,
      password,
      name,
    });
    saveAuth(response.data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await apiClient.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    saveAuth(response.data);
    return response.data;
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      clearAuth();
    }
  },

  getMe: async () => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  getToken: () => {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUser: (): User | null => {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem(TOKEN_KEY);
  },
};

function saveAuth(data: AuthResponse) {
  localStorage.setItem(TOKEN_KEY, data.token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));

  // Set default Authorization header for future requests
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  delete apiClient.defaults.headers.common['Authorization'];
}

// Initialize auth header from stored token on load
const storedToken = localStorage.getItem(TOKEN_KEY);
if (storedToken) {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
}
