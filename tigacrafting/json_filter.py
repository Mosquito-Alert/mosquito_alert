import operator

def append_chain_query(accum_query, current_clause):
    join_op = None
    if accum_query is None:
        accum_query = current_clause
    else:
        join_op = operator.and_
        accum_query = join_op(accum_query, current_clause)
    return accum_query