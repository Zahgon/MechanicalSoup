import copy
import io
import warnings

from bs4 import BeautifulSoup

from .utils import LinkNotFoundError, is_multipart_file_upload


class InvalidFormMethod(LinkNotFoundError):
    """This exception is raised when a method of :class:`Form` is used
    for an HTML element that is of the wrong type (or is malformed).
    It is caught within :func:`Form.set` to perform element type deduction.

    It is derived from :class:`LinkNotFoundError` so that a single base class
    can be used to catch all exceptions specific to this module.
    """
    pass


class Form:
    """Build a fillable form.

    :param form: A bs4.element.Tag corresponding to an HTML form element.

    The Form class is responsible for preparing HTML forms for submission.
    It handles the following types of elements:
    input (text, checkbox, radio), select, and textarea.

    Each type is set by a method named after the type (e.g.
    :func:`~Form.set_select`), and then there are convenience methods (e.g.
    :func:`~Form.set`) that do type-deduction and set the value using the
    appropriate method.

    It also handles submit-type elements using :func:`~Form.choose_submit`.
    """

    def __init__(self, form):
        if form.name != 'form':
            warnings.warn(
                f"Constructed a Form from a '{form.name}' instead of a 'form' "
                " element. This may be an error in a future version of "
                "MechanicalSoup.", FutureWarning)

        self.form = form
        self._submit_chosen = False

        # Aliases for backwards compatibility
        # (Included specifically in __init__ to suppress them in Sphinx docs)
        self.attach = self.set_input
        self.input = self.set_input
        self.textarea = self.set_textarea

    def set_input(self, data):
        """Fill-in a set of fields in a form.

        Example: filling-in a login/password form

        .. code-block:: python

           form.set_input({"login": username, "password": password})

        This will find the input element named "login" and give it the
        value ``username``, and the input element named "password" and
        give it the value ``password``.
        """
        pass

    def uncheck_all(self, name):
        """Remove the *checked*-attribute of all input elements with
        a *name*-attribute given by ``name``.
        """
        pass

    def check(self, data):
        """For backwards compatibility, this method handles checkboxes
        and radio buttons in a single call. It will not uncheck any
        checkboxes unless explicitly specified by ``data``, in contrast
        with the default behavior of :func:`~Form.set_checkbox`.
        """
        pass

    def set_checkbox(self, data, uncheck_other_boxes=True):
        """Set the *checked*-attribute of input elements of type "checkbox"
        specified by ``data`` (i.e. check boxes).

        :param data: Dict of ``{name: value, ...}``.
            In the family of checkboxes whose *name*-attribute is ``name``,
            check the box whose *value*-attribute is ``value``. All boxes in
            the family can be checked (unchecked) if ``value`` is True (False).
            To check multiple specific boxes, let ``value`` be a tuple or list.
        :param uncheck_other_boxes: If True (default), before checking any
            boxes specified by ``data``, uncheck the entire checkbox family.
            Consider setting to False if some boxes are checked by default when
            the HTML is served.
        """
        pass

    def set_radio(self, data):
        """Set the *checked*-attribute of input elements of type "radio"
        specified by ``data`` (i.e. select radio buttons).

        :param data: Dict of ``{name: value, ...}``.
            In the family of radio buttons whose *name*-attribute is ``name``,
            check the radio button whose *value*-attribute is ``value``.
            Only one radio button in the family can be checked.
        """
        pass

    def set_textarea(self, data):
        """Set the *string*-attribute of the first textarea element
        specified by ``data`` (i.e. set the text of a textarea).

        :param data: Dict of ``{name: value, ...}``.
            The textarea whose *name*-attribute is ``name`` will have
            its *string*-attribute set to ``value``.
        """
        pass

    def set_select(self, data):
        """Set the *selected*-attribute of the first option element
        specified by ``data`` (i.e. select an option from a dropdown).

        :param data: Dict of ``{name: value, ...}``.
            Find the select element whose *name*-attribute is ``name``.
            Then select from among its children the option element whose
            *value*-attribute is ``value``. If no matching *value*-attribute
            is found, this will search for an option whose text matches
            ``value``. If the select element's *multiple*-attribute is set,
            then ``value`` can be a list or tuple to select multiple options.
        """
        pass

    def __setitem__(self, name, value):
        """Forwards arguments to :func:`~Form.set`. For example,
        :code:`form["name"] = "value"` calls :code:`form.set("name", "value")`.
        """
        return self.set(name, value)

    def set(self, name, value, force=False):
        """Set a form element identified by ``name`` to a specified ``value``.
        The type of element (input, textarea, select, ...) does not
        need to be given; it is inferred by the following methods:
        :func:`~Form.set_checkbox`,
        :func:`~Form.set_radio`,
        :func:`~Form.set_input`,
        :func:`~Form.set_textarea`,
        :func:`~Form.set_select`.
        If none of these methods find a matching element, then if ``force``
        is True, a new element (``<input type="text" ...>``) will be
        added using :func:`~Form.new_control`.

        Example: filling-in a login/password form with EULA checkbox

        .. code-block:: python

            form.set("login", username)
            form.set("password", password)
            form.set("eula-checkbox", True)

        Example: uploading a file through a ``<input type="file"
        name="tagname">`` field (provide an open file object,
        and its content will be uploaded):

        .. code-block:: python

            form.set("tagname", open(path_to_local_file, "rb"))

        """
        pass

    def new_control(self, type, name, value, **kwargs):
        """Add a new input element to the form.

        The arguments set the attributes of the new element.
        """
        pass

    def choose_submit(self, submit):
        """Selects the input (or button) element to use for form submission.

        :param submit: The :class:`bs4.element.Tag` (or just its
            *name*-attribute) that identifies the submit element to use. If
            ``None``, will choose the first valid submit element in the form,
            if one exists. If ``False``, will not use any submit element;
            this is useful for simulating AJAX requests, for example.

        To simulate a normal web browser, only one submit element must be
        sent. Therefore, this does not need to be called if there is only
        one submit element in the form.

        If the element is not found or if multiple elements match, raise a
        :class:`LinkNotFoundError` exception.

        Example: ::

            browser = mechanicalsoup.StatefulBrowser()
            browser.open(url)
            form = browser.select_form()
            form.choose_submit('form_name_attr')
            browser.submit_selected()
        """
        pass

    def print_summary(self):
        """Print a summary of the form.

        May help finding which fields need to be filled-in.
        """
        pass

    def _assert_valid_file_upload(self, tag, value):
        """Raise an exception if a multipart file input is not an open file."""
        pass
