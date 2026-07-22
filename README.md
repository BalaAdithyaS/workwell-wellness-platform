# WorkWell - AI Employee Wellness Platform

## Overview
WorkWell is an AI-powered employee wellness platform designed to help organizations monitor employee wellbeing through wellness forms and conversational voice assessments.

## Features
- JWT Authentication
- Employee Wellness Form
- AI Wellness Analysis
- Voice Wellness Assistant
- Dashboard Analytics
- PostgreSQL Database Integration

## Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy

### AI
- Gemini 2.5 Flash

## Project Structure

WorkWell/
├── backend-v2/
└── workwell-frontend/

## Run Backend

```bash
cd backend-v2
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run Frontend

```bash
cd workwell-frontend/wellness-app
npm install
npm run dev
```