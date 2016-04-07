import unittest
from unittest import mock
import pkg_resources
import os
from urllib.error import HTTPError
from son.package.package import Packager, load_local_schema, load_remote_schema
from unittest.mock import patch


class PDTester(unittest.TestCase):

    __pfd__ = {
        'name': 'sonata-project-sample',
        'group': 'com.sonata.project',
        'version': '0.0.1',
        'maintainer': 'Name, Company, Contact',
        'description': 'Project description',
        'catalogues': ['personal'],
        'publish_to': ['personal']
    }

    def __init__(self, *args, **kwargs):
        super(PDTester, self).__init__(*args, **kwargs)
        self.pck = Packager(prj_path='/', generate_pd=False)

    def test_correct_gds(self):
        """ Test the correct general description section """
        print("test_correct_gds")
        gsd = self.pck.package_gds(PDTester.__pfd__)
        self.assertNotEqual(gsd, False)
        print("END test_correct_gds")

    def test_incomplete_gds(self):
        """ Test the returning message when the provided project has incomplete information."""
        print("test_incomplete_gds")
        pfd = PDTester.__pfd__
        pfd.pop('name')
        gsd = self.pck.package_gds(pfd)
        self.assertEqual(gsd, False)
        print("END test_incomplete_gds")


class LoadSchemaTests(unittest.TestCase):

    @patch("son.package.package.yaml")
    @patch("builtins.open")
    @patch("son.package.package.os.path")
    def test_load_local_schema(self, m_os_path, m_open, m_yaml):
        # Ensure that a FileNotFoundError is raised when the file does not exist
        m_os_path.isfile.return_value = False
        self.assertRaises(FileNotFoundError, load_local_schema, "/some/file/path")

        # Ensure a correct schema format and a correct opening of the schema file
        m_os_path.isfile.return_value = True
        m_open.return_value = None
        m_yaml.load.return_value = "not a dict"
        self.assertRaises(AssertionError, load_local_schema, "/some/file/path")
        self.assertEqual(m_open.call_args, mock.call('/some/file/path', 'r'))

        # Ensure that a dictionary is allowed to be returned
        sample_dict = {'dict_key': 'this is a dict'}
        m_os_path.isfile.return_value = True
        m_open.return_value = None
        m_yaml.load.return_value = sample_dict
        return_dict = load_local_schema("/some/file/path")
        self.assertEqual(sample_dict, return_dict)

    @patch("son.package.package.yaml")
    @patch("son.package.package.urllib.request.urlopen.headers.get_content_charset")
    @patch("son.package.package.urllib.request.urlopen.read.decode")
    @patch("son.package.package.urllib.request.urlopen")
    def test_load_remote_schema(self, m_urlopen, m_decode, m_cs, m_yaml):

        sample_dict = {"key": "content"}
        m_decode.return_value = ""
        m_cs.return_value = ""
        m_yaml.load.return_value = sample_dict

        # Ensure that urlopen is accessing the same address of the argument
        load_remote_schema("url")
        self.assertEqual(m_urlopen.call_args, mock.call("url"))

        # Ensure it raises error on loading an invalid schema
        m_yaml.load.return_value = "not a dict"
        self.assertRaises(AssertionError, load_remote_schema, "url")

        # Ensure that a dictionary is allowed to be returned
        m_yaml.load.return_value = sample_dict
        return_dict = load_remote_schema("url")
        self.assertEqual(sample_dict, return_dict)

    def test_load_invalid_local_template(self):
        """Test if the load schema is loading only available templates"""
        print("test_load_invalid_local_template")
        self.assertRaises(FileNotFoundError, load_local_schema, "test")
        print("END test_load_invalid_local_template")

    def test_load_valid_local_schema(self):
        """ Test if the load schema is correctly loading the templates """
        # Access to local stored schemas for this test
        schema_f = pkg_resources.resource_filename(__name__, os.path.join(".son-schema", 'pd-schema.yml'))
        schema = load_local_schema(schema_f)
        self.assertIsInstance(schema, dict)

        schema_f = pkg_resources.resource_filename(__name__, os.path.join(".son-schema", 'nsd-schema.yml'))
        schema = load_local_schema(schema_f)
        self.assertIsInstance(schema, dict)

        schema_f = pkg_resources.resource_filename(__name__, os.path.join(".son-schema", 'vnfd-schema.yml'))
        schema = load_local_schema(schema_f)
        self.assertIsInstance(schema, dict)

    def test_load_invalid_remote_template_unavailable(self):
        """ Test if it raises a HTTP error with a valid but unavailable schema URL """
        self.assertRaises(HTTPError, load_remote_schema, "http://somerandomurl.com/artifact.yml")

    def test_load_invalid_remote_template_invalid(self):
        """ Test if it raises an error with an invalid schema URL """
        self.assertRaises(ValueError, load_remote_schema, "some.incorrect/..url")

    def test_load_valid_remote_schema(self):
        """ Test if the load_remote_schema is retrieving and loading the templates correctly """
        schema = load_remote_schema(Packager.schemas[Packager.SCHEMA_PACKAGE_DESCRIPTOR]['remote'])
        self.assertIsInstance(schema, dict)
