def cross_filter(keep, test, fn):
    '''
    given two lists of results keep and test, for each element in keep, run the function against the test list as to filter the keep list
    :param fn with signature fn(item, test_list, context, keep_list, item_index) -> bool, context
        return must be a list or tuple (which is treated as [bool, context]) or a bool by itself
        bool indicates whether the item should be kept or not
        context is an optional object returned by the function, passed to the next function call
    '''
    kept_items = []
    context = None

    for i, item in enumerate(keep):
        result = fn(item, test, context, keep, i)

        if not (type(result) is list or type(result) is tuple or type(result) is bool):
            raise RuntimeError('invalid result type {0}'.format(type(result)))

        if type(result) is not bool:
            context = result[1]
            keep_cur_item = result[0]
        else:
            keep_cur_item = result

        if keep_cur_item:
            kept_items.append(item)
    
    return kept_items