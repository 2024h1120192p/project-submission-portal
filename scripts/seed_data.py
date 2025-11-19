#!/usr/bin/env python3
"""Seed script to initialize demo users and data."""
import asyncio
import httpx
from datetime import datetime, timezone


BASE_URL = "http://localhost:8001"  # Users service


async def create_user(client, user_data):
    """Create a user via API."""
    try:
        response = await client.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 201:
            print(f"✓ Created user: {user_data['email']}")
            return response.json()
        else:
            print(f"✗ Failed to create {user_data['email']}: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error creating {user_data['email']}: {e}")
        return None


async def main():
    """Seed demo users."""
    print("=" * 60)
    print("Seeding Demo Data")
    print("=" * 60)
    print()
    
    # Demo users
    users = [
        {
            "id": "student_001",
            "name": "Alice Researcher",
            "email": "researcher@university.edu",
            "role": "student"
        },
        {
            "id": "student_002",
            "name": "Bob Researcher",
            "email": "bob.researcher@university.edu",
            "role": "student"
        },
        {
            "id": "student_003",
            "name": "Carol Researcher",
            "email": "carol.researcher@university.edu",
            "role": "student"
        },
        {
            "id": "faculty_001",
            "name": "Dr. Jane Reviewer",
            "email": "reviewer@university.edu",
            "role": "faculty"
        },
        {
            "id": "faculty_002",
            "name": "Prof. John Editor",
            "email": "prof.editor@university.edu",
            "role": "faculty"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        # Check if users service is running
        try:
            response = await client.get(f"{BASE_URL}/users")
            print(f"✓ Users service is running")
            print(f"  Current users: {len(response.json())}")
            print()
        except Exception as e:
            print(f"✗ Users service is not running: {e}")
            print("  Please start services first: ./run_all_services.sh")
            return
        
        # Create users
        print("Creating demo users...")
        print()
        for user in users:
            await create_user(client, user)
        
        print()
        print("=" * 60)
        print("Demo Data Seeded Successfully!")
        print("=" * 60)
        print()
        print("You can now:")
        print("  1. Visit http://localhost:8000")
        print("  2. Click 'Login to Dashboard'")
        print("  3. Use any of these emails:")
        print()
        for user in users:
            print(f"     - {user['email']} ({user['role']})")
        print()
        print("  4. Upload a research paper from researcher dashboard")
        print()


if __name__ == "__main__":
    asyncio.run(main())
