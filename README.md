# Suggestify – Content-Based Movie Recommendation Platform 

**Author:** Marcel Beya-Wa-Beya
**Tech Stack:** React, Flask, MySQL, Python, JavaScript  
**Live Demo:** Coming soon  
**GitHub:** github.com/yourname/suggestify

---

## Overview
Suggestify is a movie recommendation web application that helps users discover personalised movie suggestions based on their interests and preferences. The platform combines a modern Netflix-inspired UI with intelligent backend logic, including content-based filtering and real-time search via the TMDB API.

This project demonstrates full-stack development using Flask (Python) for the backend and React (JavaScript) for the frontend. It includes user authentication, state management, and database integration.

---

## Features
- Content-based recommendation system (TF-IDF + Cosine Similarity)
- Cold-start questionnaire for onboarding new users
- Watchlist management with personal notes
- Movie rating & feedback system
- Explanation for recommendations ("Why this movie?")
- Clean, responsive UI inspired by Netflix
- Secure login/signup with JWT authentication
- Search functionality powered by TMDB API

---

## Tech Stack
**Frontend**
- React
- React Router
- Context API
- Axios

**Backend**
- Flask
- Flask-CORS
- MySQL
- JWT Authentication
- scikit-learn (TF-IDF)
- NLTK (Natural Language Processing)

**API**
- TMDB (The Movie Database) API for movie metadata

---

## 📁 Project Structure
```
suggestify/
├── backend/              # Flask API
│   ├── routes/           
│   ├── models/           
│   ├── utils/            
│   ├── app.py            
│   └── requirements.txt  
│
├── src/                  # React frontend
│   ├── components/       
│   ├── context/          
│   ├── pages/            
│   └── styles/           
│
├── public/               
├── .env.example          
├── package.json          
└── README.md             
```

---

## 💻 Installation & Running Locally

### Backend (Flask)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```
Create a `.env` file inside `backend/`:
```env
SECRET_KEY=your_secret_key
TMDB_API_KEY=your_tmdb_api_key
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=suggestify
```
Create the database:
```sql
CREATE DATABASE suggestify;
```
Start the Flask server:
```bash
python app.py
```

### Frontend (React)
```bash
npm install
npm start
```

The frontend runs on http://localhost:3000  
The backend API runs on http://localhost:5000

---

## 🛠️ Troubleshooting
- **API Connection Issues:** Ensure the backend server is running at the expected URL
- **Database Errors:** Check that MySQL is running and the credentials in `.env` are correct
- **CORS Errors:** Make sure the backend has CORS configured correctly for your frontend URL
- **TMDB API Key:** Verify your API key is correct and has not exceeded rate limits

---