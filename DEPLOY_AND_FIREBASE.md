# Deployment & Firebase Setup Guide

## 1. Firebase Integration

To link your bot to **Google Firebase** for cloud logging:

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Create a new project.
3.  Go to **Project Settings** -> **Service Accounts**.
4.  Click **Generate New Private Key**.
5.  Save the JSON file as `firebase_credentials.json` in this folder (`arbitrage_bot`).
6.  Go to **Build** -> **Firestore Database** and standard "Create Database".
7.  The bot is now auto-linked! When you run a scan, it will save logs to your online Firebase implementation.

---

## 2. Deploying to the Internet (Google Cloud Run)

The easiest way to host this Python app is **Google Cloud Run**.

### Prerequisites
- Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
- Valid Google Cloud Billing Account.

### Steps
1.  **Login**
    ```bash
    gcloud auth login
    gcloud config set project [YOUR_PROJECT_ID]
    ```

2.  **Deploy**
    Run this single command in the terminal:
    ```bash
    gcloud run deploy arb-bot --source . --allow-unauthenticated --region us-central1
    ```

3.  **Done!**
    Google will give you a URL (e.g., `https://arb-bot-xc92-uc.a.run.app`). You can share this link with anyone.

---

## Alternative: Render.com (Free Tier)

1.  Push this code to GitHub.
2.  Go to [Render Dashboard](https://dashboard.render.com/).
3.  New -> Web Service.
4.  Connect your GitHub repo.
5.  Settings:
    - **Runtime**: Python 3
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `gunicorn server:app`
6.  Click **Deploy**.
