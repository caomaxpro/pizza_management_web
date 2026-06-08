# WebSocket Setup Analysis Report - Pizza Admin Web

**Date:** June 2, 2026  
**Status:** ✅ Complete implementation with 3 active consumers

---

## 1. Architecture Overview

Your project has a **full-stack WebSocket implementation** using:
- **Backend:** Django Channels (v4.1.0) with Daphne ASGI server
- **Frontend:** Native browser WebSocket API with React hooks
- **Channel Layer:** InMemoryChannelLayer (development) / RedisChannelLayer (production option)

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React + TypeScript)                               │
│ ├─ useWebSocket.ts (generic handler)                        │
│ ├─ itemWebSocket.ts (Items service)                         │
│ ├─ ingredientWebSocket.ts (Ingredients service)             │
│ └─ useInventoryWebSocket.ts (Inventory hook)                │
└────────────┬────────────────────────────────────────────────┘
             │ ws:// connection
             │
┌────────────▼────────────────────────────────────────────────┐
│ Backend (Django Channels)                                   │
│ ├─ asgi.py (ProtocolTypeRouter)                             │
│ ├─ routing.py (URL patterns)                                │
│ ├─ consumers.py (3 AsyncWebsocketConsumers)                 │
│ └─ signals.py (DB triggers → broadcasts)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Setup

### 2.1 ASGI Configuration
📄 **File:** `backend_dj/backend_dj/asgi.py`

```python
# Route protocol types
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Regular HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)  # WebSocket connections
    ),
})
```

**Key Features:**
- ✅ AuthMiddlewareStack - preserves user authentication across WebSocket
- ✅ URLRouter - maps paths to consumers
- ✅ Integrated with Django settings.ASGI_APPLICATION

### 2.2 WebSocket URL Routing
📄 **File:** `backend_dj/backend_dj/routing.py`

```python
websocket_urlpatterns = [
    path("ws/items/updates/", ItemUpdateConsumer.as_asgi(), name="ws_item_updates"),
    path("ws/ingredients/updates/", IngredientUpdateConsumer.as_asgi(), name="ws_ingredient_updates"),
    path("ws/inventory/updates/", InventoryUpdateConsumer.as_asgi(), name="ws_inventory_updates"),
]
```

| Endpoint | Consumer | Group Name | Events |
|----------|----------|-----------|--------|
| `/ws/items/updates/` | ItemUpdateConsumer | `items_updates` | create, update, delete |
| `/ws/ingredients/updates/` | IngredientUpdateConsumer | `ingredients_updates` | create, update, delete |
| `/ws/inventory/updates/` | InventoryUpdateConsumer | `inventory_updates` | create, update, delete |

### 2.3 Existing Consumers

#### **ItemUpdateConsumer**
📄 `pizza_management/item/consumers.py`

```python
class ItemUpdateConsumer(AsyncWebsocketConsumer):
    # Group: "items_updates"
    # Lifecycle:
    # - connect() → joins group + accepts connection
    # - disconnect() → leaves group
    # - receive() → handles client messages (subscribe type)
    
    # Broadcast handlers:
    async def item_created(self, event)       # Called by signal
    async def item_updated(self, event)       # Called by signal
    async def item_deleted(self, event)       # Called by signal
```

**Example Message:**
```json
{
  "type": "item_updated",
  "item_id": 42,
  "item_name": "Pepperoni Pizza",
  "message": "Item updated: Pepperoni Pizza"
}
```

#### **IngredientUpdateConsumer**
📄 `pizza_management/ingredient/consumers.py`

- Identical pattern to ItemUpdateConsumer
- Group: `ingredients_updates`
- Events: `ingredient_created`, `ingredient_updated`, `ingredient_deleted`

#### **InventoryUpdateConsumer**
📄 `stock_management/inventory/consumers.py`

- Minimal implementation (no logging)
- **Serialization:** Full inventory object included in message
- Uses `_serialize_inventory()` utility for JSON compatibility
- Group: `inventory_updates`

**Example Message:**
```json
{
  "type": "inventory_updated",
  "inventory": {
    "id": 1,
    "name": "Mozzarella Cheese",
    "quantity": 50,
    "unit": "kg",
    "provider": {...}
  }
}
```

### 2.4 Signal Broadcasting Chain

#### **Pizza Management Signals**
📄 `pizza_management/signals.py`

```python
# On database save event:
@receiver(post_save, sender=Item)
def broadcast_item_update(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    if channel_layer is None: return
    
    event_data = {"item_id": instance.id, "item_name": instance.name}
    try:
        if created:
            async_to_sync(channel_layer.group_send)(
                "items_updates",
                {"type": "item_created", **event_data}
            )
        else:
            async_to_sync(channel_layer.group_send)(
                "items_updates",
                {"type": "item_updated", **event_data}
            )
    except Exception as e:
        print(f"⚠️ Failed to broadcast: {e}")
```

