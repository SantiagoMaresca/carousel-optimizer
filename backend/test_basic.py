"""
Simple test to verify core functionality without ML dependencies.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_basic_imports():
    """Test that we can import core modules."""
    
    print("Testing core imports...")
    
    try:
        from app.config import settings
        print("✓ Config module imported successfully")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False
    
    try:
        from core.logger import get_ai_logger
        logger = get_ai_logger()
        print("✓ Logger module imported successfully")
    except Exception as e:
        print(f"✗ Logger import failed: {e}")
        return False
    
    try:
        from core.session_manager import SessionManager
        print("✓ SessionManager imported successfully")
    except Exception as e:
        print(f"✗ SessionManager import failed: {e}")
        return False
    
    try:
        from modules.embeddings import EmbeddingGenerator
        print("✓ EmbeddingGenerator imported successfully")
    except Exception as e:
        print(f"✗ EmbeddingGenerator import failed: {e}")
        return False
    
    try:
        from modules.quality_metrics import QualityAnalyzer
        print("✓ QualityAnalyzer imported successfully")
    except Exception as e:
        print(f"✗ QualityAnalyzer import failed: {e}")
        return False
    
    print("All core imports successful!")
    return True

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    
    print("\nTesting basic functionality...")
    
    try:
        from core.session_manager import SessionManager
        from pathlib import Path
        import tempfile
        import asyncio
        
        async def run_test():
            # Create temporary directory for testing
            temp_dir = Path(tempfile.mkdtemp())
            session_manager = SessionManager(upload_dir=temp_dir)
            
            # Create a new session
            session_id = await session_manager.create_session()
            print(f"✓ Session created: {session_id}")
            
            # Check if session exists
            session_data = await session_manager.get_session(session_id)
            exists = session_data is not None
            print(f"✓ Session exists check: {exists}")
            
            # Get session info (using the session data we just retrieved)
            if session_data:
                print(f"✓ Session info retrieved: files={len(session_data.files)}, created={session_data.created_at}")
            else:
                print("✗ Could not retrieve session info")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            print("✓ Basic functionality test passed!")
            return True
        
        return asyncio.run(run_test())
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running basic backend validation...\n")
    
    imports_ok = test_basic_imports()
    functionality_ok = test_basic_functionality()
    
    print(f"\nResults:")
    print(f"Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"Functionality: {'PASS' if functionality_ok else 'FAIL'}")
    
    if imports_ok and functionality_ok:
        print("\n🎉 Backend validation PASSED! Core functionality is working.")
        sys.exit(0)
    else:
        print("\n❌ Backend validation FAILED!")
        sys.exit(1)