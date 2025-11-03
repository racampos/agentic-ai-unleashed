# Vercel Deployment Guide

This branch is configured for deploying the NetGenius Tutor frontend to Vercel with NVIDIA-hosted NIMs.

## Quick Deploy

1. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "Add New" → "Project"
   - Import this repository
   - Select the `vercel` branch

2. **Configure Build Settings:**

   Vercel should auto-detect the settings from `vercel.json`, but verify:

   - **Framework Preset**: Vite
   - **Root Directory**: `./` (project root)
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `cd frontend && npm install`

3. **Configure Environment Variables:**

   Add these variables in Vercel dashboard → Settings → Environment Variables:

   ```
   VITE_API_BASE_URL=https://orchestrator.netgenius.ai
   VITE_SIMULATOR_WS_URL=https://netgenius-production-pub.up.railway.app
   VITE_SIMULATOR_TOKEN=TEST_TOKEN
   ```

   - `VITE_API_BASE_URL` points to the Railway-hosted orchestrator backend
   - `VITE_SIMULATOR_WS_URL` points to the public Railway simulator instance
   - `VITE_SIMULATOR_TOKEN` is the auth token for the simulator

4. **Deploy:**
   - Click "Deploy"
   - Build takes ~2-3 minutes
   - Once deployed, you'll get a URL like `your-project.vercel.app`

5. **Test:**
   - Visit your Vercel URL
   - You should see the NVIDIA NIM banner at the top
   - Try browsing labs and starting a lab session

## Custom Domain

1. In Vercel dashboard → Settings → Domains
2. Click "Add"
3. Add `netgenius.ai`
4. Vercel will provide DNS records
5. Update your Route 53 DNS:
   ```
   Type: A
   Name: @
   Value: 76.76.21.21 (Vercel's IP)

   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

## Environment Variables Reference

- **VITE_API_BASE_URL**: Backend API endpoint (Railway deployment)
  - Production: `https://orchestrator.netgenius.ai`
  - The backend handles CORS and points to NVIDIA-hosted NIMs

## Files Added for Vercel

- `vercel.json` - Vercel build and routing configuration
- `frontend/src/components/NIMBanner.tsx` - NVIDIA NIM banner component
- Updated `frontend/src/App.tsx` - Added banner to app layout

## Banner

This deployment includes a banner at the top of every page stating:

> "This demo instance uses NVIDIA-hosted NIMs (not AWS-hosted) for easy public access"

This clearly differentiates the public demo from the AWS-hosted hackathon submission.

## Monitoring

- View deployment logs in Vercel dashboard → Deployments
- Check build status and runtime logs
- Monitor bandwidth and function invocations

## Costs

Vercel free tier includes:
- 100 GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN

Should be sufficient for a demo/portfolio site.

## Troubleshooting

### Build fails
- Check build logs in Vercel dashboard
- Verify `frontend/package.json` dependencies are valid
- Ensure Node version is compatible (Vercel uses Node 18+ by default)

### API calls fail
- Verify `VITE_API_BASE_URL` is set correctly
- Check Railway backend is running at https://orchestrator.netgenius.ai
- Check browser console for CORS errors

### Routing issues (404 on refresh)
- Verify `vercel.json` rewrites are configured correctly
- Should rewrite all routes to `/index.html` for client-side routing

## Architecture

```
User Browser
    ↓
Vercel Frontend (netgenius.ai)
    ↓
Railway Backend (orchestrator.netgenius.ai)
    ↓
NVIDIA Hosted NIMs (integrate.api.nvidia.com)
    ↓
NetGSim Simulator (Railway)
```

This setup provides a fully cloud-hosted demo without requiring AWS infrastructure.
