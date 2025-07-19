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

### 2. **Set Up the Backend**

#### a. **Install Python & MySQL**
- Install [Python 3.8+](https://www.python.org/downloads/)
- Install [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)

#### b. **Create and Configure the Database**
- Create a MySQL database (e.g., `suggestify`)
- Import the provided SQL schema (if available) or create tables as needed

#### c. **Set Up the Backend Environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

- Open MySQL and create a database:
  ```sql
  CREATE DATABASE suggestify;
  USE suggestify;
  ```
- **Run the provided `suggestify_schema.sql` file** to create all tables:
  ```bash
  mysql -u root -p suggestify < suggestify_schema.sql
  ```
- *(You can find `suggestify_schema.sql` in this repo.)*

#### d. **Start the Frontend**
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
