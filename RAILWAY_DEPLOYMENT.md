# Railway Deployment Guide

This branch is configured for deploying the NetGenius Tutor backend to Railway.

## Quick Deploy

1. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository
   - Choose the `railway` branch

2. **Configure Environment Variables:**

   Add these variables in Railway dashboard → Variables:

   ```
   # REQUIRED: NIM Configuration
   NIM_MODE=hosted
   NGC_API_KEY=your_nvidia_api_key_here

   # REQUIRED: NetGSim Simulator
   SIMULATOR_BASE_URL=your_netgsim_instance_url_here
   SIMULATOR_TOKEN=TEST_TOKEN

   # Application Settings
   LOG_LEVEL=INFO
   DEBUG=false
   PYTHONUNBUFFERED=1
   ```

   **Note:** The NVIDIA NIMs will use the default hosted endpoints. No need to set LLM/EMB URLs unless using custom endpoints.

3. **Deploy:**
   - Railway will automatically detect the configuration
   - Build takes ~3-5 minutes
   - Once deployed, you'll get a URL like `your-app.railway.app`

4. **Health Check:**
   - Visit `https://your-app.railway.app/health`
   - Should return: `{"status": "healthy"}`

## Custom Domain

1. In Railway dashboard → Settings → Domains
2. Click "Custom Domain"
3. Add `api.netgenius.ai`
4. Update your Route 53 DNS with the CNAME provided by Railway

## Environment Variables Reference

- **NIM_MODE**: Set to `hosted` to use NVIDIA's hosted NIMs (free)
- **NGC_API_KEY**: Your NVIDIA NGC API key from https://ngc.nvidia.com/setup/api-key
- **NETGSIM_BASE_URL**: Your dedicated NetGSim instance URL
- **NETGSIM_WS_URL**: WebSocket URL for the NetGSim instance

## Files Added for Railway

- `railway.json` - Railway build and deploy configuration
- `Procfile` - Process command for web server
- `runtime.txt` - Python version specification
- `requirements.txt` - Python dependencies (already existed)

## Monitoring

- View logs in Railway dashboard → Deployments → Logs
- Monitor usage in Railway dashboard → Metrics

## Costs

Railway free tier includes:
- $5/month credit
- ~100 hours of usage

Estimated cost for this backend: ~$7-15/month depending on usage.

## Troubleshooting

### Build fails
- Check logs in Railway dashboard
- Verify `requirements.txt` is valid
- Ensure Python version is compatible

### Health check fails
- Check environment variables are set
- Verify NGC_API_KEY is valid
- Check logs for startup errors

### CORS errors
- The backend allows all origins by default
- If needed, update CORS settings in `api/main.py`
