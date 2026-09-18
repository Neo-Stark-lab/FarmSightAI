import type { Farm } from '../api/types';

const AUTH_KEY = 'farmsightai_demo_user_id';
const FARMS_KEY = 'farmsight_demo_farms';

export const demoAuth = {
  login: (userId: string) => localStorage.setItem(AUTH_KEY, userId),
  logout: () => localStorage.removeItem(AUTH_KEY),
  isAuthenticated: () => !!localStorage.getItem(AUTH_KEY),
  getUserId: () => localStorage.getItem(AUTH_KEY),
};

// We persist only the successful creation records in the frontend for purely DEMO MODE.
// REAL mode now uses backend persistence.
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
