import os 

EXAMPLES_DIR = "./examples/"
EXAMPLE_NAME_TEMPLATE = "example-policy{}.yml"
VALID_BEGINNGINGS = ["scenarios", "config"]

cwd = os.path.dirname(os.path.realpath(__file__)) + "/../docs/"

files = []
for (dirpath, dirnames, filenames) in os.walk(cwd):
  for filename in filenames:
    if filename.endswith(".md"):
      #print(dirpath + "/" + filename)
      files.append(dirpath + "/" + filename)

counter = 0
for filename in files:
  #print("Reading " + filename)
  with open(filename) as f:
    content = ""
    inside = False
    for line in f.readlines():
      if line.startswith("```yaml"):
        #print("Starting " + line)
        inside = True
      elif line.startswith("```"):
        is_valid = False
        for beg in VALID_BEGINNGINGS:
          if content.startswith(beg):
            is_valid = True
        if is_valid and inside:
          #print("Finishing " + line)
          output = EXAMPLES_DIR + EXAMPLE_NAME_TEMPLATE.format(counter)
          print(output)
          with open(output, "w") as policy_file:
            policy_file.write(content)
          inside = False
          content = ""
          counter += 1
      elif inside:
        content += line
