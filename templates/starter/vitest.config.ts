// vitest.config.ts
//
// Vitest configuration for unit and integration tests.
// Test files: modules/**/*.test.ts
//
// The test agent and ship agent both run `npm test`. If this config
// is missing or the path aliases don't match tsconfig.json, tests
// will fail with import resolution errors.

import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    // Run tests serially when each test touches the database (default for
    // service tests that call real DB). Set to a number for parallel workers
    // if using a test-per-schema isolation strategy.
    pool:        'forks',
    poolOptions: { forks: { singleFork: true } },

    // Clear mock state between tests
    clearMocks:   true,
    restoreMocks: true,

    // Environment variables for test DB
    env: {
      DATABASE_URL: process.env.TEST_DATABASE_URL ?? process.env.DATABASE_URL ?? '',
    },

    // Setup files run before each test file
    setupFiles: ['./tests/setup.ts'],

    // Test file patterns
    include: [
      'modules/**/*.test.ts',
      'lib/**/*.test.ts',
    ],

    // Coverage (optional — run with: npm test -- --coverage)
    coverage: {
      provider: 'v8',
      include:  ['modules/**/*.ts', 'lib/**/*.ts'],
      exclude:  ['**/*.test.ts', '**/BEHAVIORS.md'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
})
