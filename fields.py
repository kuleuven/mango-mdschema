class Field:
    
    def __init__(self, name: str, content: dict):
        """Class representing a field of a metadata schema.

        Args:
            name (str): Name of the field, without flattening.
            content (dict): The contents of the JSON object the field comes from.
        
        Attributes:
            name (str): The name of the field.
            type (str): The type of the field, defined within the subclass.
            required (bool): Whether the field is required.
            default (any, optional): The default value for the field, if it is required.
            repeatable (bool): Whether the field is repeatable.
            flattened_name (str): The flattened name of the field, for the AVU.

        Raises:
            KeyError: When the contents don't include a type.
        """
        self.name = name
        
        if not 'type' in content:
            raise KeyError("A field must have a type.")
        
        self.required = 'required' in content and content['required']
        self.default = content['default'] if 'default' in content else None            
        self.repeatable = 'repeatable' in content and content['repeatable']
            
    def flatten_name(self, prefix: str):
        """Flatten the name for the AVU.

        Args:
            prefix (str): Prefix to add to the name of the field.
        """
        self.flattened_name = f"{prefix}.{self.name}"
        
            
    @staticmethod
    def choose_class(name: str, content: dict):
        """Identify the type of field.

        Args:
            name (str): Name of the field, to initiate it.
            content (dict): Contents of the JSON the field comes from.

        Raises:
            KeyError: When the JSON does not include a 'type' key.
            ValueError: When the value of the 'type' is not supported.

        Returns:
            Field: A representation of the field itself.
        """
        if not 'type' in content:
            raise KeyError('A field should have a type.')
        elif content['type'] == 'object':
            return CompositeField(name, content)
        elif content['type'] == 'select':
            return MultipleField(name, content)
        elif content['type'] in SimpleField.text_options:
            return SimpleField(name, content)
        else:
            raise ValueError("The type of the field is not valid.")        
        

class SimpleField(Field):
    text_options = [
        "text", "textarea", "email", "url",
        "date", "time", "datetime-local",
        "integer", "float",
        "checkbox"]
    
    def __init__(self, name: str, content: dict):
        """Class representing a simple field.

        Args:
            name (str): Name of the field.
            content (dict): Contents of the JSON that the field comes from.
        
        Attributes:
            minimum (int or float, default): If `self.type` is 'integer' or 'float',
                the minimum possible value.
            maximum (int or float, default): If `self.type` is 'integer' or 'float',
                the maximum possible value.

        Raises:
            ValueError: When the type of the field is not valid.
        """
        super().__init__(name, content)
        
        if content['type'] not in SimpleField.text_options:
            raise ValueError("The type of the field is not valid.")
        else:
            self.type = content['type']
        
        if self.type in ['integer', 'float']:
            if 'minimum' in content:
                self.minimum = content['minimum']
            if 'maximum' in content:
                self.maximum = content['maximum']    

class CompositeField(Field):
    
    def __init__(self, name: str, content: dict):
        """Class representing a composite field.

        Args:
            name (str): Name of the field.
            content (dict): Contents of the JSON the field comes from.
            
        Attributes:
            fields (dict of Field): Collection of subfields.

        Raises:
            ValueError: When the 'type' attribute of `content` is not 'object'.
            KeyError: When the 'properties' attribute is missing from `content`.
            TypeError: When the 'properties' attribute of `content` is not a dictionary.
        """
        super().__init__(name, content)
        
        if content['type'] != 'object':
            raise ValueError("The type of the field must be 'object'.")
        else:
            self.type = content['type']
        
        if not 'properties' in content:
            raise KeyError("A composite field requires a 'properties' attribute.")
        elif type(content['properties']) != dict:
            raise TypeError("The 'properties' attribute of a composite field must be a dictionary.")
        else:
            self.fields = {k:Field.choose_class(k, v) for k, v in content['properties'].items()}
            
        def flatten_name(self, prefix: str):
            """Flatten the name for the AVUs of the subfields.

            Args:
                prefix (str): Prefix to add to the name of the field.
            """
            super().flatten_name(prefix)
            for subfield in self.fields.values():
                subfield.flatten_name(self.flattened_name)
    

class MultipleField(Field):
    
    def __init__(self, name: str, content: dict):
        """A class representing a multiple-choice field.

        Args:
            name (str): Name of the field.
            content (dict): Contents of the JSON the field comes from.
            
        Attributes:
            multiple (bool): Whether more than one value can be given.
            values (list): The possible values.

        Raises:
            KeyError: When the 'multiple' or 'values' attributes are missing from `content`.
            ValueError: When the 'multiple' attribute of `content` is not boolean
                or the 'values' attribute is not a list.
        """
        super().__init__(name, content)
        
        if not 'multiple' in content:
            raise KeyError("A multiple-choice field requires a 'multiple' boolean attribute.")
        elif type(content['multiple']) != bool:
            raise ValueError("The 'multiple' attribute must be boolean.")
        else:
            self.multiple = content['multiple']
        
        if not 'values' in content:
            raise KeyError("A multiple-choice field requires a 'values' attribute.")
        elif type(content['values']) != list:
            raise ValueError("The 'values' attribute must be a list.")
        else:
            self.values = content['values']
            
        