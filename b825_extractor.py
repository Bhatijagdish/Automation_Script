import os
import re
import sys
import time


def validate_seq(codes: list[tuple], seq: list) -> list[list[tuple]]:
    """
    Validating exact expected sequence out of all event codes
    :param codes:
    :param seq:
    :return:
    """
    matching_values = []
    for i in range(len(codes) - len(seq) + 1):
        if [x[1] for x in codes[i: i + len(seq)]] == seq:
            matching_values.append([codes[i + j] for j in range(len(seq))])
    return matching_values


def get_event_code(timestamp_string: str) -> str:
    text_splits = timestamp_string.split(" ")
    return text_splits[len(text_splits) - 1]


class B825_Extractor:
    date_matcher = r"[2][0-9]{3}(.+)0x[a-zA-Z0-9]{4}"

    text_data = []
    final_data = []
    event_codes = []

    def get_event_codes(self):
        for index, line in enumerate(self.text_data):
            match = re.match(self.date_matcher, line)
            if match:
                timestamp_string = line[:39]
                event_code = get_event_code(timestamp_string)
                self.event_codes.append((index, event_code))

    def get_data_chunk(self, codes: list[tuple]):
        end_idx = 0
        for i in range(len(codes)):
            for line in self.text_data[codes[i][0] + 1:]:
                match = re.match(self.date_matcher, line)
                if match:
                    end_idx = self.text_data.index(line)
                    break
                end_idx = self.text_data.index(line) + 1
            yield self.text_data[codes[i][0]:end_idx]

    def get_file_name(self, file_name: str, output_path: str) -> str:
        """
        Function will return the absolute location of the output file.
        """
        file_abs_path: str = os.path.join(output_path, file_name)
        destination_dir: str = os.path.dirname(file_abs_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        return file_abs_path

    def get_valid_events(self):
        seqs = ["0xB825"]
        for seq in validate_seq(self.event_codes, seqs):
            yield seq

    def read_input_file(self, input_path: str, output_path: str) -> None:
        """
        Function will execute the script and create output files
        :param input_path: Absolute location of the directory of input files that needs to be read
        :param output_path: Absolute location of the directory of output files that needs to be updated
        :return: None
        """
        if os.path.exists(input_path):
            for file_name in os.listdir(input_path):
                start_time = time.time()
                # reading each text file from the directory
                if file_name.lower().endswith(".txt"):
                    # joining the input directory with the text file to get absolute location
                    file_abs_path: str = os.path.join(input_path, file_name)
                    with open(file_abs_path) as f:
                        self.text_data: list = f.readlines()

                    # Generating output text file name using input text file name
                    output_file_name: str = file_name[:len(file_name) - 4] + "_output.txt"

                    self.final_data.append(f"Source file: {file_name}\n")
                    self.final_data.append(f"Output File: {output_file_name}\n")

                    # QCAT version needs to be added as specified in the text file once it
                    # is done, it should break the loop and go to the next section
                    for i in range(10):
                        line = self.text_data[i]
                        if "%QCAT VERSION" in line:
                            self.final_data.append(line)
                            break

                    self.final_data.append("TimeTaken\n")

                    start_idx = counter = 0
                    for idx, line in enumerate(self.text_data):
                        match = re.match(self.date_matcher, line)
                        if match and counter == 0:
                            start_idx = idx
                            counter = 1
                        elif match and counter == 1:
                            end_idx = idx
                            res = self.text_data[start_idx:end_idx]
                            start_idx = idx
                            if "0xB825" in res[0] \
                                    and any("Num Contiguous CC Groups" in line for line in res):
                                key, value = [line for line in res if "Num Contiguous CC Groups" in line][0].split("=")
                                key, value = key.strip(), value.strip()
                                if int(value) > 1:
                                    self.final_data.append(res[0])

                    end_time = time.time()
                    self.final_data[3] = f"Execution took approx: {round((end_time - start_time), 3)} seconds \n"
                    # writing all data to new output log file using the list where all the data is collated
                    with open(self.get_file_name(output_file_name, output_path), "w") as file:
                        for line in self.final_data:
                            file.write(line)

                    self.final_data.clear()


if __name__ == '__main__':
    start_time_log = time.time()
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    B825_Extractor().read_input_file(input_file, output_file)
    end_time_log = time.time()
    print(f"Execution took approximately {round(end_time_log - start_time_log, 3)} seconds")
