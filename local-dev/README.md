# Trufo Local Development

This directory contains the original React frontend for local development and testing.

## 🚀 Quick Start

```bash
cd local-dev
npm install
npm run dev
```

## 📋 Features

- React frontend with TypeScript
- Tailwind CSS styling
- Vite for development server
- Google OAuth integration
- API integration with Lambda backend

## 🔧 Configuration

1. Copy `.env.example` to `.env`
2. Configure environment variables:
   ```
   VITE_LAMBDA_API_URL=https://your-lambda-function-url
   VITE_GOOGLE_CLIENT_ID=your-google-client-id
   ```

## 🌐 Development vs Production

- **Local Development**: Use this React frontend with live reload
- **Production**: Uses Lambda-served HTML templates (no build process needed)

## 📦 Scripts

```bash
npm run dev       # Start development server
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Lint code
```

## 🔗 API Integration

The React frontend connects to the same Lambda API endpoints used by the production HTML interface:

- `POST /api/objects` - Create objects
- `GET /api/objects` - Access objects
- `GET /api/user-objects` - List user objects
- `DELETE /api/objects` - Delete objects
- `POST /api/validate-email` - Email validation
- `POST /api/verify-code` - Code verification

## 🚧 Migration Note

This local development setup maintains the original React architecture for developers who prefer component-based development. The production deployment uses Lambda-served HTML for simplicity and cost optimization.