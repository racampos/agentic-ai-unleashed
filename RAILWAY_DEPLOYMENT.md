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
   # NIM Configuration
   NIM_MODE=hosted
   NGC_API_KEY=your_nvidia_api_key_here

   # NVIDIA Hosted NIMs (default URLs)
   NVIDIA_HOSTED_LLM_URL=https://integrate.api.nvidia.com/v1
   NVIDIA_HOSTED_EMB_URL=https://integrate.api.nvidia.com/v1
   NVIDIA_LLM_MODEL=nvidia/llama-3.1-nemotron-nano-8b-v1
   NVIDIA_EMB_MODEL=nvidia/nv-embedqa-e5-v5

   # NetGSim Simulator
   NETGSIM_BASE_URL=your_netgsim_instance_url_here
   NETGSIM_WS_URL=your_netgsim_websocket_url_here

   # Python environment
   PYTHONUNBUFFERED=1
   ```

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
