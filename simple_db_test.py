#!/usr/bin/env python3
"""
Simple Database Connectivity Test for VK Comments Monitor
Testing via direct socket connections without external dependencies
"""

import socket
from datetime import datetime

# Test Configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
REDIS_HOST = "localhost"
REDIS_PORT = 6379


def test_postgresql_socket():
    """Test PostgreSQL socket connection"""
    print("🔍 Testing PostgreSQL Socket Connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((POSTGRES_HOST, POSTGRES_PORT))
        sock.close()

        if result == 0:
            print("✅ PostgreSQL socket connection successful")
            return True
        else:
            print(f"❌ PostgreSQL socket connection failed: {result}")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL socket error: {e}")
        return False


def test_redis_socket():
    """Test Redis socket connection"""
    print("🔍 Testing Redis Socket Connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((REDIS_HOST, REDIS_PORT))
        sock.close()

        if result == 0:
            print("✅ Redis socket connection successful")
            return True
        else:
            print(f"❌ Redis socket connection failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Redis socket error: {e}")
        return False


def test_adminer_http():
    """Test Adminer HTTP connection"""
    print("🔍 Testing Adminer HTTP Connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", 8080))
        sock.close()

        if result == 0:
            print("✅ Adminer HTTP connection successful")
            print("💡 Access Adminer at: http://localhost:8080")
            return True
        else:
            print(f"❌ Adminer HTTP connection failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Adminer HTTP error: {e}")
        return False


def main():
    """Main validation function"""
    print("🚀 VK Comments Monitor - Simple Database Connectivity Test")
    print("=" * 65)
    print(f"⏰ Started at: {datetime.now()}")
    print()

    # Test connections
    postgres_ok = test_postgresql_socket()
    redis_ok = test_redis_socket()
    adminer_ok = test_adminer_http()

    print()
    print("📊 CONNECTIVITY RESULTS:")
    print("=" * 35)
    print(f"PostgreSQL:  {'✅ CONNECTED' if postgres_ok else '❌ FAILED'}")
    print(f"Redis:       {'✅ CONNECTED' if redis_ok else '❌ FAILED'}")
    print(f"Adminer:     {'✅ CONNECTED' if adminer_ok else '❌ FAILED'}")
    print()

    if postgres_ok and redis_ok and adminer_ok:
        print("🎉 ALL CONNECTIVITY TESTS PASSED!")
        print("📋 Database infrastructure is ready for VK Monitor")
        print()
        print("🔧 Next Steps:")
        print("  1. Install Python dependencies: asyncpg, redis, vkbottle")
        print("  2. Create FastAPI Hello World application")
        print("  3. Test VK API integration")
        print("  4. Begin Foundation Phase implementation")
        return 0
    else:
        print("⚠️  Some connectivity tests failed.")
        print("💡 Ensure Docker containers are running:")
        print("    docker-compose -f docker-compose.dev.yml up -d")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        exit(1)
