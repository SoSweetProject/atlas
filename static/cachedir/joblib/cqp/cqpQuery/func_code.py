# first line: 41
def cqpQuery(param_list) :
    try :
        pool = Pool(processes=None, initializer=cqpStart)
        query_result = pool.starmap(f, param_list, chunksize=1)
    finally:
        pool.close()
        pool.join()

    return query_result
