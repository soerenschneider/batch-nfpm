from batchnfpm.resources import ResourceReader

import unittest

class Test_TestResourceReader(unittest.TestCase):
    def test_read(self):
        r = ResourceReader.read_from_file("bla")
        print(r)