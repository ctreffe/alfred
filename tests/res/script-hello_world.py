import alfred3 as al
exp = al.Experiment()
exp += al.Page(title="Page 1", name="p1")

if __name__ == "__main__":
    exp.run()