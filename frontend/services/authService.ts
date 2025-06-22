import apiService, { ApiResponse } from './api';
import { API_ENDPOINTS } from '../constants/api';

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_verified: boolean;
  student_profile: StudentProfile;
}

export interface StudentProfile {
  student_id: string;
  region?: string;
  department?: string;
  current_semester: number;
  enrollment_year: number;
  courses: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  message: string;
}

class AuthService {
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> {
    const response = await apiService.post<AuthResponse>(
      API_ENDPOINTS.LOGIN,
      credentials
    );
    
    if (response.success && response.data?.token) {
      await apiService.setToken(response.data.token);
    }
    
    return response;
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
    const response = await apiService.post<AuthResponse>(
      API_ENDPOINTS.REGISTER,
      userData
    );
    
    if (response.success && response.data?.token) {
      await apiService.setToken(response.data.token);
    }
    
    return response;
  }

  async logout(): Promise<ApiResponse> {
    const response = await apiService.post(API_ENDPOINTS.LOGOUT);
    await apiService.clearToken();
    return response;
  }

  async getProfile(): Promise<ApiResponse<User>> {
    return await apiService.get<User>(API_ENDPOINTS.PROFILE);
  }

  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    return await apiService.put<User>(API_ENDPOINTS.PROFILE, userData);
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await apiService.getToken();
    return !!token;
  }
}

export default new AuthService(); 