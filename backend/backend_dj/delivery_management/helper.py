import math
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

class DeliveryRouter:
    """
    Manages delivery-to-store assignment and distance/direction calculations.
    Caches store locations in memory for performance.
    """
    
    def __init__(self):
        self._stores_cache: Optional[Dict[int, Dict[str, Any]]] = None
    
    # ============ Static utility methods ============
    
    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.
        
        Args:
          lat1, lon1: Latitude/longitude of origin in decimal degrees.
          lat2, lon2: Latitude/longitude of destination in decimal degrees.
        
        Returns:
          Distance in kilometers as a float.
        """
        R = 6371.0
        φ1, φ2 = math.radians(float(lat1)), math.radians(float(lat2))
        dφ = math.radians(float(lat2) - float(lat1))
        dλ = math.radians(float(lon2) - float(lon1))
        a = math.sin(dφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    @staticmethod
    def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Compute the initial bearing (forward azimuth) from point A to point B.
        
        Args:
          lat1, lon1: Origin latitude/longitude in decimal degrees.
          lat2, lon2: Destination latitude/longitude in decimal degrees.
        
        Returns:
          Initial bearing in degrees normalized to [0, 360).
        """
        φ1, φ2 = math.radians(float(lat1)), math.radians(float(lat2))
        Δλ = math.radians(float(lon2) - float(lon1))
        x = math.sin(Δλ) * math.cos(φ2)
        y = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(Δλ)
        θ = math.degrees(math.atan2(x, y))
        return (θ + 360) % 360
    
    @staticmethod
    def compass_point(bearing: float, sectors: int = 8) -> str:
        """
        Convert numeric bearing into compass label.
        
        Args:
          bearing: Bearing in degrees.
          sectors: Number of compass sectors (4, 8, 16). Default is 8.
        
        Returns:
          Compass direction string (e.g., 'N', 'NE') or rounded degrees.
        """
        labels_8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        if sectors == 8:
            sector = int((bearing + 360/(2*sectors)) / (360/sectors)) % sectors
            return labels_8[sector]
        return f"{bearing:.0f}°"
    
    # ============ Instance cache management ============
    
    def get_or_cache_stores(self, store_queryset=None) -> Dict[int, Dict[str, Any]]:
        """
        Retrieve stores from cache or fetch from DB if not cached.
        
        Args:
          store_queryset: Django ORM queryset or list of store dicts.
                     If None, will try to import and query Shop model.
        
        Returns:
          Dict mapping store_id -> store_dict with 'id', 'name', 'latitude', 'longitude'.
        """
        if self._stores_cache is not None:
            return self._stores_cache
        
        if store_queryset is None:
            try:
                from delivery_management.models import Shop
                store_queryset = Shop.objects.all()
            except ImportError:
                raise ValueError("store_queryset required or Shop model not available")
        
        self._stores_cache = {}
        for store in store_queryset:
            if isinstance(store, dict):
                # Handle dictionary input
                lat = float(store.get('latitude') or 0.0)
                lon = float(store.get('longitude') or 0.0)
                store_id = store.get('id')
                store_name = store.get('name')
            else:
                # Handle Django model instance
                lat = float(store.latitude) if store.latitude is not None else 0.0
                lon = float(store.longitude) if store.longitude is not None else 0.0
                store_id = store.id
                store_name = store.name
            
            store_dict = {
                "id": store_id,
                "name": store_name,
                "latitude": lat,
                "longitude": lon,
            }
            self._stores_cache[store_dict['id']] = store_dict
    
        return self._stores_cache
    
    def refresh_cache(self, store_queryset=None) -> Dict[int, Dict[str, Any]]:
        """Force refresh of store cache."""
        self._stores_cache = None
        return self.get_or_cache_stores(store_queryset)
    
    # ============ Enrichment and grouping ============
    
    def enrich_and_sort_deliveries(self, store_lat: float, store_lon: float,
                                   deliveries: List[Dict[str, Any]],
                                   compass_sectors: int = 8) -> List[Dict[str, Any]]:
        """
        Enrich delivery list with distance and direction from a reference point,
        sorted by distance ascending.
        
        Args:
          store_lat, store_lon: Reference point (typically a shop).
          deliveries: List of delivery dicts with 'lat'/'latitude' and 'lon'/'longitude'.
          compass_sectors: Granularity for direction labels (default 8).
        
        Returns:
          List of enriched dicts sorted by distance, each with:
            - distance_km, bearing_deg, direction
        """
        out = []
        for d in deliveries:
            try:
                lat = d.get("lat") or d.get("latitude")
                lon = d.get("lon") or d.get("longitude")
                if lat is None or lon is None:
                    continue
                dist = self.haversine_km(store_lat, store_lon, lat, lon)
                bear = self.bearing_deg(store_lat, store_lon, lat, lon)
                dir_label = self.compass_point(bear, sectors=compass_sectors)
                entry = dict(d)
                entry.update({
                    "distance_km": round(dist, 3),
                    "bearing_deg": round(bear, 1),
                    "direction": dir_label,
                })
                out.append(entry)
            except Exception:
                continue
        out.sort(key=lambda x: x["distance_km"])
        return out
    
    def group_by_direction(self, enriched_deliveries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group enriched deliveries by compass direction.
        
        Args:
          enriched_deliveries: Output from enrich_and_sort_deliveries.
        
        Returns:
          Dict mapping direction label -> list of deliveries.
        """
        groups = {}
        for d in enriched_deliveries:
            groups.setdefault(d["direction"], []).append(d)
        return groups
    
    # ============ Store assignment logic ============
    
    def find_nearest_store(self, delivery: Dict[str, Any],
                          stores: Dict[int, Dict[str, Any]]) -> Tuple[Optional[int], float]:
        """
        Find nearest store for a single delivery.
        
        Args:
          delivery: Dict with 'id', 'lat'/'latitude', 'lon'/'longitude'.
          stores: Dict of cached stores (from get_or_cache_stores).
        
        Returns:
          Tuple: (store_id, distance_km)
        """
        delivery_lat = delivery.get("lat") or delivery.get("latitude")
        delivery_lon = delivery.get("lon") or delivery.get("longitude")
        
        if delivery_lat is None or delivery_lon is None:
            raise ValueError(f"Delivery {delivery.get('id')} missing coordinates")
        
        min_distance = float('inf')
        nearest_store_id = None
        
        for store_id, store in stores.items():
            dist = self.haversine_km(store["latitude"], store["longitude"],
                                     delivery_lat, delivery_lon)
            if dist < min_distance:
                min_distance = dist
                nearest_store_id = store_id
        
        return nearest_store_id, min_distance
    
    def assign_deliveries(self, deliveries: List[Dict[str, Any]],
                         store_queryset=None) -> Dict[int, Dict[str, Any]]:
        """
        Iterate through all deliveries and assign each to nearest store.
        
        Args:
          deliveries: List of delivery dicts with id, lat/latitude, lon/longitude.
          store_queryset: Optional Django queryset or list of stores.
        
        Returns:
          Dict mapping delivery_id -> {store_id, distance_km, store_name}
        """
        stores = self.get_or_cache_stores(store_queryset)
        
        assignments = {}
        for delivery in deliveries:
            try:
                delivery_id = delivery.get("id")
                if delivery_id is None:
                    continue
                
                store_id, distance = self.find_nearest_store(delivery, stores)
                if store_id is None:
                    continue
                assignments[delivery_id] = {
                    "store_id": store_id,
                    "distance_km": round(distance, 3),
                    "store_name": stores[store_id].get("name", "Unknown"),
                }
            except Exception as e:
                # log error; skip this delivery
                print(f"Error assigning delivery {delivery.get('id')}: {e}")
                continue
        
        return assignments

    def route_deliveries(self,
                     deliveries: List[Dict[str, Any]],
                     store_queryset=None,
                     compass_sectors: int = 8,
                     max_distance_km: Optional[float] = None
                     ) -> Dict[int, Dict[str, Any]]:
        """
        Orchestrator: load stores, assign deliveries to nearest store,
        then for each store enrich deliveries (distance, bearing, direction)
        and group them by compass direction.

        Returns a dict keyed by store_id with:
          - store: store dict
          - assigned: list of original delivery dicts assigned to this store
          - enriched: list of enriched delivery dicts (distance_km, bearing_deg, direction)
          - groups: dict direction -> list of enriched deliveries
        """
        stores = self.get_or_cache_stores(store_queryset)
        per_store: Dict[int, List[Dict[str, Any]]] = {sid: [] for sid in stores.keys()}

        for d in deliveries:
            try:
                delivery_id = d.get("id")
                if delivery_id is None:
                    continue
                store_id, distance = self.find_nearest_store(d, stores)
                if store_id is None:
                    continue
                if max_distance_km is not None and distance > max_distance_km:
                    continue
                per_store.setdefault(store_id, []).append(d)
            except Exception:
                continue

        result: Dict[int, Dict[str, Any]] = {}
        for store_id, assigned in per_store.items():
            if not assigned:
                continue
            store = stores.get(store_id)
            if not store:
                continue
            store_lat = float(store["latitude"])
            store_lon = float(store["longitude"])
            enriched = self.enrich_and_sort_deliveries(store_lat, store_lon, assigned, compass_sectors)
            groups = self.group_by_direction(enriched)
            result[store_id] = {
                "store": store,
                "assigned": assigned,
                "enriched": enriched,
                "groups": groups,
            }

        return result
