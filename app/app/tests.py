"""
Sample test.
"""
from django.test import SimpleTestCase

from . import calc


class CalcTest(SimpleTestCase):
    """Test the calc module."""

    def test_add_number(self):
        """Test adding numbers together."""
        res = calc.add(2,2)

        self.assertEqual(res,4)
    
    def test_sub_number(self):
        """Test subtracting number together."""
        res = calc.sub(3,2)

        self.assertEqual(res,1)