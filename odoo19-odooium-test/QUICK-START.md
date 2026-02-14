# Odoo19 + Odooium - Test Deployment

**Quick Deploy Command:**

```bash
cd /home/cdsbot/.openclaw/workspace/odoo19-odooium-test
sudo ./deploy-production.sh
```

**What This Script Does:**

1. ✅ Installs Nginx + Certbot + ngrok
2. ✅ Configures SSL (Let's Encrypt)
3. ✅ Sets up reverse proxy to odooium.odoo-mcp.com
4. ✅ Starts Odoo 19 + PostgreSQL containers
5. ✅ Starts ngrok tunnel for external access
6. ✅ Displays all URLs and configuration

---

## 🌐 Access URLs

### Production
**HTTPS:** https://odooium.odoo-mcp.com

### Local Testing
**HTTP:** http://localhost:8069

### ngrok (Tunneling)
**Displayed when script runs**
- Use for GitHub OAuth testing
- Changes each time ngrok restarts

---

## 📋 Quick Start

### 1. Run Deployment Script
```bash
cd /home/cdsbot/.openclaw/workspace/odoo19-odooium-test
sudo ./deploy-production.sh
```

### 2. Access Odoo

**Option A - Production (SSL):**
1. Open: https://odooium.odoo-mcp.com
2. Log in: admin/admin

**Option B - Local (No SSL):**
1. Open: http://localhost:8069
2. Log in: admin/admin

**Option C - ngrok (External Access):**
1. Check deploy script output for ngrok URL
2. Update GitHub OAuth callback URL to use ngrok URL
3. Test GitHub login

---

## 🔑 GitHub OAuth Configuration

### Production URLs

**Callback URL:** `https://odooium.odoo-mcp.com/odooium/auth/github/callback`
**Webhook URL:** `https://odooium.odoo-mcp.com/odooium/webhook/github`

### Testing URLs (ngrok)

**Callback URL:** `https://<your-ngrok-url>/odooium/auth/github/callback`
**Webhook URL:** `https://<your-ngrok-url>/odooium/webhook/github`

---

## 📊 Services Status

Check if services are running:

```bash
# Docker containers
docker-compose ps

# Nginx status
sudo systemctl status nginx

# Check ngrok
ps aux | grep ngrok
```

---

## 🐛 Troubleshooting

### Issue: ngrok URL not accessible

**Solution:**
```bash
# Check ngrok logs
tail -f /tmp/ngrok.log

# Restart ngrok
killall ngrok
cd /home/cdsbot/.openclaw/workspace/odoo19-odooium-test
ngrok http 8069
```

### Issue: Odoo not accessible

**Solution:**
```bash
# Check logs
docker-compose logs -f odoo19

# Restart Odoo
docker-compose restart

# Reset database (fresh start)
docker-compose down -v
docker-compose up -d
```

### Issue: SSL Certificate Error

**Solution:**
```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Restart Nginx
sudo systemctl restart nginx
```

---

## 📝 Notes

- **ngrok tunnel** is for testing only
- **Production** uses Nginx + SSL (Let's Encrypt)
- **Default Odoo credentials:** admin/admin (CHANGE IN PRODUCTION!)
- **ngrok URL** changes each time it restarts
- **All files** are in: `/home/cdsbot/.openclaw/workspace/odoo19-odooium-test/`

---

**🐰 Ready to deploy!** 

Run `sudo ./deploy-production.sh` and start testing!
