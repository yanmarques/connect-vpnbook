"""
This module provide helper functions to manage file operations.
"""

def filesave(name, bin_body):
    """save content into file name"""
    # open a new file in write/binary mode
    # may fuck up if body is not binary
    with open(name, 'wb') as buffer:
        # handle basic iteration
        if type(bin_body) is bytes:
            buffer.write(bin_body)
        else:
            for chunk in bin_body:
                buffer.write(chunk)


def getcontent(filename, default=None):
    """read content from file when any"""
    # open file in read/text mode and get content from file
    # may fuck up when file does not exist
    with open(filename) as reader:
        return reader.read().strip() or default
