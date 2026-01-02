# Professional Web App Upgrade

- [ ] Backend Infrastructure <!-- id: 21 -->
    - [ ] Add `Flask-SQLAlchemy` and `Flask-Login` dependencies <!-- id: 22 -->
    - [ ] Create `models.py` (User, ScanHistory tables) <!-- id: 23 -->
    - [ ] Initialize Database in `server.py` <!-- id: 24 -->
- [ ] Authentication System <!-- id: 25 -->
    - [ ] Implement `/login`, `/register`, `/logout` routes <!-- id: 26 -->
    - [ ] Protect `/` and `/api/scan` with `@login_required` <!-- id: 27 -->
- [ ] User Interface (Professional) <!-- id: 28 -->
    - [ ] Design `login.html` (Premium aesthetic) <!-- id: 29 -->
    - [ ] Update `index.html` (Add User Profile/Logout) <!-- id: 30 -->
    - [ ] Create "Landing Page" flow (optional, usually Login IS the landing for private apps) <!-- id: 31 -->
- [ ] Persistence (Optional but Professional) <!-- id: 32 -->
    - [ ] Save scan history to DB instead of just in-memory <!-- id: 33 -->
