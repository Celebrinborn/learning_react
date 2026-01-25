// Stub auth service - doesn't do anything real yet
export interface User {
  id: string;
  name: string;
  email: string;
}
class AuthService {
  private readonly TOKEN_KEY = 'auth_token';

  // Stub: Just simulates login without actual authentication
  async login(username: string, password: string): Promise<User> {
    console.log('Stub login called with:', username);
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Return mock user
    const mockUser: User = {
      id: '1',
      name: username || 'Guest User',
      email: `${username}@example.com`,
    };
    
    localStorage.setItem(this.TOKEN_KEY, 'mock-token-123');
    return mockUser;
  }

  // Stub: Just clears local storage
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  // Stub: Returns mock user if token exists, null otherwise
  getCurrentUser(): User | null {
    const token = localStorage.getItem(this.TOKEN_KEY);
    if (!token) return null;

    // Return mock user
    return {
      id: '1',
      name: 'Guest User',
      email: 'guest@example.com',
    };
  }

  // Stub: Returns mock token or null
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }
}

export const authService = new AuthService();
