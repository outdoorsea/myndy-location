"""
Place Enrichment Module
File: core/analysis/enrichment.py

Cost-optimized reverse geocoding for place names and addresses.
Uses caching and proximity checks to minimize API calls.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

logger = logging.getLogger("myndy.enrichment")


@dataclass
class PlaceEnrichment:
    """Enriched place information from reverse geocoding"""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    place_type: Optional[str] = None
    raw_data: Optional[Dict] = None


class PlaceEnricher:
    """
    Cost-optimized place enrichment via reverse geocoding

    Features:
    - Local JSON cache to avoid duplicate API calls
    - Proximity checking (uses cached data for nearby places)
    - Rate limiting (1 request per second for Nominatim)
    - Configurable max requests per run
    """

    def __init__(self, cache_file: str = "data/place_enrichment_cache.json", cache_radius: float = 50.0):
        """
        Initialize place enricher

        Args:
            cache_file: Path to JSON cache file
            cache_radius: Distance in meters to consider places as "same location" for caching
        """
        self.cache_file = Path(cache_file)
        self.cache_radius = cache_radius
        self.cache: Dict[str, PlaceEnrichment] = {}
        self.geocoder = Nominatim(user_agent="myndy-location-intelligence/1.0")
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds (Nominatim rate limit)

        # Load existing cache
        self.load_cache()

        logger.info(f"Initialized PlaceEnricher with cache at {self.cache_file}")
        logger.info(f"Cache contains {len(self.cache)} entries")

    def load_cache(self):
        """Load enrichment cache from JSON file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Convert dict back to PlaceEnrichment objects
                    self.cache = {
                        key: PlaceEnrichment(**value)
                        for key, value in data.items()
                    }
                logger.info(f"Loaded {len(self.cache)} cached enrichments")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def save_cache(self):
        """Save enrichment cache to JSON file"""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert PlaceEnrichment objects to dicts
            data = {
                key: {
                    'name': value.name,
                    'address': value.address,
                    'city': value.city,
                    'state': value.state,
                    'country': value.country,
                    'postal_code': value.postal_code,
                    'place_type': value.place_type,
                    'raw_data': value.raw_data
                }
                for key, value in self.cache.items()
            }

            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.cache)} enrichments to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _get_cache_key(self, latitude: float, longitude: float) -> str:
        """Generate cache key for coordinates (rounded to ~11m precision)"""
        return f"{latitude:.4f},{longitude:.4f}"

    def _find_cached_nearby(self, latitude: float, longitude: float) -> Optional[PlaceEnrichment]:
        """
        Check if there's a cached place within cache_radius

        Args:
            latitude: Place latitude
            longitude: Place longitude

        Returns:
            PlaceEnrichment if found nearby, None otherwise
        """
        for cache_key, enrichment in self.cache.items():
            try:
                cache_lat, cache_lng = map(float, cache_key.split(','))
                distance = geodesic((latitude, longitude), (cache_lat, cache_lng)).meters

                if distance <= self.cache_radius:
                    logger.debug(f"Found cached place within {distance:.0f}m")
                    return enrichment
            except Exception:
                continue

        return None

    def enrich_place(self, latitude: float, longitude: float, force: bool = False) -> Optional[PlaceEnrichment]:
        """
        Enrich a place with reverse geocoding

        Args:
            latitude: Place latitude
            longitude: Place longitude
            force: If True, bypass cache and make API call

        Returns:
            PlaceEnrichment object or None if geocoding fails
        """
        cache_key = self._get_cache_key(latitude, longitude)

        # Check cache first (unless force=True)
        if not force:
            # Exact cache match
            if cache_key in self.cache:
                logger.debug(f"Cache hit (exact): {cache_key}")
                return self.cache[cache_key]

            # Nearby cache match
            nearby = self._find_cached_nearby(latitude, longitude)
            if nearby:
                logger.debug(f"Cache hit (nearby): {cache_key}")
                # Store in cache at this location too
                self.cache[cache_key] = nearby
                return nearby

        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        # Make API call
        try:
            logger.info(f"Reverse geocoding: {latitude:.6f}, {longitude:.6f}")
            location = self.geocoder.reverse(f"{latitude}, {longitude}", timeout=10)
            self.last_request_time = time.time()

            if not location:
                logger.warning(f"No result for {latitude}, {longitude}")
                return None

            # Parse result
            address = location.raw.get('address', {})

            # Get place name - prioritize actual place names over addresses
            place_name = location.raw.get('name', '')
            if not place_name or place_name.isdigit():
                # Fallback: check for business/poi name in address
                place_name = (
                    address.get('amenity') or
                    address.get('shop') or
                    address.get('building') or
                    address.get('tourism') or
                    location.raw.get('display_name', '').split(',')[0]
                )

            enrichment = PlaceEnrichment(
                name=place_name,
                address=location.address,
                city=address.get('city') or address.get('town') or address.get('village'),
                state=address.get('state'),
                country=address.get('country'),
                postal_code=address.get('postcode'),
                place_type=self._classify_place_type(address),
                raw_data=location.raw
            )

            # Cache the result
            self.cache[cache_key] = enrichment
            self.save_cache()

            logger.info(f"Enriched: {enrichment.name or enrichment.address}")
            return enrichment

        except Exception as e:
            logger.error(f"Geocoding failed for {latitude}, {longitude}: {e}")
            return None

    def _classify_place_type(self, address: Dict) -> str:
        """Classify place type from address components"""
        # Check for common place types in address
        if 'amenity' in address:
            return address['amenity']
        elif 'shop' in address:
            return 'commercial'
        elif 'building' in address:
            building = address['building']
            if building in ['house', 'residential', 'apartments']:
                return 'residence'
            return 'building'
        elif 'highway' in address:
            return 'road'
        else:
            return 'unknown'
