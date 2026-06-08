# WebSocket Real-Time Item Updates - Testing Guide

## Overview
Phase 1 WebSocket implementation is now complete! The system now notifies all connected clients in real-time when items are created, updated, or deleted.

## Architecture

### Backend Flow
```
Admin updates item in Django Admin/API
    ↓
Django signal fires (post_save/post_delete) → pizza_management/signals.py
    ↓
Signal broadcasts to Channel Layer (Redis)
    ↓
ItemUpdateConsumer receives event
    ↓
Consumer broadcasts to "items_updates" group
    ↓
All connected WebSocket clients receive notification
```

### Frontend Flow
```
React App mounts (App.tsx)
    ↓
useItemWebSocket hook initializes (services/itemWebSocket.ts)
    ↓
useWebSocket hook connects to ws://localhost:8000/ws/items/updates/
    ↓
Sends subscription request to server
    ↓
Listens for: item_created, item_updated, item_deleted events
    ↓
On event: invalidates store cache + forces fresh fetch
    ↓
UI updates with fresh data automatically
```

## Testing Steps

### Prerequisites
- Backend running: `python manage.py runserver`
- Frontend running: `npm run dev`
- Redis running: `redis-server`
- Channels + Daphne installed

### Test 1: Verify WebSocket Connection

**Browser Console:**
1. Open web frontend in browser
2. Open DevTools Console (F12)
3. Look for these messages:
   ```
   ✅ WebSocket connected: ws://localhost:8000/ws/items/updates/
   ✅ Subscribed to item updates
   ```

### Test 2: Create New Item

**In Django Admin (http://localhost:8000/admin/):**
1. Go to Pizza Management → Items
2. Click "Add Item"
3. Fill in item details (name, category, price, etc.)
4. Click Save

**Expected Output:**
- Terminal shows: `✨ New item created: <item_name> (ID: <id>)`
- Browser console shows:
  ```
  📬 WebSocket message received: item_created
  ✨ New item created: <item_name> (ID: <id>)
  ```
- Frontend items list cache is invalidated
- If viewing ItemList, new item appears after refresh

### Test 3: Update Existing Item

**In Django Admin:**
1. Go to Pizza Management → Items
2. Click on an existing item to edit
3. Change the name or price
4. Click Save

**Expected Output:**
- Terminal shows: `🔄 Item updated: <item_name> (ID: <id>)`
- Browser console shows:
  ```
  📬 WebSocket message received: item_updated
  🔄 Item updated: <item_name> (ID: <id>)
  ```
- If currently viewing ItemDetail for that item, cache is cleared
- Next ItemDetail fetch gets fresh data

### Test 4: Delete Item

**In Django Admin:**
1. Go to Pizza Management → Items
2. Select an item checkbox
3. Change Action dropdown to "Delete selected items"
4. Click Go

**Expected Output:**
- Terminal shows: `🗑️ Item deleted (ID: <id>)`
- Browser console shows:
  ```
  📬 WebSocket message received: item_deleted
  🗑️ Item deleted (ID: <id>)
  ```
- If item was in currentItem cache, it's cleared
- Item removed from items list cache

### Test 5: Multiple Tabs/Sessions

1. Open frontend in two separate browser tabs
2. In Tab 1, navigate to ItemList
3. In Tab 2, go to Django Admin and create a new item
4. Watch Tab 1's ItemList page - items cache is invalidated
5. Next time user navigates or page refreshes, they see the new item

### Test 6: Reconnection Logic

**Simulate disconnection:**
1. Open browser DevTools Network tab
2. Go to DevTools → Network conditions
3. Set "Throttling" to "Offline"
4. Watch console - should see connection attempts
5. Re-enable connection
6. Should auto-reconnect with exponential backoff

**Expected Console:**
```
📭 WebSocket closed
🔄 Reconnecting... attempt 1/5
✅ WebSocket connected (after 3 seconds)
```

## Files Modified/Created

### Backend
- ✅ `backend_dj/settings.py` - Added channels, daphne, ASGI config
- ✅ `backend_dj/asgi.py` - Integrated ProtocolTypeRouter
- ✅ `backend_dj/routing.py` - WebSocket URL routing (NEW)
- ✅ `pizza_management/item/consumers.py` - ItemUpdateConsumer (NEW)
- ✅ `pizza_management/signals.py` - Broadcasting signals (UPDATED)
- ✅ `pizza_management/apps.py` - Signal import in ready() (UPDATED)
- ✅ `requirements.txt` - Added channels[daphne], channels-redis

### Frontend
- ✅ `src/hooks/useWebSocket.ts` - WebSocket hook (NEW)
- ✅ `src/services/itemWebSocket.ts` - Item WebSocket service (NEW)
- ✅ `src/store/itemStore.ts` - Cache invalidation methods (UPDATED)
- ✅ `src/App.tsx` - Initialize WebSocket on mount (UPDATED)

## Troubleshooting

### WebSocket won't connect
```
Error: Failed to create WebSocket
```
**Solution:**
- Ensure backend is running on port 8000
- Check Channels dependency: `pip list | grep channels`
- Verify ASGI_APPLICATION in settings.py
- Check browser console for exact error

### No notification received
```
❌ WebSocket error: [error details]
```
**Solution:**
- Verify Redis is running: `redis-cli ping` (should return PONG)
- Check CHANNEL_LAYERS config in settings.py
- View Django logs for signal errors
- Ensure Item model has post_save signal connected

### Browser keeps reconnecting
```
🔄 Reconnecting... attempt X/5
```
**Solution:**
- Check network tab in DevTools
- Verify backend hasn't crashed
- Look for CORS issues in browser console
- Ensure protocol matches (ws:// for HTTP, wss:// for HTTPS)

### Items not updating in UI
**Solution:**
- Verify store's `invalidateItemCache()` is called
- Check itemStore implementations in ItemList/ItemDetail
- Look for error in browser console
- Manually refresh page to verify data updates work

## Next Steps (Phase 2)

- Order update notifications
- Payment status notifications
- Delivery tracking real-time updates
- Batch operations with progress tracking

## Performance Notes

- Each client connection uses ~5-10KB memory
- Redis channel layer handles broadcasting
- Messages are JSON, ~200-500 bytes per notification
- Exponential backoff prevents reconnection storms
- Auto-disconnect on tab close (browser handles)

## Production Deployment

When deploying to production:

1. **HTTPS/WSS:**
   ```python
   # settings.py
   SECURE_SSL_REDIRECT = True
   WS_SCHEME = "wss"
   ```

2. **WSGI → DAPHNE:**
   ```bash
   # Use daphne instead of gunicorn
   daphne -b 0.0.0.0 -p 8000 backend_dj.asgi:application
   ```

3. **Load Balancer:**
   - WebSocket requires sticky sessions
   - Configure session affinity for WS connections

4. **Redis URL:**
   ```python
   # Use environment variable for cloud Redis
   CHANNEL_LAYERS = {
       "default": {
           "BACKEND": "channels_redis.core.RedisChannelLayer",
           "CONFIG": {
               "hosts": [os.getenv('REDIS_URL', 'redis://localhost:6379/1')],
           },
       },
   }
   ```
