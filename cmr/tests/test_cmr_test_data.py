# to run this test file, use 'pytest -k cmr'
import json

from cmr.tests.generate_cmr_test_data import generate_cmr_response


class TestCMRTestData:
    def test_cmr_consistency(self):
        """in order to test the actual functions and not CMR itself, most of these tests rely on a
        hardcopy of the CMR api response. however, if cmr ever experiences a change, we also want
        to be alerted, as that could impact the application. this test compares our hard copy with
        cmr's present output"""

        saved_cmr_response = json.load(open('cmr/tests/cmr_response-ASCENDS.json', 'r'))
        generated_cmr_response = generate_cmr_response('ASCENDS Airborne')
        assert saved_cmr_response == generated_cmr_response
        assert False
