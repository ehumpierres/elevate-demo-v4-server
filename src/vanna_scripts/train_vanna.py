#!/usr/bin/env python3
"""
Standalone training script for Vanna.AI + Snowflake integration.

This script initializes VannaSnowflake and runs the complete training process.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vanna_scripts.vanna_snowflake import VannaSnowflake

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main training function."""
    try:
        logger.info("🚀 Starting Vanna.AI training process...")
        
        # Initialize VannaSnowflake
        logger.info("📊 Initializing VannaSnowflake...")
        vanna = VannaSnowflake()
        
        # Test connection first
        logger.info("🔗 Testing Snowflake connection...")
        connection_test = vanna.test_connection(detailed=True)
        
        if not connection_test.get("success", False):
            logger.error(f"❌ Connection test failed: {connection_test.get('error', 'Unknown error')}")
            return False
        
        logger.info(f"✅ Connected to {connection_test['database']}.{connection_test['schema']}")
        logger.info(f"📈 Found {connection_test.get('table_count', 0)} tables")
        
        # Run training
        logger.info("🎓 Starting training process...")
        training_result = vanna.train()
        
        if training_result:
            logger.info("✅ Training completed successfully!")
            
            # Display training data statistics
            logger.info("📊 Getting training data statistics...")
            try:
                from src.vanna_scripts.show_training_data import TrainingDataViewer
                viewer = TrainingDataViewer()
                stats = viewer.get_stats()
                
                logger.info("📈 Training Data Summary:")
                logger.info(f"  • Total entries: {stats['total_entries']}")
                logger.info(f"  • DDL statements: {stats['ddl_count']}")
                logger.info(f"  • Documentation entries: {stats['documentation_count']}")
                logger.info(f"  • SQL examples: {stats['sql_count']}")
                logger.info(f"  • Q&A pairs: {stats['qa_pairs_count']}")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not get training statistics: {e}")
        else:
            logger.error("❌ Training failed!")
            return False
            
        # Close connections
        vanna.close()
        logger.info("🔚 Training process completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Training process failed: {e}")
        logger.debug("Training exception details:", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code) 