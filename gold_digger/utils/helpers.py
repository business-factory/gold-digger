# -*- coding: utf-8 -*-


def batches(iterable, batch_size):
    """
    :type iterable: collections.abc.Iterable
    :type batch_size: int
    :rtype: types.GeneratorType[list]
    """
    bucket = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) == batch_size:
            yield bucket
            bucket = []

    if bucket:
        yield bucket