**Flow:**
1. Django model save → post_save signal
2. Signal handler calls `channel_layer.group_send()`
3. All consumers in group receive event
4. Consumer's method (e.g., `item_updated()`) is invoked
5. Message sent to all connected WebSocket clients

#### **Inventory Signals (Transaction-Safe)**
📄 `stock_management/inventory/signals.py`

```python
# More robust - uses transaction.on_commit()
@receiver(post_save, sender=Inventory)
def broadcast_inventory_save(sender, instance, created, **kwargs):
    def send():
        data = _serialize_inventory(instance)
        _broadcast({"type": "inventory_created", "inventory": data})
    
    # Waits until transaction commits → clients see consistent data
    transaction.on_commit(send)
```

**Benefits:**
- ✅ Data consistency - broadcast only after DB commit
- ✅ No "phantom reads" from clients
- ✅ Production-ready pattern

### 2.5 Channels Configuration
📄 `backend_dj/settings.py` (lines 351-372)

**INSTALLED_APPS:**
```python
INSTALLED_APPS = [
    'daphne',      # ← ASGI server (must be first)
    'channels',    # ← WebSocket support
    ...
]
```

**Channel Layer:**
```python
# Development (in-memory):
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Production (commented out - use Redis):
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {"hosts": [("127.0.0.1", 6380)]},
#     },
# }
```

**ASGI Application:**
```python
ASGI_APPLICATION = "backend_dj.asgi.application"
```

### 2.6 Backend Dependencies
📄 `requirements.txt`

```
channels[daphne]==4.1.0     # ← Core WebSocket library
redis==7.4.0                # ← Optional for production
asgiref==3.11.1             # ← ASGI framework
```

---

## 3. Frontend Setup

### 3.1 Core WebSocket Hook
📄 `web_frontend/src/hooks/useWebSocket.ts`

**Generic TypeScript Hook:**
```typescript
interface UseWebSocketOptions<T> {
    url: string;
    onOpen?: () => void;
    onClose?: () => void;
    onMessage: (data: T) => void;
    onError?: (error: Event) => void;
    reconnectAttempts?: number;    // Default: 5
    reconnectDelay?: number;       // Default: 3000ms
}

export const useWebSocket = <T = WebSocketMessage>({
    url,
    onOpen,
    onClose,
    onMessage,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
}: UseWebSocketOptions<T>) => {
    // Returns: { isConnected, send, disconnect }
}
```

**Features:**
- ✅ **Auto-reconnect** with exponential backoff
- ✅ **Generic typing** for different message types
- ✅ **Lifecycle callbacks** (onOpen, onClose, onError)
- ✅ **Manual send()** for custom messages
- ✅ **TypeSafe JSON parsing**

**Connection Flow:**
```
1. Component mounts → hook creates WebSocket
2. ws.onopen()
   ├─ Sets isConnected = true
   ├─ Resets reconnect counter
   └─ Sends {"type": "subscribe"}
3. ws.onmessage() → calls onMessage callback
4. On error/close → attempts reconnect
```

### 3.2 Connection URL Pattern
Dynamic protocol selection:
```typescript
const getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    
    if (import.meta.env.DEV) {
        // Development: explicit port
        return `${protocol}//${window.location.hostname}:8000/ws/items/updates/`;
    } else {
        // Production: same host
        return `${protocol}//${window.location.host}/ws/items/updates/`;
    }
};
```

**URL Examples:**
- Dev: `ws://localhost:8000/ws/items/updates/`
- Prod (HTTP): `ws://example.com/ws/items/updates/`
- Prod (HTTPS): `wss://example.com/ws/items/updates/`

### 3.3 Item WebSocket Service
📄 `web_frontend/src/services/itemWebSocket.ts`

```typescript
export const useItemWebSocket = () => {
    const store = useItemStore();
    
    const handleMessage = (message: WebSocketMessage) => {
        switch (message.type) {
            case "item_created":
                store.setItems([]);  // ← Clear cache, will refetch
                break;
            case "item_updated":
                store.invalidateItemCache(message.item_id);  // ← Refetch single
                break;
            case "item_deleted":
                store.removeItemFromCache(message.item_id);  // ← Remove from cache
                break;
        }
    };
    
    const { isConnected, send } = useWebSocket({
        url: getWebSocketUrl(),
        onMessage: handleMessage,
        reconnectAttempts: 5,
        reconnectDelay: 3000,
    });
    
    return { isConnected, send };
};
```

