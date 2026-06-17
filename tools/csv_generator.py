import csv
import io

def generate_csv(alignment):
    """
    alignment = [
        {"source": "...", "target": "..."},
        ...
    ]
    Returns CSV text.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["source", "target"])

    for pair in alignment:
        writer.writerow([pair["source"], pair["target"]])

    return output.getvalue()
