import csv


def remove_codes(item):
    n_item = item.split("-", 1)
    if len(n_item) > 1:
        return n_item[1]
    return n_item[0]


with open("productos.csv", "r") as f:
    reader = csv.reader(f, delimiter=",", quotechar='"')
    for row in reader:
        row = [r if i < 1 else remove_codes(r) for i, r in enumerate(row)]
        print(",".join(row))
