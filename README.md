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
  
* Footnotes and endnotes.
  
* Images.

* Bold, italics, underlines, strikethrough, superscript and subscript.

* Links.

* Line breaks.

* Text boxes. The contents of the text box are treated as a separate paragraph
  that appears after the paragraph containing the text box.

## Installation

    pip install mammoth

## Other supported platforms

* [JavaScript](https://github.com/mwilliamson/mammoth.js), both the browser and node.js.
  Available [on npm](https://www.npmjs.com/package/mammoth).

* [WordPress](https://wordpress.org/plugins/mammoth-docx-converter/).

* [Java/JVM](https://github.com/mwilliamson/java-mammoth).
  Available [on Maven Central](http://search.maven.org/#search|ga|1|g%3A%22org.zwobble.mammoth%22%20AND%20a%3A%22mammoth%22).

* [.NET](https://github.com/mwilliamson/dotnet-mammoth).
  Available [on NuGet](https://www.nuget.org/packages/Mammoth/).
    
## Usage

### CLI

You can convert docx files by passing the path to the docx file and the output file.
For instance:

    mammoth document.docx output.html

If no output file is specified, output is written to stdout instead.

The output is an HTML fragment, rather than a full HTML document, encoded with UTF-8.
Since the encoding is not explicitly set in the fragment,
opening the output file in a web browser may cause Unicode characters to be rendered incorrectly if the browser doesn't default to UTF-8.

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

#### Markdown

Using `--output-format=markdown` will cause Markdown to be generated.
For instance:

    mammoth document.docx --output-format=markdown

Markdown support is still in its early stages,
so you may find some features are unsupported.

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

mammoth.convert_to_html(docx_file, convert_image=mammoth.images.img_element(convert_image))
```

#### Bold

By default, bold text is wrapped in `<strong>` tags.
This behaviour can be changed by adding a style mapping for `b`.
For instance, to wrap bold text in `<em>` tags:

```python
style_map = "b => em"

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file, style_map=style_map)
```

#### Italic

By default, italic text is wrapped in `<em>` tags.
This behaviour can be changed by adding a style mapping for `i`.
For instance, to wrap italic text in `<strong>` tags:

```python
style_map = "i => strong"

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file, style_map=style_map)
```

#### Underline

By default, the underlining of any text is ignored since underlining can be confused with links in HTML documents.
This behaviour can be changed by adding a style mapping for `u`.
For instance, suppose that a source document uses underlining for emphasis.
The following will wrap any explicitly underlined source text in `<em>` tags:

```python
import mammoth

style_map = "u => em"

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file, style_map=style_map)
```

#### Strikethrough

By default, strikethrough text is wrapped in `<s>` tags.
This behaviour can be changed by adding a style mapping for `strike`.
For instance, to wrap strikethrough text in `<del>` tags:

```python
style_map = "strike => del"

with open("document.docx", "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file, style_map=style_map)
```

### API

#### `mammoth.convert_to_html(fileobj, **kwargs)`

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
  
* `ignore_empty_paragraphs`: by default, empty paragraphs are ignored.
  Set this option to `False` to preserve empty paragraphs in the output.

* `id_prefix`:
  a string to prepend to any generated IDs,
  such as those used by bookmarks, footnotes and endnotes.
  Defaults to an empty string.

* Returns a result with the following properties:

  * `value`: the generated HTML

  * `messages`: any messages, such as errors and warnings, generated during the conversion

#### `mammoth.convert_to_markdown(fileobj, **kwargs)`

Converts the source document to Markdown.
This behaves the same as `convert_to_html`,
except that the `value` property of the result contains Markdown rather than HTML.

#### `mammoth.extract_raw_text(fileobj)`

Extract the raw text of the document.
This will ignore all formatting in the document.
Each paragraph is followed by two newlines.

* `fileobj`: a file-like object containing the source document.
  Files should be opened in binary mode.

* Returns a result with the following properties:

  * `value`: the raw text

  * `messages`: any messages, such as errors and warnings

#### `mammoth.embed_style_map(fileobj, style_map)`

Embeds the style map `style_map` into `fileobj`.
When Mammoth reads a file object,
it will use the embedded style if no explicit style map is provided.

* `fileobj`: a file-like object containing the source document.
  Files should be opened for reading and writing in binary mode.

* `style_map`: the style map to embed.

* Returns `None`.

#### Messages

Each message has the following properties:

* `type`: a string representing the type of the message, such as `"warning"`

* `message`: a string containing the actual message

#### Image converters

An image converter can be created by calling `mammoth.images.img_element(func)`.
This creates an `<img>` element for each image in the original docx.
`func` should be a function that has one argument `image`.
This argument is the image element being converted,
and has the following properties:

* `open()`: open the image file. Returns a file-like object.
  
* `content_type`: the content type of the image, such as `image/png`.

`func` should return a `dict` of attributes for the `<img>` element.
At a minimum, this should include the `src` attribute.
If any alt text is found for the image,
this will be automatically added to the element's attributes.

For instance, the following replicates the default image conversion:

```python
def convert_image(image):
    with image.open() as image_bytes:
        encoded_src = base64.b64encode(image_bytes.read()).decode("ascii")
    
    return {
        "src": "data:{0};base64,{1}".format(image.content_type, encoded_src)
    }

mammoth.images.img_element(convert_image)
```

## Writing style maps

A style map is made up of a number of style mappings separated by new lines.
Blank lines and lines starting with `#` are ignored.

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

#### Bold

Match explicitly bold text:

```
b
```

Note that this matches text that has had bold explicitly applied to it.
It will not match any text that is bold because of its paragraph or run style.

#### Italic

Match explicitly italic text:

```
i
```

Note that this matches text that has had italic explicitly applied to it.
It will not match any text that is italic because of its paragraph or run style.

#### Underline

Match explicitly underlined text:

```
u
```

Note that this matches text that has had underline explicitly applied to it.
It will not match any text that is underlined because of its paragraph or run style.

#### Strikethough

Match explicitly struckthrough text:

```
strike
```

Note that this matches text that has had strikethrough explicitly applied to it.
It will not match any text that is struckthrough because of its paragraph or run style.

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
