_file_data = {}

def file_text(name):
    if name not in _file_data:
        _file_data[name] = open('testdata/%s' % name).read()
    return _file_data[name]
