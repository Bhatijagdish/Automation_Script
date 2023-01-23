import os
import re
import sys
import time
from re import Match
from typing import AnyStr

"""
# Approach
1. The tests should be assigned to each event task 
2. we will verify the main event code from which the data needs to be extracted
3. the sequence which verifies that the correct event occured
4. Data that needs to be extracted from each event log
5. Verify if there is any table in the log, then extract the column information 
"""
tests = \
    {
        "Test1":
            {
                "metric": "NR10",
                "main": "0xB97F",
                "seq": ["0xB9BE", "0xB97F", "0xB825"],
                "data":
                    {
                        "0xB9BE": [],
                        "0xB97F": ["ARFCN", "Serving Cell PCI"],
                        "0xB825": ["Band Number"]
                    },
                "table": [False, False, True]
            },
        "Test2":
            {
                "metric": "NR12",
                "main": "0x1FFB",
                "seq": ["0x1FFB"],
                "data":
                    {
                        "0x1FFB": ["Failure Type = RACH_PROBLEM, SCG mode = ENDC"]
                    },
                "table": [False]
            },
        "Test3":
            {
                "metric": "NR12",
                "main": "0x1FFB",
                "seq": ["0x1FFB"],
                "data":
                    {
                        "0x1FFB": ["RRC State = Closing"]
                    },
                "table": [False]
            }
    }

date_matcher = "[2][0-9]{3}"



def get_chunk_data(log_data: list, event_code: str):
    start_index = -1
    end_index = -1
    counter = 0
    for index, line in enumerate(log_data):
        if counter >= 2:
            break
        else:
            if re.search(date_matcher, line):
                if event_code in line and counter == 0:
                    if start_index == -1:
                        start_index = index
                        counter = 1
                        continue
                if counter == 1:
                    end_index = index
                    counter = 2
            else:
                end_index = index
    if start_index != -1:
        return log_data[start_index:end_index]


# def validate_seq(codes: list[tuple], seq: list):
#     matching_indexes = []
#     start = 0
#     while True:
#         start = [x[1] for x in codes].index(seq[0], start)
#         if [x[1] for x in codes][start: start + len(seq)] == seq:
#             matching_indexes.append(list(range(start, start + len(seq))))
#         start += 1
#         if start + len(seq) > len(codes):
#             break
#     return matching_indexes

def validate_seq(codes: list[tuple], seq: list) -> list[list[tuple]]:
    matching_values = []
    for i in range(len(codes) - len(seq) + 1):
        if [x[1] for x in codes[i: i + len(seq)]] == seq:
            matching_values.append([codes[i + j] for j in range(len(seq))])
    return matching_values


# def get_chunk_data_with_index(log_data: list, codes: list[tuple], event_code: str):
#     log_last_idx = len(log_data) - 1
#     last_idx = len(codes) - 1
#     for i in range(len(codes)):
#         if codes[i][1] == event_code:
#             start_index = codes[i][0]
#             if i == last_idx:
#                 end_index = log_last_idx
#             else:
#                 end_index = codes[i + 1][0]
#             yield log_data[start_index:end_index]


def get_chunk_data_with_index(log_data: list, codes: list[list[tuple]]):
    log_data_last_idx = len(log_data) - 1
    end_idx = 0
    for item in codes:
        last_idx = len(item) - 1
        for i in range(len(item)):
            if last_idx == i:
                for line in log_data[item[i][0] + 1:]:
                    match: Match[AnyStr] | None = re.match(date_matcher, line)
                    if match:
                        end_idx = log_data.index(line)
                        break
                    end_idx = log_data_last_idx
                yield log_data[item[i][0]:end_idx]
            else:
                yield log_data[item[i][0]:item[i + 1][0]]


def get_event_code(timestamp_string: str) -> str:
    text_splits = timestamp_string.split(" ")
    return text_splits[len(text_splits) - 1]


