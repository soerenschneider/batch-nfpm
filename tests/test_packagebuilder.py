from batchnfpm.rpmbuilder import PackageBuilder

import unittest

class Test_TestPackageBuilder(unittest.TestCase):
    def test_get_normalized_version(self):
        version = "2.4.1"
        normalized = PackageBuilder._get_normalized_version(f"v{version}")
        self.assertEqual(normalized, version)
    
    def test_get_normalized_version_identical(self):
        version = "2.4.1"
        normalized = PackageBuilder._get_normalized_version(version)
        self.assertEqual(normalized, version)

    def test_is_git_tag_newer_neg(self):
        git = "2.4.1"
        package = "2.4.1"
        is_git_newer = PackageBuilder._is_git_tag_newer(git, package)
        self.assertFalse(is_git_newer)

    def test_is_git_tag_newer_pos(self):
        git = "2.4.2"
        package = "2.4.1"
        is_git_newer = PackageBuilder._is_git_tag_newer(git, package)
        self.assertTrue(is_git_newer)
    
    def test_is_git_tag_newer_empty_package(self):
        git = "2.4.2"
        package = None
        is_git_newer = PackageBuilder._is_git_tag_newer(git, package)
        self.assertTrue(is_git_newer)

    def test_get_target_filename_no_version(self):
        project = "prometheus"
        name = PackageBuilder._get_target_filename(project, "rpm")
        self.assertEqual(name, "prometheus.rpm")

    def test_get_target_filename_version(self):
        project = "prometheus"
        version = "2.5.1-rc4"
        package_type = "rpm"
        name = PackageBuilder._get_target_filename(project, package_type)
        self.assertEqual("prometheus-2.5.1-rc4.rpm", f"{project}-{version}.{package_type}")
