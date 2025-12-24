# Module 9: User Interface (Input & Subscription Management)

Complete Next.js frontend for App Review Insights Analyzer.

## 🎯 What This Module Does

Provides a clean, user-friendly interface for:
- Entering Google Play Store app URLs
- Selecting week range (1-12 weeks)
- Entering email for insights
- Submitting subscription requests
- Viewing success/error states

## 📁 Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx             # Main page
│   └── globals.css          # Global styles
├── components/
│   └── SubscriptionForm.tsx # Main form component
├── package.json             # Dependencies
├── next.config.js          # Next.js config
├── tsconfig.json           # TypeScript config
└── README.md               # Frontend docs

app/api/
├── __init__.py
├── server.py               # FastAPI server
└── subscriptions.py        # Subscription endpoint
```

## 🚀 Quick Start

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Install Backend Dependencies

```bash
# From project root
pip install fastapi uvicorn pydantic
```

### 3. Start Backend API

```bash
uvicorn app.api.server:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000`

## ✨ Features

### Frontend Validations
- ✅ Play Store URL format validation
- ✅ Email format validation
- ✅ Week range validation (1-12)
- ✅ Real-time error display
- ✅ User-friendly error messages

### Backend Validations
- ✅ URL existence check on Play Store
- ✅ Reviews availability check
- ✅ Email format validation
- ✅ Database integrity checks

### UI/UX
- ✅ Modern gradient design
- ✅ Responsive layout
- ✅ Loading states
- ✅ Success/error feedback
- ✅ Accessible form inputs
- ✅ Help text for guidance

## 🔌 API Integration

### Endpoint: POST /api/subscriptions

**Request:**
```json
{
  "playstore_url": "https://play.google.com/store/apps/details?id=com.whatsapp",
  "weeks": 8,
  "email": "user@example.com"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Analysis started. You will receive the insights by email.",
  "app_id": "com.whatsapp"
}
```

**Error Responses:**

| Status | Error Message |
|--------|--------------|
| 400 | "This app does not exist on Play Store." |
| 400 | "No reviews found for the selected time range." |
| 400 | "Please enter a valid email address." |
| 500 | "Something went wrong. Please try again later." |

## 🎨 UI Components

### SubscriptionForm
Main form component with:
- Play Store URL input
- Week range slider (1-12)
- Email input
- Submit button
- Error/success messages
- Loading spinner

### Styling
- Modern gradient background
- Clean white card design
- Smooth transitions
- Responsive design
- Accessible colors

## 🔄 Workflow

1. **User enters data** → Frontend validates
2. **User submits** → API call to backend
3. **Backend validates** → Checks URL, reviews, email
4. **Backend processes** → Creates subscription, triggers analysis
5. **Response sent** → Success/error message displayed
6. **Email sent** → User receives insights (via existing email service)

## 🧪 Testing

### Manual Testing

1. Start backend: `uvicorn app.api.server:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Visit `http://localhost:3000`
4. Test form with:
   - Valid URL: `https://play.google.com/store/apps/details?id=com.whatsapp`
   - Invalid URL: `https://example.com`
   - Invalid email: `not-an-email`
   - Week range: Try 1-12

### API Testing

```bash
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "playstore_url": "https://play.google.com/store/apps/details?id=com.whatsapp",
    "weeks": 4,
    "email": "test@example.com"
  }'
```

## 📝 Integration Points

### With Existing Pipeline
- Uses `extract_clean_and_synthesize()` from `app.pipeline`
- Integrates with storage layer (saves to database)
- Uses email service for notifications

### With Database
- Creates app records via `AppRepository`
- Creates subscriptions via `SubscriptionRepository`
- Creates weekly batches via `WeeklyBatchRepository`

## 🚀 Production Deployment

### Frontend (Vercel/Netlify)
1. Update `next.config.js` API URL
2. Build: `npm run build`
3. Deploy to hosting platform

### Backend (Serverless/Container)
1. Use FastAPI with uvicorn
2. Set environment variables
3. Deploy to AWS Lambda, Google Cloud Run, or Docker

## 📋 Checklist

- ✅ Next.js project setup
- ✅ Form component with all inputs
- ✅ Frontend validations
- ✅ Backend API endpoint
- ✅ Error handling
- ✅ Success states
- ✅ Loading states
- ✅ Modern UI design
- ✅ API integration
- ✅ Database integration
- ✅ Documentation

## 🎯 Next Steps

1. Add authentication (optional)
2. Add subscription management page
3. Add analytics dashboard
4. Add email preferences
5. Add scheduled job management UI








