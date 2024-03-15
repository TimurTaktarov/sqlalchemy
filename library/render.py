import jinja2


async def render_template(template_path, data):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(str(template_path))
    outputText = template.render(data)  # this is where to put args to the template renderer
    return outputText
