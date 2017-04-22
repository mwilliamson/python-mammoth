import base64
import io
import os
import shutil
import subprocess
import tempfile

from . import html


def img_element(func):
    def convert_image(image):
        attributes = func(image).copy()
        if image.alt_text:
            attributes["alt"] = image.alt_text
            
        return [html.element("img", attributes)]
    
    return convert_image

# Undocumented, but retained for backwards-compatibility with 0.3.x
inline = img_element


@img_element
def data_uri(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }


_wmf_extensions = {
    "image/x-wmf": ".wmf",
    "image/x-emf": ".emf",
}


def libreoffice_wmf_conversion(post_process=None):
    if post_process is None:
        post_process = lambda x: x
    
    def convert_image(image):
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
    
    return convert_image


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
