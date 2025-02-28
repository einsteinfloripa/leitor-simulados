from core.definitions.test_defs import TestType
from api import CoreApi


# =============================================================================
# Static Constants
# =============================================================================

title_font = ("Helvetica", 13, "bold")
semititle_font = ("Helvetica", 11, "bold")
regular_font = ("Helvetica", 11)


# =============================================================================
# Configuration Class
# =============================================================================

class Config:
    """
    Global configuration class holding static and dynamic variables for the application.

    Attributes
    ----------
    api : CoreApi
        An instance of the CoreApi.
    selected_test_type : TestType
        The currently selected test type.
    current_image_index : int
        The index of the currently selected image.
    """

    # Static API instance
    api: CoreApi = CoreApi()

    # Global dynamic variables
    selected_test_type: TestType = TestType.PS_ALUNOS
    current_image_index: int = 0