def get_event_codes(log_data: list) -> list[tuple]:
    result = []
    for index, line in enumerate(log_data):
        match: Match[AnyStr] | None = re.match(date_matcher, line)
        if match:
            timestamp_string = line[:39]
            event_code = get_event_code(timestamp_string)
            result.append((index, event_code))
    return result


# need to create the same function with list argument
def get_rows(chunk_data: str) -> list | None:
    pattern = re.compile(r"\s*--+\n(.+)\n\s*--+\n(.+)\|\n\n", re.DOTALL)
    data = pattern.search(chunk_data)
    result = []
    counter = 0
    if data:
        rows_data = data.group().split("\n")[:-1]
        while rows_data:
            if rows_data[0].strip().startswith("----"):
                counter += 1
            if counter != 2:
                rows_data.pop(0)
            if counter == 2:
                if rows_data[0].strip().endswith("|") and rows_data[0].strip().startswith("|"):
                    result.append([item.strip() for item in rows_data[0].strip().split("|") if item])
                    counter = 0
                else:
                    rows_data.pop(0)
    return result


# def get_rows(chunk: list) -> list | None:
#     result = []
#     counter = 0
#     chunk_data = chunk
#     while chunk_data:
#         if chunk_data[0].strip().startswith("----"):
#             counter += 1
#         if counter != 2:
#             chunk_data.pop(0)
#         if counter == 2:
#             if chunk_data[0].strip().endswith("|") and chunk_data[0].strip().startswith("|"):
#                 result.append([item.strip() for item in chunk_data[0].strip().split("|") if item])
#                 counter = 0
#             else:
#                 chunk_data.pop(0)
#     return result


def get_headers(chunk_data: str) -> list | None:
    pattern = re.compile(r"\s*--+\n(.+)\n\s*--+\n", re.DOTALL)
    data = pattern.search(chunk_data)
    header_list = []
    if data:
        rows_data = data.group().split("\n")[:-1]
        while rows_data:
            rows = []
            counter = 0
            while counter < 2:
                rows.append(rows_data[0].strip())
                if "---" in rows_data[0].strip():
                    counter += 1
                if counter == 0:
                    rows.clear()
                rows_data.pop(0)
            original_list = [row.split("|")[1:-1] for row in rows[1:-1]]
            max_count = max([len(item) for item in original_list])
            original_list = [item for item in original_list if len(item) == max_count]
            headers = [" ".join(map(str.strip, item)).strip() for item in zip(*original_list)]
            header_list.append(headers)
            rows.clear()
        return header_list


def get_file_name(file_name: str, output_path: str) -> str:
    """
    Function will return the absolute location of the output file.
    """
    file_abs_path: str = os.path.join(output_path, file_name)
    destination_dir: str = os.path.dirname(file_abs_path)
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    return file_abs_path


# def get_seq_chunks(log_data):
#     counter = 0
#     seq_chunks = []
#     for key in NR_10:
#         if NR_10[key]:
#             print(get_chunk(log_data, key))

# for key in NR_10:
#     if key == event_code:
#         counter += 1
#     else:
#         break

# for i in range(len(log_data)):
#     match: Match[AnyStr] | None = re.match(date_matcher, log_data[i])
#     if match:
#         timestamp_string = log_data[i][:39]
#         event_code = get_event_code(timestamp_string)
#         for key in NR_10:
#             if key == event_code and NR_10[key]:
#                 print(get_chunk(log_data, NR_10[key]))
#                 seq_chunks.append(get_chunk(log_data, NR_10[key]))
#                 print(seq_chunks)
#                 counter += 1
#             else:
#                 break
# return seq_chunks

def check_prev_event(output_file_lines: list, event_code: str):
    result = False
    idx = len(output_file_lines) - 1
    while not result:
        if re.match(date_matcher, output_file_lines[idx]):
            break
        if idx < 1:
            break
        if event_code in output_file_lines[idx]:
            result = True
            break
        idx -= 1
    return result


