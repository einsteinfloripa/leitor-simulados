
class cache_readonly_property:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.func(instance)
        instance.__dict__[self.name] = value
        # Update the tracking list in the instance
        if not hasattr(instance, "_cached_properties"):
            instance._cached_properties = [self.name]
        else:
            instance._cached_properties.append(self.name)
        return value
    
    def __set__(self, instance, value):
        raise AttributeError(f"{self.name} is a read-only property")
    
    def invalidate(self, instance):
        """Delete the cached value."""
        if self.name in instance.__dict__:
            del instance.__dict__[self.name]