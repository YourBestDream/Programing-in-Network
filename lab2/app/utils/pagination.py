def paginate(query, offset=0, limit=5):
    return query.offset(offset).limit(limit).all()
