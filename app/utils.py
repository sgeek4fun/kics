def form_errors(*args):
  errors = {}
  for field in args:
     errors[field] = None
  errors['blank'] = 'This field must not be blank'
  return errors

def validate(errors, *args):
  names = list(errors.keys())
  def check(tup):
    index, field = tup
    if not field:
      errors[names[index]] = errors['blank']
    return field
  list(map(check, enumerate(args)))
  return errors