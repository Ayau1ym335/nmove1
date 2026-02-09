# Deployment Guide for NMove Website

This guide covers how to deploy the frontend (React/Vite) and important considerations for the backend API.

## 1. Frontend Deployment (React App)

The easiest way to deploy this Vite/React application is using **Vercel** or **Netlify**. Both platforms are optimized for frontend frameworks and have generous free tiers.

### Option A: Deploy with Vercel (Recommended)

**Prerequisites:**
- A [Vercel account](https://vercel.com/signup)
- `npm` installed (you already have this)

**Steps:**
1.  **Install Vercel CLI:**
    ```bash
    npm install -g vercel
    ```
2.  **Login:**
    ```bash
    vercel login
    ```
    Follow the prompts to authorize via your browser.
3.  **Deploy:**
    Run this command in the project root (`website/website/`):
    ```bash
    vercel
    ```
    - Set up and deploy: `Y`
    - Which scope: (Select your account)
    - Link to existing project: `N` (unless updating)
    - Project name: `nmove-website` (or similar)
    - Directory: `./` (default)
    - Auto-detect settings: `Y` (Vite is supported out of the box)
    - **Override settings**: `N`

4.  **Production Deployment:**
    The first run gives you a "preview" URL. To deploy to production:
    ```bash
    vercel --prod
    ```

### Option B: Deploy with Netlify (Drag & Drop)

1.  **Build the project locally:**
    ```bash
    npm run build
    ```
    This creates a `dist` folder in your project directory.
2.  **Upload:**
    - Go to [Netlify Drop](https://app.netlify.com/drop).
    - Drag and drop the `dist` folder onto the page.
    - Your site will be live instantly!

---

## 2. Important: Backend Connection

Your application currently tries to connect to a local backend at `http://localhost:8000`:
- **File:** `src/pages/Pricing.tsx`

**⚠️ This will NOT work on the deployed website.** The deployed frontend cannot access your local computer's `localhost`.

### Solution

1.  **Deploy your Backend:**
    You need to deploy your Python/FastAPI backend to a cloud provider like **Render**, **Railway**, or **Heroku**.
2.  **Update the API URL:**
    Instead of hardcoding the URL, use environment variables.

    **In your code (`src/pages/Pricing.tsx`):**
    ```typescript
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/api/create-checkout-session`, { ... });
    ```

    **In Vercel/Netlify Dashboard:**
    - Go to **Settings** > **Environment Variables**.
    - Add a variable named `VITE_API_URL`.
    - Set the value to your *production backend URL* (e.g., `https://api.nmove.com`).

---

## 3. Custom Domain (Optional)

Both Vercel and Netlify allow you to add a custom domain (e.g., `www.nmove.com`).
1.  Go to the project settings in the Vercel/Netlify dashboard.
2.  Select **Domains**.
3.  Add your domain and follow the DNS configuration instructions.
