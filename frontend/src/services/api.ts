import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to get the token from localStorage
const getToken = () => localStorage.getItem('token');

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// User types (can be expanded or moved to a dedicated types file)
export interface User {
  id: string;
  username: string;
  role: 'parent' | 'kid';
  points?: number;
}

export interface UserCreate {
  username: string;
  password: string;
  role: 'parent' | 'kid';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Store Item types
export interface StoreItem {
    id: string;
    name: string;
    description?: string;
    points_cost: number;
}

export interface StoreItemCreate {
    name: string;
    description?: string;
    points_cost: number;
}

export interface PointsAwardData {
    kid_username: string;
    points: number;
    reason?: string;
}

export interface RedemptionRequestData {
    item_id: string;
}


// --- API Service Functions ---

// Auth
export const login = (data: FormData) => apiClient.post<TokenResponse>('/token', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' } // FastAPI's OAuth2PasswordRequestForm expects this
});
export const signup = (data: UserCreate) => apiClient.post<User>('/users/', data);
export const getCurrentUser = () => apiClient.get<User>('/users/me/');

// Store Items
export const getStoreItems = () => apiClient.get<StoreItem[]>('/store/items/');
export const createStoreItem = (data: StoreItemCreate) => apiClient.post<StoreItem>('/store/items/', data);
export const updateStoreItem = (itemId: string, data: StoreItemCreate) => apiClient.put<StoreItem>(`/store/items/${itemId}`, data);
export const deleteStoreItem = (itemId: string) => apiClient.delete(`/store/items/${itemId}`);
export const getStoreItemById = (itemId: string) => apiClient.get<StoreItem>(`/store/items/${itemId}`);


// Points Management
export const awardPoints = (data: PointsAwardData) => apiClient.post<User>('/kids/award-points/', data);
export const redeemItem = (data: RedemptionRequestData) => apiClient.post<User>('/kids/redeem-item/', data);

export default apiClient;