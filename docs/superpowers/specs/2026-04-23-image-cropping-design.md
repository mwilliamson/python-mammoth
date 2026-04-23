# Design: Support Word Image Cropping in Mammoth

## Problem

When a user crops an image inside Microsoft Word (or other docx editors), Mammoth currently outputs the original, uncropped image. The cropping metadata (`a:srcRect` in DrawingML) is ignored during conversion.

## Goal

Apply Word’s rectangular image cropping by default during docx-to-HTML conversion. Provide a parameter to opt out.

## Out of Scope

- Rotation, flipping, recoloring, or any other non-rectangular image transforms.

---

## Data Model Changes

### `mammoth/documents.py`

Add a new `Crop` cobble data class to represent relative crop margins:

```python
@cobble.data
class Crop(object):
    left = cobble.field()
    top = cobble.field()
    right = cobble.field()
    bottom = cobble.field()
```

Add a `crop` field to `Image`:

```python
@cobble.data
class Image(Element):
    alt_text = cobble.field()
    content_type = cobble.field()
    open = cobble.field()
    crop = cobble.field()
```

Default value for `crop` is `None`.

Helper function:

```python
def image(alt_text, content_type, open, crop=None):
    return Image(alt_text=alt_text, content_type=content_type, open=open, crop=crop)
```

Update existing `documents.image = Image` usage to support the new field.

---

## Parser Changes

### `mammoth/docx/body_xml.py`

When reading `wp:inline` / `wp:anchor`, the `inline` function already traverses `a:graphic > a:graphicData > pic:pic > pic:blipFill > a:blip`. The `pic:blipFill` sibling/ancestor path may also contain `a:srcRect`, which defines the crop rectangle.

1. In the `inline` function, after locating `pic:blipFill`, read its child `a:srcRect`.
2. Extract attributes `l`, `t`, `r`, `b`. These are `ST_Percentage` values (thousandths of a percent, e.g. `100000` = 100%).
3. Convert to float ratios by dividing by `100000.0`.
4. Pass the resulting `Crop` (or `None`) through `_read_blip` → `_read_image` → `documents.image(..., crop=crop)`.

If `a:srcRect` is missing, `crop=None`.

If any attribute value is invalid (negative, > 100000, or non-numeric), log a warning and treat as `crop=None`.

---

## API / CLI Changes

### Library API

Add `apply_image_cropping=True` to:

- `mammoth.convert_to_html(fileobj, ..., apply_image_cropping=True)`
- `mammoth.convert_to_markdown(fileobj, ..., apply_image_cropping=True)`
- `mammoth.convert(fileobj, ..., apply_image_cropping=True)`

The parameter is threaded through `options.read_options` into `conversion.convert_document_element_to_html`.

### CLI

Add a boolean flag to `mammoth/cli.py`:

```
--apply-image-cropping / --no-apply-image-cropping
```

Default is `True`.

---

## Conversion Layer Changes

### `mammoth/conversion.py`

`_DocumentConverter.__init__` receives `apply_image_cropping` (default `True`).

Update `visit_image`:

```python
def visit_image(self, image, context):
    if self._apply_image_cropping and image.crop is not None:
        image = self._crop_image(image)
    try:
        return self._convert_image(image)
    except InvalidFileReferenceError as error:
        self._messages.append(results.warning(str(error)))
        return []
```

### `_crop_image(image)` implementation

```python
def _crop_image(self, image):
    try:
        from PIL import Image as PILImage
        import io

        with image.open() as image_file:
            pil_image = PILImage.open(image_file)
            width, height = pil_image.size
            crop_box = (
                int(image.crop.left * width),
                int(image.crop.top * height),
                int(width - image.crop.right * width),
                int(height - image.crop.bottom * height),
            )
            # Ensure non-empty box
            if crop_box[0] >= crop_box[2] or crop_box[1] >= crop_box[3]:
                self._messages.append(results.warning(
                    "Image crop resulted in empty dimensions, returning original image."
                ))
                return image
            cropped = pil_image.crop(crop_box)
            output = io.BytesIO()
            # Preserve original format if possible; fallback to PNG
            original_format = pil_image.format
            if original_format:
                cropped.save(output, format=original_format)
            else:
                cropped.save(output, format="PNG")
            output.seek(0)
            return image.copy(open=lambda: output, crop=None)
    except Exception as error:
        self._messages.append(results.warning(
            "Could not apply image cropping: {0}".format(error)
        ))
        return image
```

Rationale for wrapping `open()`:
- Custom `convert_image` handlers call `image.open()` transparently.
- They do not need to know about cropping or Pillow.
- The returned `io.BytesIO` supports context-manager protocol (`with`), matching existing expectations.

---

## Dependencies

Add `Pillow` to `install_requires` in `setup.py`:

```python
install_requires=[
    "cobble>=0.1.3,<0.2",
    "Pillow",
],
```

No specific minimum version is required; Pillow’s basic `Image.open` / `crop` / `save` APIs have been stable for years.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `a:srcRect` missing | `crop=None`, no warning |
| `a:srcRect` has invalid values | Warning, `crop=None` |
| Pillow fails to open image | Warning, fallback to original image |
| Pillow crop results in empty box | Warning, fallback to original image |
| `apply_image_cropping=False` | Skip all cropping logic entirely |

---

## Testing Strategy

### Parser tests (`tests` targeting `body_xml`)

- XML with `a:srcRect l="10000" t="20000" r="30000" b="40000"` produces `Image` with `crop` ratios `0.1, 0.2, 0.3, 0.4`.
- XML without `a:srcRect` produces `Image` with `crop=None`.
- XML with malformed `a:srcRect` produces a warning and `crop=None`.

### Conversion tests

- `apply_image_cropping=True` + `image.crop` set: verify `visit_image` returns a new image whose `open()` yields cropped bytes.
- `apply_image_cropping=False` + `image.crop` set: verify original bytes are preserved.

### Image processing tests

- Mock `image.open()` with a known PIL image (e.g., 100x100 RGB). Verify `_crop_image` computes correct pixel bounds and output dimensions.
- Verify fallback behavior when `crop_box` is empty.

---

## Backwards Compatibility

- Default behavior changes: images that were previously uncropped will now be cropped. This is intentional per user request.
- Users who want the old behavior can pass `apply_image_cropping=False`.
- Custom `convert_image` handlers are not broken; they receive an `image` object whose `open()` returns cropped bytes by default.
