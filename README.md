# Mammoth .docx to HTML converter

Mammoth is designed to convert .docx documents,
such as those created by Microsoft Word,
and convert them to HTML.
Mammoth aims to produce simple and clean HTML by using semantic information in the document,
and ignoring other details.
For instance,
Mammoth converts any paragraph with the style `Heading 1` to `h1` elements,
rather than attempting to exactly copy the styling (font, text size, colour, etc.) of the heading.

There's a large mismatch between the structure used by .docx and the structure of HTML,
meaning that the conversion is unlikely to be perfect for more complicated documents.
Mammoth works best if you only use styles to semantically mark up your document.

The following features are currently supported:

* Headings.

* Lists.

* Customisable mapping from your own docx styles to HTML.
  For instance, you could convert `WarningHeading` to `h1.warning` by providing an appropriate style mapping.
  
* Tables.
  The formatting of the table itself, such as borders, is currently ignored,
  but the formatting of the text is treated the same as in the rest of the document.
  
* Footnotes.
  
* Images.

* Bold, italics and underlines.

* Links.

* Line breaks.

## Installation

    pip install mammoth
    
## Usage

### CLI

You can convert docx files by passing the path to the docx file and the output file.
For instance:

    mammoth document.docx output.html

If no output file is specified, output is written to stdout instead.

#### Images

By default, images are included inline in the output HTML.
If an output directory is specified by `--output-dir`,
the images are written to separate files instead.
For instance:

    mammoth document.docx --output-dir=output-dir

Existing files will be overwritten if present.

#### Styles

A custom style map can be read from a file using `--style-map`.
For instance:

    mammoth document.docx output.html --style-map=custom-style-map
    
Where `custom-style-map` looks something like:

    p[style-name='Aside Heading'] => div.aside > h2:fresh
    p[style-name='Aside Text'] => div.aside > p:fresh

### Library

#### Basic conversion

To convert an existing .docx file to HTML,
pass a file-like object to `mammoth.convert_to_html`.
The file should be opened in binary mode.
For instance:

```python
import mammoth

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file)
    html = result.value # The generated HTML
    messages = result.messages # Any messages, such as warnings during conversion
```

You can also extract the raw text of the document by using `mammoth.extract_raw_text`.
This will ignore all formatting in the document.
Each paragraph is followed by two newlines.

```python
with open("document.docx", "rb") as docx_file:
    result = mammoth.extract_raw_text(docx_file)
    text = result.value # The raw text
    messages = result.messages # Any messages
```


#### Custom style map

By default,
Mammoth maps some common .docx styles to HTML elements.
For instance,
a paragraph with the style name `Heading 1` is converted to a `h1` element.
You can pass in a custom map for styles by passing an options object with a `style_map` property as a second argument to `convert_to_html`.
A description of the syntax for style maps can be found in the section "Writing style maps".
For instance, if paragraphs with the style name `Section Title` should be converted to `h1` elements,
and paragraphs with the style name `Subsection Title` should be converted to `h2` elements:

```python
import mammoth

style_map = """
p[style-name='Section Title'] => h1:fresh
p[style-name='Subsection Title'] => h2:fresh
"""

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file, style_map=style_map)
```

User-defined style mappings are used in preference to the default style mappings.
To stop using the default style mappings altogether,
pass `include_default_style_map=False`:

```python
result = mammoth.convert_to_html(docx_file, style_map=style_map, include_default_style_map=False)
```

#### Custom image handlers

