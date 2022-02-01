import pytest
import json
import os

@pytest.mark.django_db
class TestGCMD:
    @staticmethod
    def open_json_file(filepath):
        return json.load(open(filepath, 'r'))

    @pytest.mark.parametrize("input_file,output_file", [("convert_record_input1.json", "convert_record_output1.json")])
    def test_convert_record(self, input_file, output_file):
        test_file_directory = "files/"

        assert self.open_json_file(os.path.join(test_file_directory, input_file)) == self.open_json_file(os.path.join(test_file_directory, output_file))

    # Python unittest runner version of test above.
    # def test_convert_record(self):
    #     test_file_directory = "files/"
    #     inputs = ["convert_record_input1.json"]
    #     outputs = ["convert_record_output1.json"]

    #     for input, output in zip(inputs, outputs):
    #         assert self.open_json_file(os.path.join(test_file_directory, input)) == self.open_json_file(os.path.join(test_file_directory, output))