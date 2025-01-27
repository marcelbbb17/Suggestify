import React from "react";

function Profile_Page() {
  return (
    <div className="background">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><a href="#movies">Movies</a></li>
            <li><a href="#trending">Trending</a></li>
            <li><a href="#watchlist">Watchlist</a></li>
            <li><a href="#profile" className="active">Home</a></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello</p>
        </div>
      </header>

      <section className="main">
        <div className="profile-info">
          <h1>Profile Page</h1>
          <p>Manage your account and preferences here.</p>
        </div>
      </section>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Profile_Page;
