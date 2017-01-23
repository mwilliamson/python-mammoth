def uri_to_zip_entry_name(base, uri):
    if uri.startswith("/"):
        return uri[1:]
    else:
        return base + "/" + uri
