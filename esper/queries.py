import inspect

QUERIES = []


def register_query(name):
    global QUERIES

    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    filename = module.__file__

    def wrapper(f):
        lines = inspect.getsource(f).split('\n')
        lines = lines[:-1]  # Seems to include a trailing newline

        # Hacky way to get just the function body
        i = 0
        while True:
            if "():" in lines[i]:
                break
            i = i + 1

        fn = lines[i:]
        fn += ['FN = ' + f.__name__]
        QUERIES.append([name, '\n'.join(fn)])

        return f

    return wrapper
