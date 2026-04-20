import pathlib
import html
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, FOAF, SKOS

def get_local_name(uri: URIRef) -> str:
    """Extracts the local name from a URI."""
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    return uri_str.split("/")[-1]

def format_value(value) -> str:
    """Formats an RDF value for HTML output."""
    if isinstance(value, URIRef):
        uri_str = str(value)
        local_name = get_local_name(value)
        
        # If it's an internal link (our own namespace)
        if "kb.elias.eng.br/nid.ttl#" in uri_str:
            return f'<a href="#{local_name}">{html.escape(local_name)}</a>'
        # If it's an external link (like github, elias.eng.br, etc)
        elif uri_str.startswith("http"):
            return f'<a href="{html.escape(uri_str)}">{html.escape(uri_str)}</a>'
        
        return html.escape(local_name)
    else:
        return html.escape(str(value))

def generate_html(graph: Graph, base_uri: str) -> str:
    entities_html = []
    
    # Get all distinct subjects
    subjects = set(graph.subjects(None, None))
    
    # Filter out blank nodes and ontology definition itself
    subjects = [s for s in subjects if isinstance(s, URIRef) and str(s) != base_uri.rstrip("#")]
    
    # Sort subjects by local name
    subjects.sort(key=lambda s: get_local_name(s))

    for subject in subjects:
        local_id = get_local_name(subject)
        subject_str = str(subject)
        
        # Determine title (try foaf:name, schema:name, or fallback to local ID)
        title = local_id
        for name_prop in [FOAF.name, URIRef("https://schema.org/name")]:
            name_val = graph.value(subject, name_prop)
            if name_val:
                title = str(name_val)
                break

        # Group properties
        properties = {}
        for p, o in graph.predicate_objects(subject):
            p_name = get_local_name(p)
            # Use prefixed names for common properties for better readability
            if p == RDF.type:
                p_name = "Tipo (rdf:type)"
            elif str(p).startswith(str(FOAF)):
                p_name = f"foaf:{get_local_name(p)}"
            elif str(p).startswith("https://schema.org/"):
                p_name = f"schema:{get_local_name(p)}"
            elif str(p).startswith("http://www.w3.org/ns/org#"):
                p_name = f"org:{get_local_name(p)}"
                
            if p_name not in properties:
                properties[p_name] = []
            properties[p_name].append(o)

        # Build table rows
        rows_html = ""
        for p_name, values in sorted(properties.items()):
            formatted_values = ", ".join([format_value(v) for v in values])
            rows_html += f"<tr><th>{html.escape(p_name)}</th><td>{formatted_values}</td></tr>\n"

        # Build entity block
        entity_html = f"""
        <div class="entity" id="{html.escape(local_id)}">
            <h3 class="entity-title">{html.escape(title)}</h3>
            <span class="uri">{html.escape(subject_str)}</span>
            <table class="props">
                {rows_html}
            </table>
        </div>"""
        entities_html.append(entity_html)

    # HTML Template
    template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Namespace ID (NID) - KB Elias</title>
    <style>
        :root {{
            --text: #333;
            --muted: #666;
            --rule: #eaeaea;
            --accent: #1f4f9a;
            --bg: #fdfdfd;
        }}
        body {{
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
            line-height: 1.6;
        }}
        .container {{
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }}
        header {{
            border-bottom: 2px solid var(--rule);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: var(--accent);
        }}
        h2 {{
            border-bottom: 1px solid var(--rule);
            padding-bottom: 5px;
            margin-top: 40px;
        }}
        code {{
            background: #f1f1f1;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #d63384;
        }}
        .entity {{
            background: white;
            border: 1px solid var(--rule);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}
        .entity-title {{
            margin-top: 0;
            color: var(--accent);
        }}
        .uri {{
            font-family: monospace;
            color: var(--muted);
            margin-bottom: 15px;
            display: block;
            word-break: break-all;
        }}
        .props {{
            width: 100%;
            border-collapse: collapse;
        }}
        .props th, .props td {{
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid var(--rule);
        }}
        .props th {{
            width: 30%;
            color: var(--muted);
            font-weight: normal;
        }}
        .rdf-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .rdf-link:hover {{
            background: #153b75;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Namespace ID (NID)</h1>
        <p>Vocabulário e identificadores de recursos da base de conhecimento de Elias Magalhães.</p>
        <p><strong>URI Base:</strong> <code>{html.escape(base_uri)}</code></p>
        <a href="/nid.ttl" class="rdf-link">⬇ Baixar dados RDF (Turtle)</a>
    </header>

    <section>
        <h2>Indivíduos Nomeados (Named Individuals)</h2>
        {"".join(entities_html)}
    </section>
</div>

</body>
</html>"""
    
    return template

def main():
    base_dir = pathlib.Path(__file__).resolve().parent
    ttl_path = base_dir / "nid.ttl"
    html_path = base_dir / "nid" / "index.html"
    
    # Define Base URI matching the ontology
    base_uri = "http://kb.elias.eng.br/nid.ttl#"

    print(f"Loading RDF from {ttl_path}...")
    g = Graph()
    g.parse(ttl_path, format="ttl")
    
    print(f"Generating HTML documentation...")
    html_content = generate_html(g, base_uri)
    
    # Ensure directory exists
    html_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing to {html_path}...")
    html_path.write_text(html_content, encoding="utf-8")

if __name__ == "__main__":
    main()
