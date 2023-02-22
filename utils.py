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


def squence_match(validate_seqs):
    if len(validate_seqs) > 0:
        return True


def get_chunk(event_codes, text_data, seq):
    if len(event_codes) - 1 == event_codes.index(seq[0]):
        next_index = len(event_codes)
    else:
        next_index = event_codes[event_codes.index(seq[0]) + 1][0]
    return text_data[seq[0][0]:next_index]


def time_diff(line):
    res = line.split(":", 3)
    return float(res[1]) * 60 + float(res[2][:7])
