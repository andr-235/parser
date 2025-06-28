#!/usr/bin/env python3
"""
Database Connectivity Test for VK Comments Monitor
Phase 1C: PostgreSQL + Redis Validation
"""

import asyncio
import asyncpg
import redis
import sys
from datetime import datetime
from typing import Optional

# Test Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'vk_monitor',
    'password': 'dev_password_123',
    'database': 'vk_monitor_dev'
}

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': 'dev_redis_password',
    'db': 0
}


async def test_postgresql_connection():
    """Test PostgreSQL connection and basic operations"""
    print("🔍 Testing PostgreSQL Connection...")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ PostgreSQL connection successful")
        
        # Test basic operations
        await conn.execute("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, message TEXT, created_at TIMESTAMP)")
        print("✅ Table creation successful")
        
        # Insert test data
        await conn.execute("INSERT INTO test_table (message, created_at) VALUES ($1, $2)", 
                          "Test message from VK Monitor", datetime.now())
        print("✅ Data insertion successful")
        
        # Query test data
        rows = await conn.fetch("SELECT * FROM test_table LIMIT 5")
        print(f"✅ Data query successful: {len(rows)} rows retrieved")
        
        # Cleanup
        await conn.execute("DROP TABLE test_table")
        print("✅ Table cleanup successful")
        
        await conn.close()
        print("✅ PostgreSQL validation PASSED\n")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL error: {e}")
        return False


def test_redis_connection():
    """Test Redis connection and basic operations"""
    print("🔍 Testing Redis Connection...")
    
    try:
        # Connect to Redis
        r = redis.Redis(**REDIS_CONFIG)
        
        # Test connection
        r.ping()
        print("✅ Redis connection successful")
        
        # Test basic operations
        r.set("test_key", "VK Monitor Test Value")
        print("✅ Redis SET operation successful")
        
        value = r.get("test_key")
        print(f"✅ Redis GET operation successful: {value.decode()}")
        
        # Test expiration
        r.setex("temp_key", 60, "Temporary value")
        ttl = r.ttl("temp_key")
        print(f"✅ Redis TTL operation successful: {ttl} seconds")
        
        # Cleanup
        r.delete("test_key", "temp_key")
        print("✅ Redis cleanup successful")
        
        print("✅ Redis validation PASSED\n")
        return True
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False


async def main():
    """Main validation function"""
    print("🚀 VK Comments Monitor - Database Connectivity Test")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Test PostgreSQL
    postgres_ok = await test_postgresql_connection()
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Results
    print("📊 VALIDATION RESULTS:")
    print("=" * 30)
    print(f"PostgreSQL: {'✅ PASSED' if postgres_ok else '❌ FAILED'}")
    print(f"Redis:      {'✅ PASSED' if redis_ok else '❌ FAILED'}")
    print()
    
    if postgres_ok and redis_ok:
        print("🎉 ALL TESTS PASSED! Database connectivity validated.")
        print("📋 Next step: VKBottle VK API integration test")
        return 0
    else:
        print("⚠️  Some tests failed. Check Docker containers and configuration.")
        print("💡 Run: docker-compose -f docker-compose.dev.yml up -d")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
