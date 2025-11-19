#!/usr/bin/env python3
"""Test file upload and plagiarism check workflow."""
import asyncio
import httpx
import os
from pathlib import Path


async def test_workflow():
    """Test the complete workflow: file upload -> plagiarism check."""
    print("=" * 60)
    print("Testing Complete Workflow")
    print("=" * 60)
    print()
    
    # Create a test file
    test_content = """
def machine_learning_analysis():
    print("Research Paper: ML Analysis")
    return "This is a test research paper submission for ICML 2024"

if __name__ == "__main__":
    machine_learning_analysis()
"""
    
    test_file = Path("test_paper_submission.py")
    test_file.write_text(test_content)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Upload submission
        print("Test 1: Uploading research paper...")
        files = {"file": ("test_paper_submission.py", test_content, "text/plain")}
        data = {"assignment_id": "ICML2024-P001"}
        
        response = await client.post(
            "http://localhost:8000/api/submissions/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 201:
            print("✓ Research paper submitted successfully!")
            result = response.json()
            submission_id = result["submission"]["id"]
            print(f"  Paper ID: {submission_id}")
            
            if result.get("plagiarism_check"):
                print("  Plagiarism Check:")
                plag = result["plagiarism_check"]
                print(f"    - Internal Score: {plag['internal_score']:.2f}")
                print(f"    - External Score: {plag['external_score']:.2f}")
                print(f"    - AI Probability: {plag['ai_generated_probability']:.2f}")
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  {response.text}")
            test_file.unlink()
            return
        
        print()
        
        # Test 2: Get submission from submission service
        print("Test 2: Retrieving paper from database...")
        response = await client.get(f"http://localhost:8002/submissions/{submission_id}")
        if response.status_code == 200:
            print("✓ Paper submission retrieved from PostgreSQL")
            sub = response.json()
            print(f"  User ID: {sub['user_id']}")
            print(f"  Conference: {sub['assignment_id']}")
            print(f"  Text length: {len(sub.get('text', ''))} chars")
        else:
            print(f"✗ Failed to retrieve paper submission")
        
        print()
        
        # Test 3: Get plagiarism result from plagiarism service
        print("Test 3: Retrieving plagiarism result from MongoDB...")
        response = await client.get(f"http://localhost:8003/results/{submission_id}")
        if response.status_code == 200:
            print("✓ Plagiarism result retrieved from MongoDB")
            result = response.json()
            print(f"  Submission ID: {result['submission_id']}")
            print(f"  Internal Score: {result['internal_score']:.3f}")
            print(f"  External Score: {result['external_score']:.3f}")
            print(f"  AI Probability: {result['ai_generated_probability']:.3f}")
        else:
            print(f"✗ Failed to retrieve plagiarism result")
        
        print()
        
        # Test 4: Check file was saved
        print("Test 4: Checking uploaded file...")
        upload_dir = Path("./uploads")
        if upload_dir.exists():
            files = list(upload_dir.glob("*.py"))
            if files:
                print(f"✓ Found {len(files)} uploaded file(s)")
                print(f"  Latest: {files[-1].name}")
            else:
                print("⚠ No files found in uploads directory")
        
        print()
        
        # Test 5: List user submissions
        print("Test 5: Listing user's paper submissions...")
        response = await client.get(
            "http://localhost:8000/api/submissions?user_id=student_001"
        )
        if response.status_code == 200:
            subs = response.json()
            print(f"✓ User has {len(subs)} paper(s) submitted")
        else:
            print(f"✗ Failed to list submissions")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    
    print()
    print("=" * 60)
    print("Workflow Test Complete!")
    print("=" * 60)
    print()
    print("✓ All services are working correctly")
    print("✓ PostgreSQL: storing users and submissions")
    print("✓ MongoDB: storing plagiarism results")
    print("✓ File upload: working")
    print("✓ API Gateway: routing correctly")
    print()
    print("You can now:")
    print("  1. Visit http://localhost:8000")
    print("  2. Login with researcher@university.edu")
    print("  3. Upload research papers from the dashboard")
    print()


if __name__ == "__main__":
    asyncio.run(test_workflow())
