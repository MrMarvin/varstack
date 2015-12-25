from nose.tools import *
import logging
from testfixtures import log_capture
import os, sys, shutil

from varstack import Varstack

class TestVarstack(object):

    def test_init(self):
        v = Varstack()
        assert_is_not_none(v.config_filename)
        v = Varstack("/etc/some/other_file.yaml")
        assert_equal(v.config_filename, "/etc/some/other_file.yaml")

    def test_evaluate_uses_default_datadir(self):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_no_datadir.yaml")
        assert_not_equal({}, v.evaluate({}))

    @log_capture(level=logging.INFO)
    def test_evaluate_with_non_existing_datadir_fails_and_returns_empty(self, log):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack.yaml")
        assert_equal({}, v.evaluate({}))
        assert_in('not found, skipping', str(log))

    def test_evaluate_merges_and_replaces(self):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_no_datadir.yaml", {})
        evaluated = v.evaluate({})
        assert_equal(3, len(evaluated['an_array']))
        assert_equal(2, len(evaluated['a_dict']))
        assert_equal("another_string", v.evaluate({})['a_dict']['key1'])


class TestVarstackWithCrypto(object):
    @classmethod
    def setup_class(klass):
        import gnupg
        if os.path.isdir(os.path.dirname(__file__)+'/helper/gnupghome/'):
          shutil.rmtree(os.path.dirname(__file__)+'/helper/gnupghome/')
        os.makedirs(os.path.dirname(__file__)+'/helper/gnupghome/')
        gpg = gnupg.GPG(gnupghome=os.path.dirname(__file__)+'/helper/gnupghome/')
        gpg.import_keys(open(os.path.dirname(__file__)+'/helper/public_shared_varstack_testrunner_key_pair.asc').read())

    @classmethod
    def teardown_class(klass):
        shutil.rmtree(os.path.dirname(__file__)+'/helper/gnupghome/')

    def setUp(self):
        self.v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_crypted.yaml",
                          {'gnupghome': os.path.dirname(__file__)+'/helper/gnupghome/'})
        self.evaluated = self.v.evaluate({})

    def test_evaluate_with_encrypted_string(self):
        assert_equal(self.evaluated['unencrypted_string'], self.evaluated['encrypted_string'])
        assert_is_instance(self.evaluated['encrypted_string'], str)

    def test_evaluate_with_encrypted_multiline_string(self):
        assert_equal(self.evaluated['unencrypted_multiline_string'], self.evaluated['encrypted_multiline_string'])
        assert_is_instance(self.evaluated['encrypted_multiline_string'], str)

    def test_evaluate_with_encrypted_list(self):
        assert_equal(self.evaluated['unencrypted_yaml_list'], self.evaluated['encrypted_yaml_list'])
        assert_is_instance(self.evaluated['encrypted_yaml_list'], list)

    def test_evaluate_with_nested_encrytion(self):
        assert_is_instance(self.evaluated['nested_encrytion'], dict)
        assert_is_instance(self.evaluated['nested_encrytion']['encrypted_hash'], dict)

        assert_is_instance(self.evaluated['nested_encrytion']['encrypted_hash']['foo'], str)
        assert_equal("42", self.evaluated['nested_encrytion']['encrypted_hash']['foo'])

        assert_is_instance(self.evaluated['nested_encrytion']['encrypted_hash']['baz'], int)
        assert_equal(42, self.evaluated['nested_encrytion']['encrypted_hash']['baz'])

    @log_capture(level=logging.ERROR)
    def test_evaluate_cant_decrypt(self, log):
        logged_evaluated = self.v.evaluate({})
        assert_is_instance(logged_evaluated['secret_that_was_encrypted_with_another_key'], str)
        assert_in('BEGIN PGP MESSAGE', logged_evaluated['secret_that_was_encrypted_with_another_key'])
        assert_in('could not decrypt string', str(log))

class TestVarstackVariableExtractor(object):
    @log_capture(level=logging.DEBUG)
    def test_can_load_py_files_from_working_dir(self, log):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_with_extractors.yaml")
        v.evaluate({})
        assert_in('successfully loaded "extract_from_id"', str(log))
        assert_in('extract_from_id', v.config['extractor_functions'])

    @log_capture(level=logging.ERROR)
    def test_can_load_py_files_with_absolute_path(self, log):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_with_extractors.yaml")
        v.evaluate({})
        assert_in('Could not load extractor function from', str(log))
        assert_not_in('absolute_path_extractor', v.config['extractor_functions'])

    @log_capture(level=logging.DEBUG)
    def test_extractor_function_is_called(self, log):
        v = Varstack(os.path.dirname(__file__)+"/../examples/varstack_with_extractors.yaml", {})
        evaluated = v.evaluate({'id': 'some1-extractortest1.varstack.example.com'})
        assert_equal(evaluated['my_tld'], 'com')

        evaluated = v.evaluate({'id': 'some1-extractortest1.varstack.example.net'})
        assert_in('tld/net.yaml" not found', str(log))
