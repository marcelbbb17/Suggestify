import './App.css';

function App() {
  return (
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
          <button className="login-btn">Login</button>
          <button className="signup-btn">Sign Up</button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-content">
          <h1>Discover Your Next Favorite Movie</h1>
          <input type="text" className="search-bar" placeholder="Search for movies..." />
        </div>
      </section>

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
