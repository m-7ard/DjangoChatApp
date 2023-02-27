def get_object_or_none(obj, **kwargs):
	return obj.objects.filter(**kwargs).first()
