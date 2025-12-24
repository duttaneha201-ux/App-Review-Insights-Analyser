# App Review Insights UI

Next.js frontend for the App Review Insights Analyzer.

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Backend API

The frontend expects the backend API to be running on `http://localhost:8000`.

Start the backend API:
```bash
# From project root
uvicorn app.api.server:app --reload --port 8000
```

## Features

- ✅ Play Store URL input with validation
- ✅ Week range selector (1-12 weeks)
- ✅ Email input with validation
- ✅ Loading states
- ✅ Error handling with user-friendly messages
- ✅ Success confirmation
- ✅ Modern, responsive UI

## API Contract

### POST /api/subscriptions

**Request:**
```json
{
  "playstore_url": "https://play.google.com/store/apps/details?id=com.example.app",
  "weeks": 8,
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Analysis started. You will receive the insights by email.",
  "app_id": "com.example.app"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid input (URL format, email format, etc.)
- `404 Not Found`: App doesn't exist on Play Store
- `500 Internal Server Error`: Server error

## Error Messages

The UI displays user-friendly error messages:

- "This app does not exist on Play Store." - Invalid/non-existent app
- "No reviews found for the selected time range." - No reviews in timeframe
- "Please enter a valid email address." - Invalid email format
- "Something went wrong. Please try again later." - Server error

## Production Deployment

For production:

1. Update `next.config.js` to point to production API URL
2. Build the app:
```bash
npm run build
npm start
```

3. Deploy to Vercel, Netlify, or your preferred hosting