def read_input_file(input_path: str, output_path: str) -> None:
    """
    Function will execute the script and create output files
    :param input_path: Absolute location of the directory of input files that needs to be read
    :param output_path: Absolute location of the directory of output files that needs to be updated
    :return: None
    """
    for file_name in os.listdir(input_path):
        # reading each text file from the directory
        if file_name.lower().endswith(".txt"):
            # joining the input directory with the text file to get absolute location
            file_abs_path: str = os.path.join(input_path, file_name)
            with open(file_abs_path) as f:
                lines: list = f.readlines()

                # Generating output text file name using input text file name
                output_file_name: str = file_name[:len(file_name) - 4] + "_output.txt"

                # QCAT version needs to be added as specified in the text file once it
                # is done, it should break the loop and go to the next section
                file_data = []
                for line in lines:
                    if "%QCAT VERSION" in line:
                        file_data.append(line)
                        break

                # iterate over the given data in dictionary to get the expected information
                for test in tests:
                    # Get a list of tuples that contains index of line with timestamp
                    # and event_code associated with it
                    event_codes = get_event_codes(lines)
                    # will get list of list that contains tuples and
                    # the event codes in tuples matches the sequence specified in the given data
                    # these tuples will help us to get the chunk of data specific to that event code only
                    seq_codes = validate_seq(event_codes, tests[test]['seq'])
                    # extracting each chunk of the data that start from the
                    # timestamp line and end before next timestamp line.
                    for chunk in get_chunk_data_with_index(lines, seq_codes):

                        # convert list into string to read it as chunk and extract table info.
                        chunk_str = "".join(chunk)
                        columns = get_headers(chunk_str)
                        rows = get_rows(chunk_str)
                        # convert table info into dictionary
                        dict_data = {}
                        counter = 0

                        for idx, key in enumerate(tests[test]['data']):
                            if columns and tests[test]['table'][idx]:
                                final_row = [item for row in rows for item in row]
                                final_column = [item for col in columns for item in col]
                                dict_data = dict(zip(final_column, final_row))
                            if tests[test]['data'][key]:
                                if chunk and key in chunk[0]:
                                    for line in chunk:
                                        if tests[test]['metric'] == "NR12" and \
                                                check_prev_event(file_data, "NR10"):
                                            for find_text in tests[test]['data'][key]:
                                                if find_text in line:
                                                    if counter == 0 and tests[test]["main"] == key:
                                                        file_data.append(chunk[0][:39] + "\n")
                                                        file_data.append(f"Metric: {tests[test]['metric']}\n")
                                                        counter = 1
                                                    file_data.append(line)
                                                if dict_data:
                                                    if find_text in dict_data:
                                                        file_data.append(f"{find_text}: {dict_data[find_text]}\n")
                                                        dict_data.pop(find_text)
                                        elif tests[test]['metric'] == "NR10":
                                            for find_text in tests[test]['data'][key]:
                                                if find_text in line:
                                                    if counter == 0 and tests[test]["main"] == key:
                                                        file_data.append(chunk[0][:39] + "\n")
                                                        file_data.append(f"Metric: {tests[test]['metric']}\n")
                                                        counter = 1
                                                    file_data.append(line)
                                                if dict_data:
                                                    if find_text in dict_data:
                                                        file_data.append(f"{find_text}: {dict_data[find_text]}\n")
                                                        dict_data.pop(find_text)

            with open(get_file_name(output_file_name, output_path), "w") as file:
                file.write(f"Source file: {file_name}\n")
                file.write(f"Output File: {output_file_name}\n")

                for line in file_data:
                    file.write(line)


if __name__ == '__main__':
    start_time = time.time()
    # input_txt_files_dir = sys.argv[1]
    # output_txt_files_dir = sys.argv[2]
    input_txt_files_dir = "./phase3/14_2_AfterPatch_12-14.12-41-56-910/"
    output_txt_files_dir = "./phase3/output/"
    read_input_file(input_txt_files_dir, output_txt_files_dir)
    end_time = time.time()
    print(f"Execution took approximately {round(end_time - start_time, 2)} seconds")
