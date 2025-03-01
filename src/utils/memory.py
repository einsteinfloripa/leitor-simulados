class cache_readonly_property:
    """
    A decorator-based descriptor for creating cached read-only properties.

    This class allows for the caching of computed properties in an instance's 
    dictionary upon first access, preventing redundant calculations. The property 
    is read-only, and attempts to modify it will raise an AttributeError.

    Attributes
    ----------
    func : function
        The function used to compute the property's value.
    name : str
        The name of the property.

    Methods
    -------
    __get__(instance, owner)
        Retrieves the cached value of the property, computing and storing it if necessary.
    __set__(instance, value)
        Raises an AttributeError since the property is read-only.
    invalidate(instance)
        Removes the cached value from the instance's dictionary.
    """

    def __init__(self, func):
        """
        Initializes the descriptor with the provided function.

        Parameters
        ----------
        func : function
            The function used to compute the property's value.
        """
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        """
        Retrieves the cached property value, computing and storing it if necessary.

        Parameters
        ----------
        instance : object
            The instance on which the property is accessed.
        owner : type
            The class of the instance.

        Returns
        -------
        Any
            The computed and cached property value.
        """
        if instance is None:
            return self
        value = self.func(instance)
        instance.__dict__[self.name] = value

        # Update the tracking list in the instance
        if not hasattr(instance, "_cached_properties"):
            instance._cached_properties = [self]
        else:
            instance._cached_properties.append(self)

        return value

    def __set__(self, instance, value):
        """
        Prevents modification of the cached property.

        Parameters
        ----------
        instance : object
            The instance on which the property is accessed.
        value : Any
            The value being assigned.

        Raises
        ------
        AttributeError
            If an attempt is made to modify the property.
        """
        raise AttributeError(f"{self.name} is a read-only property")

    def invalidate(self, instance):
        """
        Deletes the cached property value from the instance.

        Parameters
        ----------
        instance : object
            The instance whose cached property should be invalidated.
        """
        del instance.__dict__[self.name]