**Cache Strategy:**
| Event | Action | Reasoning |
|-------|--------|-----------|
| item_created | Clear all items | New item entered list, refresh needed |
| item_updated | Refetch single | Get latest data for specific item |
| item_deleted | Remove from cache | Item no longer exists |

### 3.4 Ingredient WebSocket Service
📄 `web_frontend/src/services/ingredientWebSocket.ts`

```typescript
const handleMessage = (message: WebSocketMessage) => {
    const { fetchAllIngredients, removeIngredientFromCache } = 
        useIngredientStore.getState();
    
    switch (message.type) {
        case "ingredient_created":
        case "ingredient_updated":
            fetchAllIngredients(true);  // ← Force refresh
            break;
        case "ingredient_deleted":
            removeIngredientFromCache(message.ingredient_id);
            break;
    }
}
```

**Uses getState()** to avoid stale closure issues with Zustand.

### 3.5 Inventory WebSocket Hook
📄 `web_frontend/src/hooks/useInventoryWebSocket.ts`

Callback-based pattern (used in `Inventory.tsx` and `InventoryDetails.tsx`):

```typescript
export const useInventoryWebSocket = (
    onUpdate: (item: InventoryItem) => void,
    onDelete: (id: number) => void,
    onCreate: (item: InventoryItem) => void,
) => {
    const handleMessage = (msg: InventoryWSMessage) => {
        switch (msg.type) {
            case "inventory_created":
                onCreate(msg.inventory);
                break;
            case "inventory_updated":
                onUpdate(msg.inventory);
                break;
            case "inventory_deleted":
                onDelete(msg.inventory_id);
                break;
        }
    };
    
    const { isConnected } = useWebSocket({
        url: getWebSocketUrl(),
        onMessage: handleMessage,
    });
    
    return { isConnected };
};
```

**Usage in Components:**
```typescript
const handleWSUpdate = useCallback(
    (item: InventoryItem) => 
        setItems((prev) => prev.map((i) => (i.id === item.id ? item : i))),
    [],
);
const handleWSDelete = useCallback(
    (id: number) => setItems((prev) => prev.filter((i) => i.id !== id)),
    [],
);
const handleWSCreate = useCallback(
    (item: InventoryItem) => setItems((prev) => [item, ...prev]),
    [],
);

useInventoryWebSocket(handleWSUpdate, handleWSDelete, handleWSCreate);
```

### 3.6 App-Level Initialization
📄 `web_frontend/src/App.tsx`

```typescript
function App() {
    // Initialize ALL WebSocket connections on app mount
    useItemWebSocket();
    useIngredientWebSocket();
    // Note: useInventoryWebSocket is per-page, not global
    
    return (
        <Router>
            <AppRoutes />
        </Router>
    );
}
```

### 3.7 Frontend Dependencies
📄 `web_frontend/package.json`

```json
{
  "dependencies": {
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "zustand": "^5.0.12",  // ← State management for cache
    "axios": "^1.13.6"     // ← API client
  }
}
```

**No external WebSocket library** - uses native browser API.

---

## 4. Message Format Specifications

### 4.1 Client → Server (Subscription)
```json
{
  "type": "subscribe"
}
```

**Response:**
```json
{
  "type": "subscription_confirmed",
  "message": "Subscribed to item updates"
}
```

### 4.2 Server → Client (Item Events)
```json
{
  "type": "item_created",          // or "item_updated", "item_deleted"
  "item_id": 42,
  "item_name": "Margherita Pizza",
  "message": "New item created: Margherita Pizza"
}
```

### 4.3 Server → Client (Ingredient Events)
```json
{
  "type": "ingredient_created",    // or "ingredient_updated", "ingredient_deleted"
  "ingredient_id": 7,
  "ingredient_name": "Tomato Sauce",
  "message": "New ingredient created: Tomato Sauce"
}
```

### 4.4 Server → Client (Inventory Events)
```json
{
  "type": "inventory_updated",     // or "inventory_created", "inventory_deleted"
  "inventory": {
    "id": 1,
    "name": "Mozzarella Cheese",
    "quantity": 50,
    "unit": "kg",
    "unit_price": 12.50,
    "total_value": 625.00,
    "provider": {
      "id": 2,
      "name": "Italian Suppliers Inc."
    },
    "is_active": true,
    "last_updated": "2026-06-02T10:30:00Z"
  }
}
```

### 4.5 Error Messages
```json
{
  "type": "error",
  "message": "Invalid JSON format"
}
```

---

## 5. Serialization & Data Flow

### 5.1 Backend Serialization

**Items/Ingredients:** Basic serialization
```python
event_data = {
    "item_id": instance.id,
    "item_name": instance.name,
}
```

