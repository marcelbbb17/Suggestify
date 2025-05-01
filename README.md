# Suggestify - Designing an AI: Netflix Recommender System

**Author**: Marcel Beya-Wa-Beya  
**Module**: CO3204 Software Engineering Project  
**University**: University of Leicester  
**Date**: May 2025

---

## Overview

**Suggestify** is a content-based movie recommendation platform designed to help users discover films tailored to their preferences. Built using React (frontend), Flask (backend), and MySQL (database), it uses TF-IDF and cosine similarity to recommend movies via the TMDB API.

The project was developed as part of the CO3204 Software Engineering Project.

---

## Features
- Personalised movie recommendations using content-based filtering
- Cold-start questionnaire for new users
- Watchlist system (Want to Watch, Watching, Watched + personal notes)
- Feedback mechanism to improve future recommendations
- Rating system
- Search functionality for movies
- Explanation of why each movie was recommended
- Responsive, Netflix-inspired UI built in React
- Secure login/signup system using JWT

---

## Tech Stack

### Frontend
- React
- React Router
- Context API
- Axios

### Backend
- Flask (Python)
- Flask-CORS
- MySQL
- JWT for auth
- TF-IDF (via `scikit-learn`)
- Natural Language Processing with NLTK

### Database
- MySQL: Stores user data, watchlist, preferences, feedback

### API
- TMDB API for movie data and metadata

---

## System Requirements
- Node.js 14+
- Python 3.7+
- MySQL 5.7+
- Modern web browser (Chrome, Firefox, Edge, Safari)
- 4GB RAM minimum

---

## Project Structure
```
├── backend/              # Flask backend
│   ├── routes/           # API endpoints
│   ├── utils/            # Helper functions
│   ├── models/           # Data models
│   ├── app.py            # Entry point
│   └── requirements.txt  # Dependencies
│
├── src/                  # React frontend
│   ├── components/       # Reusable components
│   ├── context/          # Context providers
│   ├── pages/            # Page components
│   └── styles/           # CSS files
│
└── README.md             # This file
```

---

## Installation & Running the System

### Backend (Flask API)
To activate the backend follow the steps below 

1. Navigate to the `backend/` folder
2. Create a virtual environment and activate it
```bash
python -m venv venv
venv\Scripts\activate  # For Windows
```
#### Install dependencies 
```bash
pip install -r requirements.txt
```
#### Create a .env file containing: 
```bash
SECRET_KEY=your_secret
TMDB_API_KEY=your_api_key
DB_HOST=localhost
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_pass
DB_NAME=suggestify
```
#### Database Setup
1. Install MySQL if not already installed
2. Create a database named 'suggestify':
```sql
CREATE DATABASE suggestify;
```
3. The tables will be automatically created when running the backend for the first time

#### Start the server
```bash
python app.py
```
The backend API runs on http://localhost:5000 by default

### Frontend 
1. Navigate to the frontend directory which should just be the root directory 

#### Install dependencies 
```bash
npm install
```
#### Start the frontend 
```bash
npm start
```
The frontend runs on http://localhost:3000 by default

---

## Troubleshooting

### Common Issues
- **API Connection Issues**: Ensure the backend server is running at the expected URL
- **Database Errors**: Check that MySQL is running and the credentials in `.env` are correct
- **CORS Errors**: Make sure the backend has CORS configured correctly for your frontend URL
- **TMDB API Key**: Verify your API key is correct and has not exceeded rate limits

---

## Project Log
A full development log is available in project_log.md, located in the GitLab repository root.

---

## Use of AI 

Throughout the development of Suggestify, I made use of AI tools (such as ChatGPT and GitHub Copilot) as support during implementation and debugging. These tools acted as a "coding buddy," helping me understand error messages, generate ideas for structuring functions, and explore possible solutions to programming issues.

Because of this workflow, many parts of the code were influenced or initially drafted with AI support, particularly during problem-solving and development sprints. However, all AI-generated code was reviewed, tested, and edited by me to ensure it met the needs of the system and aligned with my own understanding.

AI was not used to write the dissertation, but was permitted for grammar checks and simplifying explanations, in line with university guidelines.

All final decisions, system design, and implementation logic were made and executed by myself.
