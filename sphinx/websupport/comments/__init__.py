
class StorageBackend(object):
    def pre_build(self):
        pass

    def add_node(self, document, line, source, treeloc):
        raise NotImplemented
    
    def post_build(self):
        pass

    def add_comment(self, parent_id, text, displayed, username, 
                    rating, time):
        raise NotImplemented

    def get_comments(self, parent_id):
        raise NotImplemented
