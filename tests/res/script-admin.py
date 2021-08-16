import alfred3 as al

exp = al.Experiment()

exp.admin += al.Page(title="Admin", name="admin_test")
exp.admin += al.Page(title="Admin2", name="admin_test2")

exp += al.Page(title="normal", name="normal")

if __name__ == "__main__":
    exp.run(open_browser=False)