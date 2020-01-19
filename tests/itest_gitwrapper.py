from batchnfpm.gitwrapper import GitWrapper
import shutil
import os
import unittest

LOCAL_REPO_PATH = '/tmp/batch-nfpm-test'


class Test_TestPackageBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree(LOCAL_REPO_PATH, ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(LOCAL_REPO_PATH, ignore_errors=True)

    def test_get_checkout_clone(self):
        repo = "https://gitlab.com/soerenschneider/batch-nfpm.git"
        self.assertFalse(os.path.isdir(LOCAL_REPO_PATH))
        # clone
        GitWrapper.checkout(repo, LOCAL_REPO_PATH)
        self.assertTrue(os.path.isdir(LOCAL_REPO_PATH))

        # pull
        GitWrapper.checkout(repo, LOCAL_REPO_PATH)
        self.assertTrue(os.path.isdir(LOCAL_REPO_PATH))
