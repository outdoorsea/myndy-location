#!/usr/bin/env python3
"""
Data Migration Script: Myndy-AI → Myndy-Location
File: scripts/migrate_from_myndy_ai.py

Migrates existing location data from myndy-ai postgres to myndy-location postgres.

Usage:
    python scripts/migrate_from_myndy_ai.py --dry-run
    python scripts/migrate_from_myndy_ai.py --migrate
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocationDataMigrator:
    """Migrates location data from myndy-ai to myndy-location"""

    def __init__(self, source_url: str, target_url: str):
        """
        Initialize migrator

        Args:
            source_url: Connection URL for myndy-ai postgres
            target_url: Connection URL for myndy-location postgres
        """
        self.source_url = source_url
        self.target_url = target_url

    def get_source_counts(self) -> Dict[str, int]:
        """Get counts from source database"""
        logger.info("📊 Querying source database (myndy-ai)...")

        with psycopg2.connect(self.source_url) as conn:
            with conn.cursor() as cur:
                counts = {}

                # Count GPS points
                cur.execute("SELECT COUNT(*) FROM location_data;")
                counts["location_data"] = cur.fetchone()[0]

                # Count places
                try:
                    cur.execute("SELECT COUNT(*) FROM places;")
                    counts["places"] = cur.fetchone()[0]
                except:
                    counts["places"] = 0

                # Count visits
                try:
                    cur.execute("SELECT COUNT(*) FROM visits;")
                    counts["visits"] = cur.fetchone()[0]
                except:
                    counts["visits"] = 0

                # Count movements
                try:
                    cur.execute("SELECT COUNT(*) FROM movements;")
                    counts["movements"] = cur.fetchone()[0]
                except:
                    counts["movements"] = 0

        logger.info(f"✅ Source database counts:")
        for table, count in counts.items():
            logger.info(f"   {table}: {count:,}")

        return counts

    def get_target_counts(self) -> Dict[str, int]:
        """Get counts from target database"""
        logger.info("📊 Querying target database (myndy-location)...")

        with psycopg2.connect(self.target_url) as conn:
            with conn.cursor() as cur:
                counts = {}

                # Count GPS points
                cur.execute("SELECT COUNT(*) FROM location_data;")
                counts["location_data"] = cur.fetchone()[0]

                # Count places
                cur.execute("SELECT COUNT(*) FROM places;")
                counts["places"] = cur.fetchone()[0]

                # Count visits
                cur.execute("SELECT COUNT(*) FROM visits;")
                counts["visits"] = cur.fetchone()[0]

                # Count movements
                cur.execute("SELECT COUNT(*) FROM movements;")
                counts["movements"] = cur.fetchone()[0]

        logger.info(f"✅ Target database counts:")
        for table, count in counts.items():
            logger.info(f"   {table}: {count:,}")

        return counts

    def migrate_location_data(self, batch_size: int = 1000) -> int:
        """
        Migrate GPS location data

        Args:
            batch_size: Number of records to migrate at once

        Returns:
            Number of records migrated
        """
        logger.info("🔄 Migrating location_data (GPS points)...")

        migrated = 0

        with psycopg2.connect(self.source_url) as source_conn:
            with psycopg2.connect(self.target_url) as target_conn:
                source_cur = source_conn.cursor(cursor_factory=RealDictCursor)
                target_cur = target_conn.cursor()

                # Query source data
                source_cur.execute(
                    """
                    SELECT id, timestamp, latitude, longitude, accuracy, altitude,
                           source, data, created_at, updated_at
                    FROM location_data
                    ORDER BY timestamp
                """
                )

                batch = []
                for row in source_cur:
                    batch.append(
                        (
                            row["id"],
                            row["timestamp"],
                            row["latitude"],
                            row["longitude"],
                            row["accuracy"],
                            row["altitude"],
                            None,  # speed (not in old schema)
                            None,  # course (not in old schema)
                            row["source"],
                            row["data"],
                            row["created_at"],
                            row["updated_at"],
                        )
                    )

                    if len(batch) >= batch_size:
                        # Insert batch
                        target_cur.executemany(
                            """
                            INSERT INTO location_data
                                (id, timestamp, latitude, longitude, accuracy, altitude,
                                 speed, course, source, data, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """,
                            batch,
                        )
                        target_conn.commit()
                        migrated += len(batch)
                        logger.info(f"   Migrated {migrated:,} GPS points...")
                        batch = []

                # Insert remaining batch
                if batch:
                    target_cur.executemany(
                        """
                        INSERT INTO location_data
                            (id, timestamp, latitude, longitude, accuracy, altitude,
                             speed, course, source, data, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
                        batch,
                    )
                    target_conn.commit()
                    migrated += len(batch)

        logger.info(f"✅ Migrated {migrated:,} GPS points")
        return migrated

    def run_migration(self) -> Dict[str, Any]:
        """
        Run complete migration

        Returns:
            Migration results
        """
        logger.info("🚀 Starting data migration from myndy-ai to myndy-location...")

        start_time = datetime.now()

        # Get initial counts
        source_counts = self.get_source_counts()
        target_counts_before = self.get_target_counts()

        # Migrate data
        results = {
            "location_data_migrated": self.migrate_location_data(),
            "places_migrated": 0,  # TODO: Implement when place schema is finalized
            "visits_migrated": 0,  # TODO: Implement when visit schema is finalized
            "movements_migrated": 0,  # TODO: Implement
        }

        # Get final counts
        target_counts_after = self.get_target_counts()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info("✅ Migration Complete!")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info("")
        logger.info("📊 Results:")
        for table, count in results.items():
            logger.info(f"   {table}: {count:,}")
        logger.info("")
        logger.info("📈 Target Database After Migration:")
        for table, count in target_counts_after.items():
            logger.info(f"   {table}: {count:,}")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate location data from myndy-ai to myndy-location"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show counts without migrating"
    )
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument(
        "--source",
        default=os.getenv(
            "MYNDY_AI_DATABASE_URL",
            "postgresql://myndy:password@localhost:5434/myndy_ai",
        ),
        help="Source database URL (myndy-ai)",
    )
    parser.add_argument(
        "--target",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://location_user:password@localhost:5435/location_intelligence",
        ),
        help="Target database URL (myndy-location)",
    )

    args = parser.parse_args()

    if not args.dry_run and not args.migrate:
        parser.print_help()
        sys.exit(1)

    # Create migrator
    migrator = LocationDataMigrator(args.source, args.target)

    if args.dry_run:
        logger.info("🔍 Dry run mode - showing counts only")
        logger.info("")
        migrator.get_source_counts()
        logger.info("")
        migrator.get_target_counts()
        logger.info("")
        logger.info("💡 Run with --migrate to perform actual migration")

    elif args.migrate:
        migrator.run_migration()


if __name__ == "__main__":
    main()