**Inventory:** Full object serialization (transactional)
```python
def _serialize_inventory(instance: Inventory) -> dict:
    data_bytes = JSONRenderer().render(InventorySerializer(instance).data)
    return json.loads(data_bytes)
```

**Why the difference?**
- Items/Ingredients: Only metadata needed for cache invalidation
- Inventory: Full details required for UI updates (stock levels, prices, provider info)

### 5.2 Frontend Deserialization

Type-safe parsing in useWebSocket:
```typescript
ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data) as T;
        onMessage(data);
    } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
    }
};
```

Each service defines its message interface:
```typescript
interface WebSocketMessage {
    type: "item_created" | "item_updated" | "item_deleted" | 
          "subscription_confirmed" | "error";
    item_id?: number;
    item_name?: string;
    message?: string;
}
```

---

## 6. Connection Flow Diagram

### Connection Lifecycle
```
Client                              Server
 │                                   │
 ├─────── new WebSocket(url) ───────→│
 │                                   ├─ connect()
 │                                   ├─ group_add("items_updates")
 │                                   ├─ accept()
 │←────────── onopen ────────────────┤
 │                                   │
 ├─── {"type": "subscribe"} ────────→│
 │                                   ├─ receive()
 │                                   ├─ send(subscription_confirmed)
 │←─ {"type": "subscription_confirmed"} ─┤
 │                                   │
 │        [Listening for events...]  │
 │                                   │
 │                        [DB Save]  │
 │                                   ├─ post_save signal
 │                                   ├─ group_send("items_updates", event)
 │                                   ├─ item_updated(event)
 │←── {"type": "item_updated": ...} ─┤
 │                                   │
 └─── ws.close() ───────────────────→│
                                     ├─ disconnect()
                                     ├─ group_discard()
```

---

## 7. Configuration Checklist

### Backend Configuration
- ✅ `daphne` in INSTALLED_APPS (must be first)
- ✅ `channels` in INSTALLED_APPS
- ✅ `ASGI_APPLICATION = "backend_dj.asgi.application"`
- ✅ `CHANNEL_LAYERS` configured (InMemoryChannelLayer for dev)
- ✅ `asgi.py` with ProtocolTypeRouter
- ✅ `routing.py` with websocket_urlpatterns
- ✅ Consumers created with AsyncWebsocketConsumer
- ✅ Signal handlers broadcasting to channel groups

### Frontend Configuration
- ✅ useWebSocket hook implemented with generic typing
- ✅ Service/hook for each consumer endpoint
- ✅ Dynamic URL with protocol detection
- ✅ Message type handling in callbacks
- ✅ Store integration for cache management
- ✅ Initialization in App component

---

## 8. Production Considerations

### Current Issues
1. **InMemoryChannelLayer** - works only on single server
   - Solution: Switch to `channels_redis.core.RedisChannelLayer`
   - Uncomment configuration in settings.py
   - Ensure Redis running on port 6380

2. **No Authentication on WebSocket**
   - AuthMiddlewareStack is applied but no permission checks
   - Consider: Add permission check in `connect()` method
   - Example: Verify user is authenticated before accept()

3. **No Rate Limiting**
   - Clients can spam subscribe/messages
   - Solution: Add rate limiting middleware

### Recommended Enhancements
```python
# In consumer:
async def connect(self):
    if not self.scope["user"].is_authenticated:
        await self.close()
        return
    # ... rest of connect
```

---

## 9. Testing WebSocket

### Backend Test
```bash
# Using Django shell + channels
python manage.py shell

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    "items_updates",
    {"type": "item_created", "item_id": 1, "item_name": "Test"}
)
```

### Frontend Test (Browser Console)
```javascript
// Connect to WebSocket
const ws = new WebSocket("ws://localhost:8000/ws/items/updates/");

ws.onopen = () => {
    console.log("Connected!");
    ws.send(JSON.stringify({ type: "subscribe" }));
};

ws.onmessage = (e) => {
    console.log("Message:", JSON.parse(e.data));
};

// Simulate backend event (from admin or API)
// Then watch console for incoming message
```

---

## 10. Summary

| Aspect | Value |
|--------|-------|
| **Framework** | Django Channels 4.1.0 |
| **Protocol** | WebSocket (ws/wss) |
| **Authentication** | AuthMiddlewareStack (user session preserved) |
| **Channel Layer** | InMemoryChannelLayer (dev) |
| **Consumers** | 3 (Items, Ingredients, Inventory) |
| **Frontend Lib** | Native WebSocket API |
| **Serialization** | JSON |
| **Auto-Reconnect** | Yes (5 attempts, 3s exponential backoff) |
| **Frontend Framework** | React 19 + Zustand |
| **Message Format** | Type-based (item_created, item_updated, etc.) |

**Status:** Production-ready with minor enhancements recommended for multi-server deployment.
