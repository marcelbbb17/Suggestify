import './App.css';

function App() {
  return (
    /* Basic Structure for homepage */   
    /* Citation: OpenAI. (2024). Assistance with the structure of homepage for App.js and App.css. ChatGPT. Retrieved October 23, 2024, from https://www.openai.com */
    <div className="background">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><a href="#movies">Movies</a></li>
            <li><a href="#trending">Trending</a></li>
            <li><a href="#watchlist">Watchlist</a></li>
            <li><a href="#profile">Profile</a></li>
          </ul>
        </nav>
        <div className="auth">
          {/*Login and Sign up buttons*/}
          <button className="login-btn">Login</button>
          <button className="signup-btn">Sign Up</button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <h1>Discover Your Next Favorite Movie</h1>
          {/*Search Bar*/}
          <input type="text" className="search-bar" placeholder="Search for movies..." />
        </div>
      </section>
      {/*Basic layout for both recommended and trending movies */}
      <section id="recommended" className="movies-section">
        <h2>Recommended For You</h2>
        <div className="movie-grid">
          <div className="movie">Movie 1</div>
          <div className="movie">Movie 2</div>
          <div className="movie">Movie 3</div>
          <div className="movie">Movie 4</div>
        </div>
      </section>

      <section id="trending" className="movies-section">
        <h2>Trending Movies</h2>
        <div className="movie-grid">
          <div className="movie">Movie 5</div>
          <div className="movie">Movie 6</div>
          <div className="movie">Movie 7</div>
          <div className="movie">Movie 8</div>
        </div>
      </section>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
