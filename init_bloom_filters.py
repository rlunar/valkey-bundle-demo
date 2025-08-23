#!/usr/bin/env python3
"""
Initialize Bloom filters for tracking viewed products per user.
Run this script once after starting Valkey to set up the Bloom filters.
"""

import valkey
import argparse
from valkey.cluster import ValkeyCluster, ClusterNode

def main():
    parser = argparse.ArgumentParser(description="Initialize Bloom filters for user product views")
    parser.add_argument('--cluster', action='store_true', help="Enable cluster mode for connecting to a Valkey Cluster")
    parser.add_argument('--host', default='localhost', help="Valkey host (default: localhost)")
    parser.add_argument('--port', type=int, default=6379, help="Valkey port (default: 6379)")
    args = parser.parse_args()

    # Connect to Valkey
    try:
        if args.cluster:
            client = ValkeyCluster(startup_nodes=[ClusterNode(host=args.host, port=args.port)])
        else:
            client = valkey.Valkey(host=args.host, port=args.port)
        client.ping()
        print(f"✅ Connected to Valkey at {args.host}:{args.port}")
    except Exception as e:
        print(f"❌ Failed to connect to Valkey: {e}")
        return

    # Get list of users from the database
    user_keys = list(client.scan_iter("user:*"))
    if not user_keys:
        print("⚠️  No users found in database. Make sure to run load_data.py first.")
        return

    print(f"Found {len(user_keys)} users")

    # Initialize Bloom filters for each user
    for user_key in user_keys:
        user_id = user_key.decode().split(':')[1]
        bloom_key = f"viewed:{user_id}"
        
        try:
            # Create Bloom filter with reasonable parameters
            # Error rate: 0.01 (1%), Initial capacity: 1000 items
            client.bf().reserve(bloom_key, 0.01, 1000)
            print(f"✅ Initialized Bloom filter for user {user_id}")
        except Exception as e:
            if "item exists" in str(e).lower():
                print(f"ℹ️  Bloom filter for user {user_id} already exists")
            else:
                print(f"⚠️  Failed to create Bloom filter for user {user_id}: {e}")

    print("🎉 Bloom filter initialization complete!")
    print("Users can now have their product views tracked.")

if __name__ == "__main__":
    main()