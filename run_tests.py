"""
run_tests.py
=============
Automated test runner executing unit tests across data, analytics, and reporting layers.
Works with standard Python unittest library without third-party test runners.
"""
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tests.test_competitor import test_price_elasticity_simulation, test_store_cpi_metrics_structure
from tests.test_database import test_database_initialization, test_record_sale_and_fetch_logs, test_update_catalog_price
from tests.test_pdf_export import test_chat_transcript_pdf_generation, test_enterprise_pdf_generation
from src.data.db_manager import DatabaseManager

class BoutiqueTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db = DatabaseManager(db_path=self.tmp.name)

    def test_01_elasticity(self):
        test_price_elasticity_simulation()
        
    def test_02_cpi_structure(self):
        test_store_cpi_metrics_structure(self.db)
        
    def test_03_database_initialization(self):
        test_database_initialization(self.db)
        
    def test_04_record_sale(self):
        test_record_sale_and_fetch_logs(self.db)
        
    def test_05_update_catalog_price(self):
        test_update_catalog_price(self.db)
        
    def test_06_chat_transcript_pdf(self):
        test_chat_transcript_pdf_generation()
        
    def test_07_enterprise_pdf(self):
        test_enterprise_pdf_generation(self.db)

if __name__ == '__main__':
    print("=" * 65)
    print("  Local BI Boutique Assistant - Automated Test Suite")
    print("=" * 65)
    suite = unittest.TestLoader().loadTestsFromTestCase(BoutiqueTestCase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n [OK] All 7 automated tests passed successfully!")
        sys.exit(0)
    else:
        print("\n [FAIL] Some tests failed.")
        sys.exit(1)