By default, images are converted to `<img>` elements with the source included inline in the `src` attribute.
This behaviour can be changed by setting the `convert_image` argument to an [image converter](#image-converters) .

For instance, the following would replicate the default behaviour:

```python
def convert_image(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }

mammoth.convert_to_html(docx_file, convert_image=mammoth.images.inline(convert_image))
```

#### Underline

By default, the underlining of any text is ignored since underlining can be confused with links in HTML documents.
This behaviour can be changed by setting the `convert_underline` argument to `mammoth.underline.element(name)`.

For instance, suppose that a source document uses underlining for emphasis.
The following will wrap any underlined source text in `<em>` tags:

```python
mammoth.convert_to_html(docx_file, convert_underline=mammoth.underline.element("em"))
```

### API

#### `mammoth.convert_to_html(fileobj, style_map=None, include_default_style_map=True)`

Converts the source document to HTML.

* `fileobj`: a file-like object containing the source document.
  Files should be opened in binary mode.
  
* `style_map`: a string to specify the mapping of Word styles to HTML.
  See the section "Writing style maps" for a description of the syntax.

* `include_default_style_map`: by default, the style map passed in `style_map` is combined with the default style map.
  To stop using the default style map altogether,
  pass `include_default_style_map=False`.
    
* `convert_image`: by default, images are converted to `<img>` elements with the source included inline in the `src` attribute.
  Set this argument to an [image converter](#image-converters) to override the default behaviour.
  
* `convert_underline`: by default, the underlining of any text is ignored.
  Set this argument to [`mammoth.underline.element(name)`](#underline) to override the default behaviour.

* Returns a result with the following properties:

  * `value`: the generated HTML

  * `messages`: any messages, such as errors and warnings, generated during the conversion

#### `mammoth.extract_raw_text(fileobj)`

Extract the raw text of the document.
This will ignore all formatting in the document.
Each paragraph is followed by two newlines.

* `fileobj`: a file-like object containing the source document.
  Files should be opened in binary mode.

* Returns a result with the following properties:

  * `value`: the raw text

  * `messages`: any messages, such as errors and warnings

#### Messages

Each message has the following properties:

* `type`: a string representing the type of the message, such as `"warning"`

* `message`: a string containing the actual message

#### Image converters

An inline image converter can be created by calling `mammoth.images.inline(func)`.
This creates an inline `<img>` element for each image in the original docx.
`func` should be a function that has one argument `image`.
This argument is the image element being converted,
and has the following properties:

* `open()`: open the image file. Returns a file-like object.
  
* `content_type`: the content type of the image, such as `image/png`.

`func` should return a `dict` with a `src` item,
which will be used as the `src` attribute on the `<img>` element.

For instance, the following replicates the default image conversion:

```python
def convert_image(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }

mammoth.images.inline(convert_image)
```

## Writing style maps

A style map is made up of a number of style mappings separated by new lines.

A style mapping has two parts:

* On the left, before the arrow, is the document element matcher.
* On the right, after the arrow, is the HTML path.

When converting each paragraph,
Mammoth finds the first style mapping where the document element matcher matches the current paragraph.
Mammoth then ensures the HTML path is satisfied.

### Freshness

When writing style mappings, it's helpful to understand Mammoth's notion of freshness.
When generating, Mammoth will only close an HTML element when necessary.
Otherwise, elements are reused.

For instance, suppose one of the specified style mappings is `p[style-name='Heading 1'] => h1`.
If Mammoth encounters a .docx paragraph with the style name `Heading 1`,
the .docx paragraph is converted to a `h1` element with the same text.
If the next .docx paragraph also has the style name `Heading 1`,
then the text of that paragraph will be appended to the *existing* `h1` element,
rather than creating a new `h1` element.

In most cases, you'll probably want to generate a new `h1` element instead.
You can specify this by using the `:fresh` modifier:

`p[style-name='Heading 1'] => h1:fresh`

The two consective `Heading 1` .docx paragraphs will then be converted to two separate `h1` elements.

Reusing elements is useful in generating more complicated HTML structures.
For instance, suppose your .docx contains asides.
Each aside might have a heading and some body text,
which should be contained within a single `div.aside` element.
In this case, style mappings similar to `p[style-name='Aside Heading'] => div.aside > h2:fresh` and
`p[style-name='Aside Text'] => div.aside > p:fresh` might be helpful.

### Document element matchers

#### Paragraphs and runs

Match any paragraph:

```
p
```

Match any run:

```
r
```

To match a paragraph or run with a specific style,
you can reference the style by name.
This is the style name that is displayed in Microsoft Word or LibreOffice.
For instance, to match a paragraph with the style name `Heading 1`:

```
p[style-name='Heading 1']
```

Styles can also be referenced by style ID.
This is the ID used internally in the .docx file.
To match a paragraph or run with a specific style ID,
append a dot followed by the style ID.
For instance, to match a paragraph with the style ID `Heading1`:

```
p.Heading1
```

### HTML paths

#### Single elements

The simplest HTML path is to specify a single element.
For instance, to specify an `h1` element:

```
h1
```

To give an element a CSS class,
append a dot followed by the name of the class:

```
h1.section-title
```

To require that an element is fresh, use `:fresh`:

```
h1:fresh
```

Modifiers must be used in the correct order:

```
h1.section-title:fresh
```

#### Nested elements

Use `>` to specify nested elements.
For instance, to specify `h2` within `div.aside`:

```
div.aside > h2
```

You can nest elements to any depth.
