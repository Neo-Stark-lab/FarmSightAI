import type { Farm } from '../api/types';

const AUTH_KEY = 'farmsight_demo_authenticated';
const FARMS_KEY = 'farmsight_demo_farms';

export const demoAuth = {
  login: () => localStorage.setItem(AUTH_KEY, 'true'),
  logout: () => localStorage.removeItem(AUTH_KEY),
  isAuthenticated: () => localStorage.getItem(AUTH_KEY) === 'true',
};

// We cannot fetch a list of farms from the backend, so we persist
// only the successful creation records in the frontend for demo purposes.
export const demoFarms = {
  addFarm: (farm: Farm) => {
    const existing = demoFarms.getFarms();
    // Prevent duplicates if multiple components trigger
    if (!existing.find(f => f.id === farm.id)) {
      existing.unshift(farm);
      localStorage.setItem(FARMS_KEY, JSON.stringify(existing));
    }
  },
  getFarms: (): Farm[] => {
    try {
      const data = localStorage.getItem(FARMS_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }
};
