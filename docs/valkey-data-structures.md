# Valkey Data Structures - 5 Minute Overview

## 1. Strings
**Use Case**: Caching, counters, feature flags
```bash
SET user:1001:name "Roberto Luna"
GET user:1001:name
INCR page_views
```

## 2. Lists
**Use Case**: Message queues, activity feeds, recent items
```bash
LPUSH notifications "New order received - B187EAA0-5B55-4824-B196-F1C8B53567F5"
LPUSH notifications "Payment processed - B187EAA0-5B55-4824-B196-F1C8B53567F5" 
LRANGE notifications 0 4  # Get last 5 notifications
RPOP notifications        # Process oldest notification
```

## 3. Sets
**Use Case**: Unique collections, tags, user permissions
```bash
SADD user:1001:interests "technology" "gaming" "music"
SADD user:1002:interests "music" "sports" "travel"
SINTER user:1001:interests user:1002:interests  # Common interests
```

## 4. Sorted Sets (ZSets)
**Use Case**: Leaderboards, rankings, time-series data
```bash
ZADD leaderboard 1500 "player1" 2300 "player2" 1800 "player3"
ZREVRANGE leaderboard 0 2 WITHSCORES  # Top 3 players
ZINCRBY leaderboard 50 "player1"      # Update score
```

## 5. Hashes
**Use Case**: Object storage, user profiles, settings
```bash
HSET product:123 name "Laptop" price 999.99 stock 15
HGET product:123 price
HINCRBY product:123 stock -1  # Decrement stock
```

## 6. Streams
**Use Case**: Event sourcing, real-time analytics, log aggregation
```bash
XADD orders * user_id 1001 product laptop quantity 1 timestamp 1754505659.5724602
XREAD COUNT 10 STREAMS orders $  # Read new entries
```

## 7. Bitmaps
**Use Case**: Analytics, user activity tracking, A/B testing
```bash
SETBIT daily_active_users:2025-01-15 1001 1  # User 1001 active
BITCOUNT daily_active_users:2025-01-15       # Count active users
```

## 8. HyperLogLog
**Use Case**: Approximate cardinality, unique visitors counting
```bash
PFADD unique_visitors user1001 user1002 user1003
PFADD unique_visitors user1001 user1004
PFCOUNT unique_visitors  # Approximate unique count
```

## 9. Geospatial
**Use Case**: Location-based services, proximity searches
```bash
GEOADD restaurants -99.1332 19.4326 "Café Central"
GEOADD restaurants -99.1635 19.4284 "Tacos de la esquina"
GEORADIUS restaurants -99.1400 19.4300 1 km WITHDIST
```

## Performance Tips
- **Strings**: O(1) for GET/SET operations
- **Lists**: O(1) for push/pop at ends, O(N) for middle operations
- **Sets**: O(1) for add/remove/check membership
- **Sorted Sets**: O(log N) for most operations
- **Hashes**: O(1) for field operations
- **Streams**: O(1) for append, O(N) for range queries

## Real-World Application Example
```bash
# E-commerce session data
HSET session:abc123 user_id 1001 cart_total 299.99
SADD session:abc123:viewed product:456 product:789
LPUSH session:abc123:activity "viewed_product:456" "added_to_cart:789"
ZADD trending_products 15 product:456 23 product:789
```

*Each data structure is optimized for specific use cases - choose the right tool for your data access patterns!*