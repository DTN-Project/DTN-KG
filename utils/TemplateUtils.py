import yaml
import re

class TemplateUtils:

    templatedata = None
    templateName = None
    templateParentDirectory = None
    def load(self,template_file):
        self.templateName = re.split("\.",re.split("/",template_file)[2])[0]
        self.templateParentDirectory = re.split("/",template_file)[2]
        with open(template_file,"r") as stream:
            self.templatedata = yaml.safe_load(stream)

    def get_entities(self):
        return list(self.templatedata["variables"]["entities"].keys())

    def get_relations(self):
        return self.templatedata["variables"]["relationships"]

    def get_properties(self,entity):

        return self.templatedata["variables"]["entities"][entity]

    def get_mechanisms(self):

        return self.templatedata["mechanisms"]

    def get_policies(self):
        return self.templatedata["policies"]

instance = TemplateUtils()