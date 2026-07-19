export type { ApiClient } from './client';
export * from './types';
export { createMockClient } from './mock-client';

import { createMockClient } from './mock-client';

// The single API client instance used throughout the app.
// Swap `createMockClient()` for `createHttpClient(baseUrl)` when the backend exists.
export const api = createMockClient();
