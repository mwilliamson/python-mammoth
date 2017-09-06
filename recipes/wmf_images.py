import io
import os
import shutil
import subprocess
import tempfile


# An example of how to use LibreOffice and ImageMagick to convert WMF images to
# PNGs.
#
# libreoffice_wmf_conversion uses LibreOffice to convert the image to a PNG.
# This normally creates an image with a large amount of padding, so
# imagemagick_trim can be used to trim the image.
#
# The image can be then be converted using a normal image handler, such as
# mammoth.images.data_uri.
#
# Example usage:
#
# def convert_image(image):
#     image = libreoffice_wmf_conversion(image, post_process=imagemagick_trim)
#     return mammoth.images.data_uri(image)
#    
# with open("document.docx", "rb") as fileobj:
#     result = mammoth.convert_to_html(fileobj, convert_image=convert_image)


_wmf_extensions = {
    "image/x-wmf": ".wmf",
    "image/x-emf": ".emf",
}


def libreoffice_wmf_conversion(image, post_process=None):
    if post_process is None:
        post_process = lambda x: x
    
    wmf_extension = _wmf_extensions.get(image.content_type)
    if wmf_extension is None:
        return image
    else:
        temporary_directory = tempfile.mkdtemp()
        try:
            input_path = os.path.join(temporary_directory, "image" + wmf_extension)
            with io.open(input_path, "wb") as input_fileobj:
                with image.open() as image_fileobj:
                    shutil.copyfileobj(image_fileobj, input_fileobj)
            
            output_path = os.path.join(temporary_directory, "image.png")
            subprocess.check_call([
                "libreoffice",
                "--headless",
                "--convert-to",
                "png",
                input_path,
                "--outdir",
                temporary_directory,
            ])
            
            with io.open(output_path, "rb") as output_fileobj:
                output = output_fileobj.read()
            
            def open_image():
                return io.BytesIO(output)
            
            return post_process(image.copy(
                content_type="image/png",
                open=open_image,
            ))
        finally:
            shutil.rmtree(temporary_directory)


def imagemagick_trim(image):
    command = ["convert", "-", "-trim", "-"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        with image.open() as image_fileobj:
            shutil.copyfileobj(image_fileobj, process.stdin)
        output, err_output = process.communicate()
    except:
        process.kill()
        process.wait()
        raise
        
    return_code = process.poll()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)
    else:
        def open_image():
            return io.BytesIO(output)
        
        return image.copy(open=open_image)

