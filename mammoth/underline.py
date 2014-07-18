def element(name):
    def convert_underline(html_generator):
        html_generator.start(name)
        
    return convert_underline
