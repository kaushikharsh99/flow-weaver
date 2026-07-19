export type { ApiClient } from './client';
export * from './types';
export { createMockClient } from './mock-client';
export { createHttpClient } from './http-client';

import { createMockClient } from './mock-client';
import { createHttpClient } from './http-client';

export const isMockMode = import.meta.env.VITE_USE_MOCK_API !== 'false';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = isMockMode 
  ? createMockClient() 
  : createHttpClient(API_URL);
