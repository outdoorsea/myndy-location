#!/usr/bin/env python3
"""
Place Enrichment Script
File: scripts/enrich_places.py

Cost-optimized enrichment: only geocodes places without names.
Prioritizes high-visit-count places (home, work) first.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.analysis.enrichment import PlaceEnricher
from core.analysis.classification import get_place_classifier
from core.analysis.semantic_enrichment import get_semantic_enricher
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enrich places with reverse geocoding")
    parser.add_argument(
        "--max-calls",
        type=int,
        default=10,
        help="Maximum API calls per run (default: 10)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-enrichment even for places with names",
    )
    parser.add_argument(
        "--min-visits",
        type=int,
        default=1,
        help="Minimum visit count to enrich (default: 1)",
    )

    args = parser.parse_args()

    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"🏷️  Place Enrichment (Cost-Optimized)\n")
    print("=" * 60)
    print(f"Max API calls: {args.max_calls}")
    print(f"Minimum visits: {args.min_visits}")
    print(f"Force re-enrichment: {args.force}\n")

    # Load places that need enrichment
    print("📍 Loading places...")

    if args.force:
        # All places
        query = """
            SELECT id, latitude, longitude, name, visit_count
            FROM places
            WHERE visit_count >= :min_visits
            ORDER BY visit_count DESC, last_visit_at DESC
        """
    else:
        # Only places without names or coordinate-based names
        query = """
            SELECT id, latitude, longitude, name, visit_count
            FROM places
            WHERE (name IS NULL OR name = '' OR name LIKE 'Place at%')
              AND visit_count >= :min_visits
            ORDER BY visit_count DESC, last_visit_at DESC
        """

    result = session.execute(text(query), {"min_visits": args.min_visits})
    places_to_enrich = []

    for row in result:
        places_to_enrich.append({
            'id': str(row[0]),
            'latitude': float(row[1]),
            'longitude': float(row[2]),
            'name': row[3],
            'visit_count': row[4]
        })

    print(f"✅ Found {len(places_to_enrich)} places needing enrichment")

    if not places_to_enrich:
        print("\n✅ All places are already enriched!")
        print("💡 Use --force to re-enrich all places")
        session.close()
        return

    # Limit to max calls
    if len(places_to_enrich) > args.max_calls:
        print(f"⚠️  Limiting to top {args.max_calls} places (sorted by visit count)")
        places_to_enrich = places_to_enrich[:args.max_calls]

    # Initialize enricher, classifier, and semantic enricher
    enricher = PlaceEnricher(
        cache_file="data/place_enrichment_cache.json",
        cache_radius=50.0  # Use cache for places within 50m
    )
    classifier = get_place_classifier()
    semantic_enricher = get_semantic_enricher()

    # Check if semantic enrichment is available
    semantic_enabled = semantic_enricher.client is not None
    if semantic_enabled:
        print(f"✨ Semantic enrichment: ENABLED (using Claude API)")
    else:
        print(f"⚠️  Semantic enrichment: DISABLED (set ANTHROPIC_API_KEY to enable)")

    print(f"\n📍 Enriching {len(places_to_enrich)} places...\n")

    enriched_count = 0
    cached_count = 0
    failed_count = 0

    for i, place in enumerate(places_to_enrich, 1):
        print(f"{i}/{len(places_to_enrich)}: {place['latitude']:.6f}, {place['longitude']:.6f}")
        print(f"   Visits: {place['visit_count']}")

        # Enrich place
        enrichment = enricher.enrich_place(
            place['latitude'],
            place['longitude'],
            force=args.force
        )

        if enrichment:
            # Check if it was from cache
            cache_key = enricher._get_cache_key(place['latitude'], place['longitude'])
            from_cache = cache_key in enricher.cache and not args.force

            if from_cache:
                cached_count += 1
                print(f"   ✅ From cache: {enrichment.name or enrichment.address}")
            else:
                enriched_count += 1
                print(f"   ✅ Geocoded: {enrichment.name or enrichment.address}")

            # Enhanced classification using PlaceClassifier
            classified_type = classifier.classify_place(
                name=enrichment.name,
                place_type=enrichment.place_type,
                metadata={'raw_data': enrichment.raw_data} if hasattr(enrichment, 'raw_data') else None
            )

            # Log if classification improved the type
            if classified_type != (enrichment.place_type or 'unknown'):
                print(f"   🏷️  Improved classification: {enrichment.place_type or 'unknown'} → {classified_type}")

            # Semantic enrichment with Claude API
            semantic_data = None
            if semantic_enabled and enrichment.name:
                try:
                    semantic_data = semantic_enricher.enrich_place(
                        name=enrichment.name,
                        place_type=classified_type,
                        coordinates=(place['latitude'], place['longitude']),
                        address=enrichment.address,
                        city=enrichment.city,
                        visit_stats={
                            'visit_count': place['visit_count']
                        }
                    )
                    if semantic_data:
                        print(f"   ✨ Semantic: {semantic_data.get('description', '')[:60]}...")
                except Exception as e:
                    logger.warning(f"Semantic enrichment failed for {enrichment.name}: {e}")

            # Build address JSONB
            address_data = {}
            if enrichment.address:
                address_data['full_address'] = enrichment.address
            if enrichment.city:
                address_data['city'] = enrichment.city
            if enrichment.state:
                address_data['state'] = enrichment.state
            if enrichment.country:
                address_data['country'] = enrichment.country
            if enrichment.postal_code:
                address_data['postal_code'] = enrichment.postal_code

            # Build place_metadata JSONB (preserve existing metadata)
            metadata = {}
            if semantic_data:
                metadata['semantic'] = semantic_data
            metadata['enriched_at'] = datetime.now(timezone.utc).isoformat()
            metadata['enrichment_source'] = 'reverse_geocoding'

            # Update database
            session.execute(text("""
                UPDATE places
                SET name = :name,
                    address = :address,
                    place_type = :place_type,
                    place_metadata = COALESCE(place_metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {
                'id': place['id'],
                'name': enrichment.name,
                'address': json.dumps(address_data) if address_data else None,
                'place_type': classified_type,  # Use enhanced classification
                'metadata': json.dumps(metadata)
            })

            session.commit()
        else:
            failed_count += 1
            print(f"   ❌ Failed to geocode")

        print()

    # Summary
    print("=" * 60)
    print("\n📊 Enrichment Summary:\n")
    print(f"Total processed: {len(places_to_enrich)}")
    print(f"New API calls: {enriched_count} 💰")
    print(f"From cache: {cached_count} (free!)")
    print(f"Failed: {failed_count}")
    print(f"\nCache size: {len(enricher.cache)} locations")

    if enriched_count > 0:
        print(f"\n💰 API calls used: {enriched_count}/{args.max_calls}")

    # Show top enriched places
    print("\n🏆 Top Enriched Places:\n")
    result = session.execute(text("""
        SELECT name, address, visit_count, last_visit_at
        FROM places
        WHERE name IS NOT NULL AND name NOT LIKE 'Place at%'
        ORDER BY visit_count DESC, last_visit_at DESC
        LIMIT 10
    """))

    for i, row in enumerate(result, 1):
        name = row[0]
        address_json = row[1]
        visits = row[2]
        last_visit = row[3]

        # Extract city/state from address JSONB
        location = "Unknown"
        if address_json:
            try:
                address_data = json.loads(address_json) if isinstance(address_json, str) else address_json
                city = address_data.get("city")
                state = address_data.get("state")
                location = f"{city}, {state}" if city and state else (city or state or "Unknown")
            except:
                location = "Unknown"

        print(f"{i}. {name}")
        print(f"   Location: {location}")
        print(f"   Visits: {visits} | Last visit: {last_visit.strftime('%Y-%m-%d') if last_visit else 'Unknown'}")
        print()

    print("✅ Enrichment complete!")

    if len(places_to_enrich) < len(result.fetchall()) and not args.force:
        remaining = len(result.fetchall()) - len(places_to_enrich)
        print(f"\n💡 {remaining} more places need enrichment")
        print(f"   Run again to enrich {min(remaining, args.max_calls)} more")

    session.close()


if __name__ == "__main__":
    main()
