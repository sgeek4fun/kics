from math import ceil

def slugify(title):
   return title.lower().replace(' ', '-')

def pagination(count, page, per_page=2):
  page_number = ceil(count / per_page)
  offset = (page - 1) * per_page
  next_page = page + 1
  prev_page = page - 1
  return {
     'per_page': per_page,
     'offset': offset,
     'pages': list(range(1, page_number + 1)),
     'page': page,
     'page_num': page_number,
     'next_page': next_page,
     'prev_page': prev_page
  }