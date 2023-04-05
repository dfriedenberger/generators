
def remove_duplicates(input_list):
    output_list = []
    for e in input_list:
        if e not in output_list:
            output_list.append(e)
    return output_list