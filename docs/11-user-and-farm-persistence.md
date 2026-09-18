# Lap 11 — User Accounts + Farm Persistence

## Overview

Lap 11 introduces demo user accounts and backend persistence for farms linked to specific users. It updates both the FastAPI backend and React frontend to handle basic authentication for hackathon/demo purposes without production-grade security (passwords, JWTs, OAuth).

## Backend Changes

1. **User Persistence (`backend/app/persistence.py`)**: 
   - Added a `users` dictionary inside the in-memory `Repository`.
   - Populated the repository with three seeded demo users: Arjun Kumar, Meena Ravi, Kumaravel S.
   - Pre-seeded 4 valid real-world farms belonging to the demo users in Tamil Nadu, using the existing area and geometry calculations.

2. **Farm Ownership (`backend/app/services.py`)**:
   - `FarmService.create` was updated to accept an optional `owner_user_id`.
   - Validates the user exists and attaches the user ID to the new farm record.

3. **API Endpoints (`backend/app/main.py`)**:
   - Updated `POST /api/v1/farms` to optionally capture the `X-Demo-User-Id` header and forward it to `FarmService.create`.
   - Implemented `GET /api/v1/users/{user_id}/farms` to fetch all farms owned by a given user.
   - Allowed `X-Demo-User-Id` in the `CORSMiddleware` configuration.

## Frontend Changes

1. **Demo Identity (`frontend/src/utils/demoPersistence.ts`)**:
   - Changed authentication logic from a generic boolean to tracking the logged-in demo user ID under `farmsightai_demo_user_id`.
   
2. **Login Page (`frontend/src/pages/LoginPage.tsx`)**:
   - Replaced the generic "Continue as demo farmer" button with a selection menu for the three seeded demo accounts.
   
3. **API Client Integration (`frontend/src/api/client.ts`)**:
   - Attached `X-Demo-User-Id` to `POST /farms` requests when a user is authenticated.
   - Added `getUserFarms` method to interface with the new backend endpoint in REAL mode, while retaining fixture mock support for DEMO mode.
   
4. **Farms List (`frontend/src/pages/MyFarmsPage.tsx`)**:
   - Migrated from local storage-only demo persistence to dynamically fetching user-specific farms via the backend `getUserFarms` method when in REAL mode. Added `isLoading` and `error` states to improve the UI resilience.
   
5. **Farm Setup (`frontend/src/pages/FarmSetupPage.tsx`)**:
   - Fetches the active demo user ID from `demoAuth.getUserId()` and passes it to the `apiClient.createFarm` call to properly link newly mapped farms.

## Testing

- Backend coverage added in `backend/tests/test_users.py` to ensure user endpoints, creation validation, and ownership integrity work as expected.
- Frontend test suite updated to align `apiClient.createFarm` mock expectations with the new `userId` parameter.

## Guardrails

- The data pipeline and polling mechanism for analyses remains completely untouched, retaining perfect compatibility with earlier laps.
- Existing frontend rendering components and visualizations are unmodified and display data for any appropriately owned farm accurately.
