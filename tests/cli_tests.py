import os
import base64

from nose.tools import istest, assert_equal
import spur
import tempman

from .testing import test_path


_local = spur.LocalShell()

@istest
def html_is_printed_to_stdout_if_output_file_is_not_set():
    docx_path = test_path("single-paragraph.docx")
    result = _local.run(["mammoth", docx_path])
    assert_equal(b"", result.stderr_output)
    assert_equal(b"<p>Walking on imported air</p>", result.output)


@istest
def html_is_written_to_file_if_output_file_is_set():
    with tempman.create_temp_dir() as temp_dir:
        output_path = os.path.join(temp_dir.path, "output.html")
        docx_path = test_path("single-paragraph.docx")
        result = _local.run(["mammoth", docx_path, output_path])
        assert_equal(b"", result.stderr_output)
        assert_equal(b"", result.output)
        with open(output_path) as output_file:
            assert_equal("<p>Walking on imported air</p>", output_file.read())


_image_base_64 = b"iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAOvgAADr4B6kKxwAAAABNJREFUKFNj/M+ADzDhlWUYqdIAQSwBE8U+X40AAAAASUVORK5CYII="

@istest
def inline_images_are_included_in_output_if_writing_to_single_file():
    docx_path = test_path("tiny-picture.docx")
    result = _local.run(["mammoth", docx_path])
    assert_equal(b"""<p><img height="10" src="data:image/png;base64,""" + _image_base_64 + b"""" width="10" /></p>""", result.output)


@istest
def images_are_written_to_separate_files_if_output_dir_is_set():
    with tempman.create_temp_dir() as temp_dir:
        output_path = os.path.join(temp_dir.path, "tiny-picture.html")
        image_path = os.path.join(temp_dir.path, "1.png")
        
        docx_path = test_path("tiny-picture.docx")
        result = _local.run(["mammoth", docx_path, "--output-dir", temp_dir.path])
        assert_equal(b"", result.stderr_output)
        assert_equal(b"", result.output)
        with open(output_path) as output_file:
            assert_equal("""<p><img height="10" src="1.png" width="10" /></p>""", output_file.read())
        
        with open(image_path, "rb") as image_file:
            assert_equal(_image_base_64, base64.b64encode(image_file.read()))
    

@istest
def style_map_is_used_if_set():
    with tempman.create_temp_dir() as temp_dir:
        docx_path = test_path("single-paragraph.docx")
        style_map_path = os.path.join(temp_dir.path, "style-map")
        with open(style_map_path, "w") as style_map_file:
            style_map_file.write("p => span:fresh")
        result = _local.run(["mammoth", docx_path, "--style-map", style_map_path])
        assert_equal(b"", result.stderr_output)
        assert_equal(b"<span>Walking on imported air</span>", result.output)


@istest
def output_format_markdown_option_generates_markdown_output():
    docx_path = test_path("single-paragraph.docx")
    result = _local.run(["mammoth", docx_path, "--output-format=markdown"])
    assert_equal(b"", result.stderr_output)
    assert_equal(b"Walking on imported air\n\n", result.output)
