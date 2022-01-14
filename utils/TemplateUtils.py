import yaml
import glob

class TemplateUtils:

    entity_map = {}
    properties_map = {}

    def read_templates(self):
        template_files = glob.glob("templates/*.yaml")
        for file in template_files:
            with open(file, 'r') as stream:
               file_content = yaml.safe_load(stream)
               type = file_content['Type']
               name = file_content['Name']
               properties = file_content['Properties']
               self.properties_map[name] = properties
               relationships = {}
               if 'Relationships'  in file_content:
                 relationships = file_content['Relationships']
               self.entity_map[name] = [properties, relationships]

               print(file_content)
        return self.entity_map, self.properties_map

    def get_relationship_details(self, source_entity, destination_entity):
        relationship_data = self.entity_map[source_entity][1]
        relationship_details = {}
        for relations in relationship_data:
            if relations['entity'] == destination_entity:
                relationship_details = relations
                break

        return relationship_details

instance = TemplateUtils()