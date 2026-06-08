# Pizza Admin Web - Render.com Deployment Guide

This guide walks you through deploying the Pizza Admin Web application to Render.com.

## Prerequisites
- GitHub account with your pizza_admin_web repository pushed
- Render.com account (free tier supported)
- Firebase service account JSON file (keep locally, don't commit to git)

## Step-by-Step Deployment

### 1. Prepare Repository
```bash
cd /home/cao-le/Web\ Projects/pizza_admin_web
git status
git add render.yaml .gitignore
git commit -m "Add Render.yaml deployment config and update .gitignore"
git push origin main
```

### 2. Create Render.com Account
1. Visit https://render.com
2. Click "Sign up" → Select "Sign up with GitHub"
3. Authorize Render to access your GitHub repositories
4. Wait for account confirmation

### 3. Deploy via Blueprint
1. Go to Render Dashboard → Click **New +** → Select **Blueprint**
2. Search for and select your `pizza_admin_web` repository
3. Render will auto-detect `render.yaml`
4. Click **Deploy Blueprint**
5. Wait 5-10 minutes for all services to transition to "Live"

Watch progress:
- `pizza-admin-frontend` (Static Site) - Usually completes first
- `pizza-admin-backend` (Web Service) - Runs migrations and collectstatic
- `pizza-admin-worker` (Background Worker) - Celery processes start
- `pizza-admin-db` (PostgreSQL) - Database service initializes
- `pizza-admin-redis` (Redis) - Cache/message broker initializes

### 4. Configure Firebase Credentials
1. Get your Firebase service account JSON file
2. In Render Dashboard → Go to `pizza-admin-backend` service → **Settings** → **Secrets**
3. Click **Add Secret**
   - Key: `FIREBASE_CONFIG`
   - Value: Copy entire contents of your Firebase JSON file
4. Click **Save**
5. Backend service will auto-restart with new secret

### 5. Verify Services Are Running

Check health endpoint:
```bash
curl https://<BACKEND-URL>/api/health/
# Expected response:
# {
#   "status": "ok",
#   "services": {
#     "database": "healthy",
#     "cache": "healthy"
#   }
# }
```

### 6. Update Environment Variables (Post-Deployment)

After deployment, Render generates URLs. Update these in services:

**Frontend Service:**
- Retrieve actual backend URL from Render dashboard
- No changes needed - automatically set via ${{web.url}}

**Backend Service Environment:**
1. Go to Settings → Environment
2. Update these variables with actual URLs:
   - `ALLOWED_HOSTS`: `pizza-admin-backend-xxxxx.onrender.com`
   - `CORS_ALLOWED_ORIGINS`: `https://pizza-admin-frontend-xxxxx.onrender.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://pizza-admin-frontend-xxxxx.onrender.com`
3. Click **Save** (services auto-restart)

### 7. Create Admin User

SSH into backend service:
1. Go to `pizza-admin-backend` → **Shell** tab
2. Run:
```bash
cd backend_dj
python manage.py createsuperuser
```

### 8. Test Complete Workflow

1. **Access Frontend:**
   ```
   https://pizza-admin-frontend-xxxxx.onrender.com
   ```

2. **Access Admin Panel:**
   ```
   https://pizza-admin-backend-xxxxx.onrender.com/admin
   ```
   Login with credentials created in step 7

3. **Test Image Import Cancellation:**
   - Upload CSV with 20-30 items
   - Start image processing
   - Click Cancel during image upload
   - Verify logs show: `🛑 [WORKER CANCELLED]` messages
   - Confirm no orphaned Firebase uploads

### Troubleshooting

**Backend service won't start:**
- Check logs: Services → `pizza-admin-backend` → **Logs**
- Common issues: Missing environment variables, database connection errors
- Run migrations manually: Shell tab → `python manage.py migrate`

**Frontend shows API errors:**
- Check CORS settings match actual Render URLs
- Verify backend is responding: `curl https://<BACKEND>/api/health/`
- Check frontend browser console for detailed errors

**Redis/PostgreSQL connection errors:**
- Verify CONNECTION strings are correct in environment variables
- Check service names match in `render.yaml`
- Restart services after updating environment variables

**Images not uploading:**
- Verify Firebase credentials are set correctly
- Check FIREBASE_CONFIG_PATH matches: `/etc/secrets/firebase_config.json`
- Test Firebase permissions locally before deploying

### Cost Information

Render.com free tier includes:
- ✅ 1 static site (unlimited)
- ✅ 1 web service (spins down after 15 min inactivity)
- ✅ 1 background worker (spins down after 15 min inactivity)
- ✅ 1 PostgreSQL (256 MB, spins down after 15 min)
- ✅ 1 Redis instance (free Starter Plan)

Perfect for development and testing. For production 24/7 uptime, upgrade to Paid plan ($5-7/month minimum).

### Next Steps

- Monitor application health via `/api/health/`
- Enable notifications for service failures
- Implement backup strategy for PostgreSQL
- Consider upgrading to Paid tier if need 24/7 uptime

