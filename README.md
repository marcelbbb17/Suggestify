# Suggestify – Content-Based Movie Recommendation Platform 

**Author:** Marcel Beya-Wa-Beya
**Tech Stack:** React, Flask, MySQL, Python, JavaScript  
**GitHub:** github.com/marcelbbb17/Suggestify
**Link:** https://suggestify-three.vercel.app/

## What is Suggestify?

**Suggestify** is a full-stack movie recommendation web app that leverages advanced content-based and collaborative filtering techniques to provide personalised movie recommendations.  
It features user authentication, a watchlist, feedback system, and a sophisticated recommendation engine that analyzes user preferences, movie content, and feedback to generate tailored suggestions.

**Key Features:**
- User registration, login, and profile management
- Movie search and details
- Personalised recommendations based on genres, actors, themes, and user feedback
- Watchlist and feedback system
- Modern React frontend and Flask backend
- MySQL database (locally or on Railway)
- Caching and performance optimisations

---

## Why is the Recommendation System Disabled on the Live Demo?

Due to the **resource limitations of free hosting platforms like Render** (512MB RAM, 30s timeout), the full recommendation engine cannot run in production.  
**The deployed version works for all features except recommendations.**  
If you want to experience the full recommendation engine, please run the project locally as described below.

---

## ⚠️ Security Notice

**This project is for demonstration and educational purposes only.**  
- **Do NOT use real or sensitive data.**  
- Use only dummy emails, passwords, and information.
- The focus is on the recommendation engine, not production-grade security.

---

## How to Run Locally (Full Recommendation System)

### 1. **Clone the Repository**
```bash
git clone https://github.com/marcelbbb17/suggestify.git
cd suggestify
```

---

### 2. **Set Up the Backend**

#### a. **Install Prerequisites**
- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **MySQL Community Server**: [Download MySQL](https://dev.mysql.com/downloads/mysql/)
- **Node.js & npm** (for the frontend): [Download Node.js](https://nodejs.org/)

#### b. **Create the Database**
1. **Open MySQL Workbench or the MySQL CLI** and run:
    ```sql
    CREATE DATABASE suggestify;
    USE suggestify;
    ```
2. **Run the provided schema file to create all tables:**
    ```bash
    mysql -u root -p suggestify < suggestify_schema.sql
    ```
    *(You can find `suggestify_schema.sql` in this repo.)*

#### c. **Set Up the Backend Environment**
1. **Navigate to the backend folder:**
    ```bash
    cd backend
    ```
2. **Create and activate a virtual environment:**
    - On macOS/Linux:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    - On Windows:
      ```bash
      python -m venv venv
      venv\Scripts\activate
      ```
3. **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Create a `.env` file in the `backend/` folder with the following content:**
    ```env
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=root
    DB_PASSWORD=your_mysql_password
    DB_NAME=suggestify

    SECRET_KEY=your_secret_key
    TMBD_API_KEY=your_tmdb_api_key

    FLASK_ENV=development
    API_BASE_URL=http://localhost:5000
    ENABLE_ACTORS=true
    ENABLE_ENHANCED_PROFILES=true
    PAGES_PER_CATEGORY=10
    ```
    - Get a [TMDB API key](https://www.themoviedb.org/documentation/api) (free signup).

5. **Start the backend server:**
    ```bash
    flask run
    ```
    or, if using `app.py`:
    ```bash
    python app.py
    ```
    - The backend will run at [http://localhost:5000](http://localhost:5000)

---

### 3. **Set Up the Frontend**

1. **Navigate to the project root (if not already there):**
    ```bash
    cd ../
    ```
2. **Install frontend dependencies:**
    ```bash
    npm install
    ```
3. **Start the frontend:**
    ```bash
    npm start
    ```
    - The app will open at [http://localhost:3000](http://localhost:3000)

---

## Why the Recommendation System Doesn't Work on the Live Demo

- The recommendation engine is **resource-intensive** (analyzes hundreds of movies, builds profiles, computes similarities).
- Free hosting (Render, Railway, etc.) **limits RAM and request timeouts** (30-60s), which is not enough for the full engine.
- All other features (auth, search, watchlist) work online, but recommendations require local resources.

---

## Recruiter/Client Notes

- **Advanced Recommendation Engine:**  
  Uses TF-IDF, genre/actor matching, user feedback, and hybrid filtering for high-quality recommendations.
- **Modern Full-Stack Architecture:**  
  React frontend, Flask backend, MySQL database, RESTful APIs, and caching.
- **Scalable & Configurable:**  
  Environment-based configuration allows easy switching between local and production.
- **Clean Code & Documentation:**  
  Modular, well-commented codebase with clear separation of concerns.
- **Security Disclaimer:**  
  Security is basic; focus is on recommendation logic and system design.
- **Portfolio-Ready:**  
  Designed to showcase advanced engineering, not just CRUD features.

---
