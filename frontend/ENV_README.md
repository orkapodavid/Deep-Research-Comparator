# Frontend Environment Configuration

This directory contains environment configuration files for the React frontend application.

## Environment Files

- **`.env`** - Default environment variables (created automatically)
- **`.env.local`** - Local development overrides (gitignored)
- **`.env.development`** - Development-specific settings
- **`.env.production`** - Production-specific settings
- **`.env.example`** - Template file for new environments

## Required Environment Variables

### `VITE_API_BASE_URL`
- **Description**: The base URL for the backend API
- **Default**: `http://localhost:5001`
- **Development**: `http://localhost:5001`
- **Production**: Update to your production backend URL

### `VITE_DEBUG_MODE` (Optional)
- **Description**: Enable debug mode for additional logging
- **Default**: `false`
- **Development**: `true`
- **Production**: `false`

## Setup Instructions

1. **Automatic Setup** (Recommended):
   ```bash
   # From project root
   ./entrypoint.sh development
   ```

2. **Manual Setup**:
   ```bash
   cd frontend
   cp .env.example .env
   # Edit .env with your values
   ```

## Usage

### Development
```bash
npm run dev          # Uses .env.development
npm run dev:local    # Uses .env.local
```

### Production Build
```bash
npm run build                # Uses .env.production
npm run build:production     # Explicit production build
```

## Important Notes

- All Vite environment variables must be prefixed with `VITE_`
- Environment files are processed in this order (later files override earlier ones):
  1. `.env`
  2. `.env.local`
  3. `.env.[mode]` (e.g., `.env.development`)
  4. `.env.[mode].local`
- The `.env.local` file is gitignored for local overrides
- Never commit sensitive data to environment files tracked by git

## Troubleshooting

### Environment Variable Not Loading
1. Ensure the variable is prefixed with `VITE_`
2. Check the file naming and location
3. Restart the development server after changes
4. Verify TypeScript types in `src/vite-env.d.ts`

### API Connection Issues
1. Verify `VITE_API_BASE_URL` points to the running backend
2. Check backend is running on the specified port
3. Ensure no trailing slashes in the URL
4. Check CORS configuration if accessing from different domains