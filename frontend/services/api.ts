import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../constants/api';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  details?: any;
}

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      async (config) => {
        if (!this.token) {
          this.token = await AsyncStorage.getItem('auth_token');
        }
        
        if (this.token) {
          config.headers.Authorization = `Token ${this.token}`;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid, clear stored token
          await this.clearToken();
        }
        return Promise.reject(error);
      }
    );
  }

  async setToken(token: string): Promise<void> {
    this.token = token;
    await AsyncStorage.setItem('auth_token', token);
  }

  async clearToken(): Promise<void> {
    this.token = null;
    await AsyncStorage.removeItem('auth_token');
  }

  async getToken(): Promise<string | null> {
    if (!this.token) {
      this.token = await AsyncStorage.getItem('auth_token');
    }
    return this.token;
  }

  // Generic HTTP methods
  async get<T = any>(url: string, params?: any): Promise<ApiResponse<T>> {
    try {
      console.log('API GET Request:', `${this.api.defaults.baseURL}${url}`, params);
      const response: AxiosResponse<T> = await this.api.get(url, { params });
      console.log('API GET Response:', response.status, response.data);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      console.error('API GET Error:', error);
      return this.handleError(error);
    }
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    try {
      console.log('API POST Request:', `${this.api.defaults.baseURL}${url}`, data);
      const response: AxiosResponse<T> = await this.api.post(url, data, config);
      console.log('API POST Response:', response.status, response.data);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      console.error('API POST Error:', error);
      return this.handleError(error);
    }
  }

  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.api.put(url, data);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.api.delete(url);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  async uploadFile<T = any>(url: string, formData: FormData): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.api.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return this.handleError(error);
    }
  }

  private handleError(error: any): ApiResponse {
    console.error('API Error:', error);
    
    if (error.response) {
      // Server responded with an error status
      return {
        success: false,
        error: error.response.data?.message || error.response.data?.detail || 'Server error',
        details: error.response.data,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        success: false,
        error: 'Network error - please check your connection',
      };
    } else {
      // Something else happened
      return {
        success: false,
        error: error.message || 'An unexpected error occurred',
      };
    }
  }
}

export default new ApiService(); 