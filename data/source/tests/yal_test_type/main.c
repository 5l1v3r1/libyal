/* The main program
 */
#if defined( LIBCSTRING_HAVE_WIDE_SYSTEM_CHARACTER )
int wmain(
     int argc ${library_name_suffix_upper_case}_TEST_ATTRIBUTE_UNUSED,
     wchar_t * const argv[] ${library_name_suffix_upper_case}_TEST_ATTRIBUTE_UNUSED )
#else
int main(
     int argc ${library_name_suffix_upper_case}_TEST_ATTRIBUTE_UNUSED,
     char * const argv[] ${library_name_suffix_upper_case}_TEST_ATTRIBUTE_UNUSED )
#endif
{
	${library_name_suffix_upper_case}_TEST_UNREFERENCED_PARAMETER( argc )
	${library_name_suffix_upper_case}_TEST_UNREFERENCED_PARAMETER( argv )

	${library_name_suffix_upper_case}_TEST_RUN(
	 "${library_name}_${library_type}_initialize",
	 ${library_name_suffix}_test_${library_type}_initialize() )

	${library_name_suffix_upper_case}_TEST_RUN(
	 "${library_name}_${library_type}_free",
	 ${library_name_suffix}_test_${library_type}_free() )

	return( EXIT_SUCCESS );

on_error:
	return( EXIT_FAILURE );
}

