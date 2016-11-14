/* Retrieves a specific recovered ${value_description} by index
 * Returns a Python object if successful or NULL on error
 */
PyObject *${python_module_name}_${type_name}_get_recovered_${value_name}_by_index(
           PyObject *${python_module_name}_${type_name},
           int ${value_name}_index )
{
	PyObject *${value_name}_object                 = NULL;
	libcerror_error_t *error                       = NULL;
	${library_name}_${value_name}_t *${value_name} = NULL;
	static char *function                          = "${python_module_name}_${type_name}_get_recovered_${value_name}_by_index";
	int result                                     = 0;

	if( ${python_module_name}_${type_name} == NULL )
	{
		PyErr_Format(
		 PyExc_TypeError,
		 "%s: invalid ${type_description}.",
		 function );

		return( NULL );
	}
	Py_BEGIN_ALLOW_THREADS

	result = ${library_name}_${type_name}_get_recovered_${value_name}(
	          ( (${python_module_name}_${type_name}_t *) ${python_module_name}_${type_name} )->${type_name},
	          ${value_name}_index,
	          &${value_name},
	          &error );

	Py_END_ALLOW_THREADS

	if( result != 1 )
	{
		${python_module_name}_error_raise(
		 error,
		 PyExc_IOError,
		 "%s: unable to retrieve recovered ${value_description}: %d.",
		 function,
		 ${value_name}_index );

		libcerror_error_free(
		 &error );

		goto on_error;
	}
	${value_name}_object = ${python_module_name}_${value_name}_new(
	                        &${python_module_name}_${value_name}_type_object,
	                        ${value_name},
	                        (PyObject *) ${python_module_name}_${type_name} );

	if( ${value_name}_object == NULL )
	{
		PyErr_Format(
		 PyExc_MemoryError,
		 "%s: unable to create ${value_description} object.",
		 function );

		goto on_error;
	}
	return( ${value_name}_object );

on_error:
	if( ${value_name} != NULL )
	{
		${library_name}_${value_name}_free(
		 &${value_name},
		 NULL );
	}
	return( NULL );
}

/* Retrieves a specific recovered ${value_description}
 * Returns a Python object if successful or NULL on error
 */
PyObject *${python_module_name}_${type_name}_get_recovered_${value_name}(
           ${python_module_name}_${type_name}_t *${python_module_name}_${type_name},
           PyObject *arguments,
           PyObject *keywords )
{
	PyObject *${value_name}_object = NULL;
	static char *keyword_list[]    = { "${value_name}_index", NULL };
	int ${value_name}_index        = 0;

	if( PyArg_ParseTupleAndKeywords(
	     arguments,
	     keywords,
	     "i",
	     keyword_list,
	     &${value_name}_index ) == 0 )
	{
		return( NULL );
	}
	${value_name}_object = ${python_module_name}_${type_name}_get_recovered_${value_name}_by_index(
	                        (PyObject *) ${python_module_name}_${type_name},
	                        ${value_name}_index );

	return( ${value_name}_object );
}

/* Retrieves a sequence and iterator object for the recovered ${value_description}s
 * Returns a Python object if successful or NULL on error
 */
PyObject *${python_module_name}_${type_name}_get_recovered_${value_name}s(
           ${python_module_name}_${type_name}_t *${python_module_name}_${type_name},
           PyObject *arguments ${python_module_name_upper_case}_ATTRIBUTE_UNUSED )
{
	PyObject *sequence_object    = NULL;
	libcerror_error_t *error     = NULL;
	static char *function        = "${python_module_name}_${type_name}_get_recovered_${value_name}s";
	int number_of_${value_name}s = 0;
	int result                   = 0;

	${python_module_name_upper_case}_UNREFERENCED_PARAMETER( arguments )

	if( ${python_module_name}_${type_name} == NULL )
	{
		PyErr_Format(
		 PyExc_TypeError,
		 "%s: invalid ${type_description}.",
		 function );

		return( NULL );
	}
	Py_BEGIN_ALLOW_THREADS

	result = ${library_name}_${type_name}_get_number_of_recovered_${value_name}s(
	          ${python_module_name}_${type_name}->${type_name},
	          &number_of_${value_name}s,
	          &error );

	Py_END_ALLOW_THREADS

	if( result != 1 )
	{
		${python_module_name}_error_raise(
		 error,
		 PyExc_IOError,
		 "%s: unable to retrieve number of recovered ${value_description}s.",
		 function );

		libcerror_error_free(
		 &error );

		return( NULL );
	}
	sequence_object = ${python_module_name}_${value_name}s_new(
	                   (PyObject *) ${python_module_name}_${type_name},
	                   &${python_module_name}_${type_name}_get_recovered_${value_name}_by_index,
	                   number_of_${value_name}s );

	if( sequence_object == NULL )
	{
		${python_module_name}_error_raise(
		 error,
		 PyExc_MemoryError,
		 "%s: unable to create sequence object.",
		 function );

		return( NULL );
	}
	return( sequence_object );
}

