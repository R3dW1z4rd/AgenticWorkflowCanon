// lib/logger.ts
//
// Application logger. All structured logging goes through this instance.
// Never use console.log or console.error in production code — use this logger.
//
// Canon rule: every successful service write calls logger.info() with a
// structured object and a short message string.
//
// Pattern:
//   logger.info(
//     { contractId: record.id, orgId: ctx.orgId },
//     'contract created'
//   )
//
// The structured object fields are indexed by your log aggregator.
// The message string is for human readers.
//
// Log levels:
//   logger.error() — unexpected failures (DB connection lost, external API down)
//   logger.warn()  — expected degraded states (rate limit approaching, cache miss)
//   logger.info()  — normal operations (record created, record updated)
//   logger.debug() — development detail (query params, response shapes)
//
// Canon reference: Section 10 (Observability)

import pino from 'pino'

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',

  // In local development, pretty-print for readability:
  ...(process.env.NODE_ENV === 'development' && {
    transport: {
      target: 'pino-pretty',
      options: { colorize: true },
    },
  }),

  // Base fields appended to every log entry:
  base: {
    service: process.env.SERVICE_NAME ?? 'app',
    env:     process.env.NODE_ENV     ?? 'development',
  },
})
