import girder_client
from bioportalSearchWidgets import BioportalSearchWidgets

class GirderUploader:

    def __init__(self, girder_api_url, username, password):
        self._client = girder_client.GirderClient(apiUrl = girder_api_url)
        self._client.authenticate(username, password)
        self._bio_search = BioportalSearchWidgets(self.__submit_callback)
        self._metadata = dict()
        self._local_path = None
        self._girder_dest_path = None
        self._request_metadata = False

    def upload_folder(self, girder_dest_path, local_path):
        """
        Begins the upload process. If metadata is required, input forms and
        created and displayed before upload begins. 
        """
        self._local_path = local_path
        self._girder_dest_path = girder_dest_path
        if self._request_metadata:
            self._bio_search.display_widgets()
        else:
            parentId, parentType = parent.__get_parent_id_and_type()
            self._client.upload(self._local_path, parentId,
                                parent_type=parentType)

    def request_metadata(self, keyword, ontologies, require=False):
        """
        Setup to request metadata from the user after attempting to upload
        a folder/file.

        :param keyword:     Keyword of what the metadata requested is
                            describing (e.i., region, disease)
        :param ontologies:  List of ontology IDs to be searched.
        :param require:     Whethere or not to require this metadata to be
                            filled before upload
        """
        self._request_metadata = True
        self._bio_search.add_search_widget(keyword, ontologies, require)

    def __submit_callback(self, results):
        parentId, parentType = self.__get_parent_id_and_type()

        def get_id(id_url):
            temp_id = id_url.rsplit('/', 1)[-1]
            if '#' in temp_id:
                # RADLEX
                id = temp_id.rsplit('#', 1)[-1]
                return id[3:]
            else:
                # DOID, UBERON
                return temp_id.rsplit('_', 1)[-1]

        def extract_info(name):
            result = results[name]
            keyword = result[0]
            dictionary = result[1]
            topic = name
            ontology_url = dictionary['links']['ontology']
            json_result = self._bio_search.GET(ontology_url)
            acronym = json_result['acronym']
            name = json_result['name']
            resource = dictionary['@id']
            id = get_id(resource)
            meta = {'Ontology Name' : name,
                    'Ontology Acronym' : acronym,
                    'Name': keyword,
                    'ID' : id,
                    'Resource URL' : resource}
            self._metadata[topic] = meta
        
        for name in results:
            extract_info(name)      
        # extract_info('region')
        # extract_info('disease')

        self._client.add_folder_upload_callback(self.__upload_folder_callback)
        self._client.add_item_upload_callback(self.__upload_item_callback)
        self._client.upload(self._local_path, parentId, parent_type=parentType)

    def __get_parent_id_and_type(self):
        params = {'path': self._girder_dest_path, 'test': True}
        response = self._client.get('resource/lookup',
                                    parameters=params)
        parentType = response['_modelType']
        parentId = response['_id']
        return (parentId, parentType)


    def __upload_item_callback(self, item, filepath):
        self._client.addMetadataToItem(item['_id'], self._metadata)

    def __upload_folder_callback(self, folder, filepath):
        self._client.addMetadataToFolder(folder['_id'], self._metadata)
        