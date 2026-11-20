# FoodBridge — Food Donation & Surplus Coordination Platform

A full-stack coordination app connecting restaurants and retail donors with NGOs and collection volunteers. It supports donation listings, reservations, collection tracking, and completion.

## Roles
- Restaurant Manager / Retail Donor: create food donation listings.
- NGO Coordinator: discover and reserve available donations; complete a collected handover.
- Collection Volunteer: mark reserved donations as collected.

## Stack
React + Vite · Flask REST API · SQLite · Docker / Docker Compose · GitHub · Vercel

## Run locally with Docker
Prerequisite: Docker Desktop.

```bash
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend health: http://localhost:5000/api/health

The backend creates a demo donor and two sample listings on first startup. Create your own account using the Register screen to test each role. For a full workflow, create separate accounts for a donor, NGO coordinator, and collection volunteer.

## Run without Docker
Terminal 1 — backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Terminal 2 — frontend:
```bash
cd frontend
npm install
npm run dev
```
Vite runs at http://localhost:5173. Set `VITE_API_URL=http://localhost:5000/api` in `frontend/.env` if needed.

## Push to GitHub
Create an empty repository on GitHub, then run these commands from this project folder:
```bash
git init
git add .
git commit -m "Build FoodBridge food donation platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/foodbridge.git
git push -u origin main
```

## Deploy frontend to Vercel
1. Push this project to GitHub.
2. In Vercel, choose **Add New → Project** and import the repository.
3. Keep the repository root as the project root; `vercel.json` configures the Vite build/output.
4. Add environment variable `VITE_API_URL` with your deployed backend URL, ending in `/api`.
5. Deploy.

## Deploy backend with Docker
Vercel is used for the React frontend. Deploy the Flask API separately to a Docker-capable service (for example Render, Railway, Fly.io, or a VPS):
1. Create a backend service from this GitHub repository.
2. Set its Dockerfile path to `backend/Dockerfile` (or set the service root directory to `backend`).
3. Configure `SECRET_KEY`, `FRONTEND_ORIGIN` (your Vercel domain), and `DATABASE_URL`.
4. Set the Vercel `VITE_API_URL` to `https://YOUR_API_HOST/api` and redeploy the frontend.

## Important production notes
- SQLite is included for local development/demo. A container's local filesystem may be ephemeral; use a persistent volume or preferably managed PostgreSQL for production data.
- The demo API uses an `X-User-Id` header for simple role-based coursework demonstration. This is **not production authentication**. Before public production use, replace it with signed sessions/JWT, authorization checks, rate limiting, HTTPS, validation, and audit logging.
- Food safety: donors must provide accurate use-by information and recipients should verify food condition, storage, allergens, and local food-safety requirements before collection.
- No external delivery API is integrated; collection is coordinated internally by volunteers.
