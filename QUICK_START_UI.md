# Quick Start: UI Module

## 🚀 Running the Complete UI System

### Step 1: Install Dependencies

**Backend:**
```bash
pip install fastapi uvicorn pydantic
```

**Frontend:**
```bash
cd frontend
npm install
```

### Step 2: Start Backend API

```bash
python run_api_server.py
```

Or:
```bash
uvicorn app.api.server:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Step 4: Test the UI

1. Open `http://localhost:3000` in your browser
2. Enter a Play Store URL (e.g., `https://play.google.com/store/apps/details?id=com.whatsapp`)
3. Select week range (1-12)
4. Enter your email
5. Click "Start Analysis"

## 📋 What Happens

1. **Frontend validates** input (URL format, email, weeks)
2. **Request sent** to backend API
3. **Backend validates** URL exists on Play Store
4. **Backend creates** subscription in database
5. **Backend triggers** analysis pipeline
6. **Analysis runs** (extracts reviews, identifies themes, generates pulse)
7. **Email sent** to user with insights
8. **Success message** displayed in UI

## 🧪 Test API Directly

```bash
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "playstore_url": "https://play.google.com/store/apps/details?id=com.whatsapp",
    "weeks": 4,
    "email": "your-email@example.com"
  }'
```

## ✅ Success Indicators

- ✅ Form shows "Processing..." with spinner
- ✅ Success message appears: "Analysis started. You will receive the insights by email."
- ✅ Email arrives in inbox (check spam folder)
- ✅ Data saved to database (check `data/reviews.db`)

## ❌ Common Issues

**Frontend can't connect to backend:**
- Make sure backend is running on port 8000
- Check `next.config.js` has correct API URL

**CORS errors:**
- Backend CORS is configured for `localhost:3000`
- Check browser console for errors

**API errors:**
- Check backend logs for detailed error messages
- Verify `.env` file has all required credentials
- Ensure database is initialized

## 📁 File Structure

```
frontend/              # Next.js frontend
├── app/
│   ├── page.tsx      # Main page
│   └── globals.css   # Styles
└── components/
    └── SubscriptionForm.tsx

app/api/               # FastAPI backend
├── server.py         # API server
└── subscriptions.py  # Subscription endpoint
```

## 🎯 Next Steps

- Add authentication
- Add subscription management page
- Add analytics dashboard
- Deploy to production








